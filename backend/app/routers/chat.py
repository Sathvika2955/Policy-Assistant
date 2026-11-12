import json

from fastapi import APIRouter, Depends, HTTPException, Response

from app.answer import answer_question
from app.database import get_db
from app.deps import get_current_user
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


def _get_owned_conversation(db, conversation_id: int, user_id: int):
    row = db.execute(
        "SELECT id, title, created_at FROM conversations WHERE id = ? AND user_id = ?",
        (conversation_id, user_id),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return row


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, user: dict = Depends(get_current_user), db=Depends(get_db)):
    if body.conversation_id is None:
        title = body.message.strip()[:50]
        cur = db.execute(
            "INSERT INTO conversations (user_id, title) VALUES (?, ?)", (user["id"], title)
        )
        conversation_id = cur.lastrowid
    else:
        _get_owned_conversation(db, body.conversation_id, user["id"])
        conversation_id = body.conversation_id

    # Earlier turns of this conversation (last 10), oldest first, so follow-ups make sense
    rows = db.execute(
        "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT 10",
        (conversation_id,),
    ).fetchall()
    history = [dict(r) for r in reversed(rows)]

    db.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (?, 'user', ?)",
        (conversation_id, body.message),
    )

    answer, sources = answer_question(body.message, history, user)

    db.execute(
        "INSERT INTO messages (conversation_id, role, content, sources) VALUES (?, 'assistant', ?, ?)",
        (conversation_id, answer, json.dumps(sources)),
    )
    db.commit()
    return ChatResponse(conversation_id=conversation_id, answer=answer, sources=sources)


@router.get("/conversations")
def list_conversations(user: dict = Depends(get_current_user), db=Depends(get_db)):
    rows = db.execute(
        "SELECT id, title, created_at FROM conversations WHERE user_id = ? ORDER BY id DESC",
        (user["id"],),
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: int, user: dict = Depends(get_current_user), db=Depends(get_db)):
    conv = _get_owned_conversation(db, conversation_id, user["id"])
    rows = db.execute(
        "SELECT role, content, sources, created_at FROM messages WHERE conversation_id = ? ORDER BY id",
        (conversation_id,),
    ).fetchall()
    messages = [
        {
            "role": r["role"],
            "content": r["content"],
            "sources": json.loads(r["sources"]) if r["sources"] else [],
            "created_at": r["created_at"],
        }
        for r in rows
    ]
    return {"id": conv["id"], "title": conv["title"], "messages": messages}


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: int, user: dict = Depends(get_current_user), db=Depends(get_db)):
    _get_owned_conversation(db, conversation_id, user["id"])
    db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    db.commit()
    return Response(status_code=204)
