from fastapi import APIRouter
from services.ollama_service import generate_ai_response

from database import engine
from sqlalchemy import text

router = APIRouter()

@router.get("/chat")
def chat(prompt: str, conversation_id: int):

    ai_response = generate_ai_response(prompt)

    with engine.connect() as connection:

        # Save user message
        connection.execute(
            text("""
                INSERT INTO messages
                (conversation_id, role, text)
                VALUES
                (:conversation_id, :role, :text)
            """),
            {
                "conversation_id": conversation_id,
                "role": "user",
                "text": prompt
            }
        )

        # Save AI message
        connection.execute(
            text("""
                INSERT INTO messages
                (conversation_id, role, text)
                VALUES
                (:conversation_id, :role, :text)
            """),
            {
                "conversation_id": conversation_id,
                "role": "ai",
                "text": ai_response
            }
        )

        connection.commit()

    return {
        "response": ai_response
    }

@router.get("/history")
def history():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT prompt, response
                FROM chat_history
                ORDER BY id ASC
            """)
        )

        chats = []

        for row in result:

            chats.append({
                "role": "user",
                "text": row.prompt
            })

            chats.append({
                "role": "ai",
                "text": row.response
            })

    return chats

@router.post("/conversation")
def create_conversation():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                INSERT INTO conversations (title)
                VALUES ('New Chat')
                RETURNING id
            """)
        )

        connection.commit()

        conversation_id = result.fetchone()[0]

    return {
        "conversation_id": conversation_id
    }
@router.get("/conversations")
def get_conversations():

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT id, title
                FROM conversations
                ORDER BY id DESC
            """)
        )

        conversations = []

        for row in result:

            conversations.append({
                "id": row.id,
                "title": row.title
            })

    return conversations

@router.get("/messages/{conversation_id}")
def get_messages(conversation_id: int):

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT role, text
                FROM messages
                WHERE conversation_id = :conversation_id
                ORDER BY id ASC
            """),
            {
                "conversation_id": conversation_id
            }
        )

        messages = []

        for row in result:

            messages.append({
                "role": row.role,
                "text": row.text
            })

    return messages

@router.get("/messages/{conversation_id}")
def get_messages(conversation_id: int):

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT role, text
                FROM messages
                WHERE conversation_id = :conversation_id
                ORDER BY id ASC
            """),
            {
                "conversation_id": conversation_id
            }
        )

        messages = []

        for row in result:

            messages.append({
                "role": row.role,
                "text": row.text
            })

    return messages