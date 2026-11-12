"""The LangGraph agent.

        START -> agent --(wants a tool?)--> tools --+
                   ^                                |
                   +--------------------------------+
                   |
                   +--(no tool needed)--> END

"agent" asks Gemini what to do next. If Gemini requests a tool, the "tools" node runs it,
and the result goes back to "agent". This repeats until Gemini writes a final answer.
"""
import re
from functools import lru_cache

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app import config as settings
from app.tools import ALL_TOOLS

SYSTEM_PROMPT = """You are the ACME Corp Policy Assistant, helping an employee named {name}.

Rules:
1. If the user asks what policies exist, asks for all policies, or requests an overview
   of the policy library, call list_policies and summarize every returned document.
   Cite each policy by its source filename.
2. For other questions about company policy, rules, limits or procedures, call the
   search_policies tool first, and answer ONLY from the text it returns.
3. If the returned text does not contain the answer, say you could not find it in the
   company policies and suggest contacting HR. NEVER invent policy details or numbers.
4. When you use policy text, name the source file in parentheses exactly as it appears in
   the [Source: ...] label, e.g. (leave_policy.txt). If you could not find the answer,
   do not cite any file.
5. For the user's own leave balance or expense claims, use get_leave_balance or
   get_expense_status. You may combine tools, e.g. check their balance AND the policy.
6. Be concise and friendly. Use plain sentences; short lists only when helpful."""


def build_graph(llm):
    """Wire up the graph. `llm` is injected so tests can use a fake model."""
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    def agent_node(state: MessagesState, config: RunnableConfig):
        name = config.get("configurable", {}).get("user_name", "there")
        system = SystemMessage(content=SYSTEM_PROMPT.format(name=name))
        return {"messages": [llm_with_tools.invoke([system] + state["messages"], config)]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)  # -> "tools" or END
    graph.add_edge("tools", "agent")
    return graph.compile()


@lru_cache(maxsize=1)
def _default_graph():
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0,
    )
    return build_graph(llm)


def _text_of(message) -> str:
    """Gemini can return a plain string or a list of content blocks; normalise to text."""
    content = message.content
    if isinstance(content, str):
        return content.strip()
    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts).strip()


_WORD = re.compile(r"[a-z0-9]+")


def _best_passage(chunk: str, answer: str, max_len: int = 500) -> str:
    """The paragraph of a chunk that best matches the answer, i.e. the part that supports it.

    A chunk can hold several policy sections, so showing its first lines is often the wrong
    section. We pick the paragraph sharing the most words with the answer (length-normalised
    so long paragraphs don't win just for being long)."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", chunk) if p.strip()]
    if len(paragraphs) < 2:
        return chunk.strip()[:max_len]
    answer_words = set(_WORD.findall(answer.lower()))

    # Policy chunks often begin with a short document or section heading. Those headings
    # can match an answer very strongly (for example, "Expense Reimbursement Policy")
    # while saying nothing useful on their own. Prefer paragraphs with actual guidance.
    substantive = [p for p in paragraphs if len(_WORD.findall(p.lower())) >= 8]
    candidates = substantive or paragraphs

    def score(par: str) -> float:
        words = set(_WORD.findall(par.lower()))
        return len(words & answer_words) / (len(words) ** 0.5 or 1)

    return max(candidates, key=score)[:max_len]


STRONG_MATCH = 0.5  # if the model forgets to cite, still show a very strong top match


def _cited_sources(answer: str, messages) -> list[dict]:
    """Citations = the retrieved passages from files the answer actually names.

    Search scores are not comparable across differently-worded queries, so a fixed score
    cutoff is unreliable. The answer text is the ground truth for what the model used."""
    hits = []
    for msg in messages:
        if isinstance(msg, ToolMessage) and msg.name in {"search_policies", "list_policies"} and msg.artifact:
            hits.extend(msg.artifact)
    if not hits:
        return []

    text = answer.lower()
    chosen = [h for h in hits if h["source"].lower() in text]
    if not chosen:
        top = max(hits, key=lambda h: h["score"])
        chosen = [top] if top["score"] >= STRONG_MATCH else []

    best: dict[tuple, dict] = {}  # one entry per document page: its best-scoring passage
    for h in chosen:
        key = (h["source"], h["page"])
        if key not in best or h["score"] > best[key]["score"]:
            best[key] = {
                "source": h["source"],
                "page": h["page"],
                "score": h["score"],
                "snippet": _best_passage(h["text"], answer),
            }
    return sorted(best.values(), key=lambda x: x["score"], reverse=True)[:10]


def run_agent(question: str, history: list[dict], user: dict, graph=None) -> tuple[str, list[dict]]:
    """Run one chat turn. Returns (answer, sources)."""
    graph = graph or _default_graph()

    messages = []
    for m in history:  # earlier turns so follow-up questions make sense
        cls = HumanMessage if m["role"] == "user" else AIMessage
        messages.append(cls(content=m["content"]))
    messages.append(HumanMessage(content=question))

    result = graph.invoke(
        {"messages": messages},
        config={
            "configurable": {"user_id": user["id"], "user_name": user["full_name"]},
            "recursion_limit": 12,
        },
    )

    answer = _text_of(result["messages"][-1])
    if not answer:
        raise RuntimeError("The model returned an empty answer")
    return answer, _cited_sources(answer, result["messages"])
