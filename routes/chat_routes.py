from fastapi import APIRouter
from services.ollama_service import generate_ai_response

from database import engine
from sqlalchemy import text

router = APIRouter()

@router.get("/chat")
def chat(prompt: str):

    ai_response = generate_ai_response(prompt)

    with engine.connect() as connection:

        connection.execute(
            text("""
                INSERT INTO chat_history (prompt, response)
                VALUES (:prompt, :response)
            """),
            {
                "prompt": prompt,
                "response": ai_response
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