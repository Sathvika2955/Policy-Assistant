"""Tools the agent can call. The LLM decides WHEN to use them; this code does the real work.

The docstring of each tool is what the LLM reads to decide whether it is the right tool,
so it is written for the model, not for humans.
"""
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app import config, retrieval
from app.database import connect
from app.ingestion import load_pages


@tool(response_format="content_and_artifact")
def search_policies(query: str) -> tuple[str, list[dict]]:
    """Search the company policy documents (leave, expenses, travel, remote work,
    IT security, code of conduct). Use this for ANY question about company rules,
    entitlements, limits, deadlines or procedures. Pass a short, specific search query."""
    hits = retrieval.search(query, k=3)
    if not hits:
        return "No matching policy text was found.", []
    parts = []
    for h in hits:
        where = h["source"] + (f", page {h['page']}" if h["page"] else "")
        parts.append(f"[Source: {where}]\n{h['text']}")
    # content -> what the LLM reads;  artifact -> structured data we use for citations
    return "\n\n".join(parts), hits


@tool(response_format="content_and_artifact")
def list_policies() -> tuple[str, list[dict]]:
    """Use when the user asks what company policies exist, asks to see all policies,
    or requests a list or overview of the policy library. Return the available policy
    documents and their text so the answer can summarize every one, not just search hits."""
    names = retrieval.list_documents()
    if not names:
        return "No policy documents are available.", []

    sections = []
    artifacts = []
    for name in names:
        path = config.POLICY_DIR / name
        try:
            pages = load_pages(path)
        except Exception:
            continue
        file_text = []
        for page in pages:
            text = page["text"].strip()
            if not text:
                continue
            file_text.append(text)
            artifacts.append({
                "text": text,
                "source": name,
                "page": page["page"],
                "score": 1.0,
            })
        if file_text:
            sections.append(f"[Source: {name}]\n" + "\n\n".join(file_text))

    if not sections:
        return "The policy library has no readable policy text.", []
    return "\n\n".join(sections), artifacts


@tool
def get_leave_balance(config: RunnableConfig) -> str:
    """Get the CURRENT USER's own leave balance: annual and sick leave days taken and
    remaining. Use when the user asks how many leave days THEY have left or have used."""
    user_id = config["configurable"]["user_id"]
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM leave_balances WHERE user_id = ?", (user_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        return "No leave record was found for this user."
    return (
        f"Annual leave: {row['annual_total'] - row['annual_used']} days remaining "
        f"({row['annual_used']} used of {row['annual_total']}). "
        f"Sick leave: {row['sick_total'] - row['sick_used']} days remaining "
        f"({row['sick_used']} used of {row['sick_total']})."
    )


@tool
def get_expense_status(config: RunnableConfig) -> str:
    """Get the status of the CURRENT USER's own submitted expense claims (amount, status,
    date). Use when the user asks about their expense claims, reimbursements or approvals."""
    user_id = config["configurable"]["user_id"]
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT description, amount, status, submitted_on FROM expenses "
            "WHERE user_id = ? ORDER BY submitted_on DESC",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        return "This user has no expense claims on record."
    return "\n".join(
        f"- {r['description']}: {r['amount']:,.0f} INR, status: {r['status']} (submitted {r['submitted_on']})"
        for r in rows
    )


ALL_TOOLS = [search_policies, list_policies, get_leave_balance, get_expense_status]
