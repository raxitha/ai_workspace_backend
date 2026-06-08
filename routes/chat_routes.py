from fastapi import APIRouter
from services.ollama_service import generate_ai_response
from fastapi.responses import PlainTextResponse
from fastapi import UploadFile

from database import engine
from sqlalchemy import text

router = APIRouter()

@router.get("/chat")
def chat(
    prompt: str,
    conversation_id: int,
    model: str = "llama3"
):
    knowledge = get_knowledge(
        prompt
    )
    full_prompt = f"""
    Answer using the provided context.

    Context:
    {knowledge}

    Question:
    {prompt}
    """
    response = generate_ai_response(
        full_prompt,
        model
    )

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT title
                FROM conversations
                WHERE id = :conversation_id
            """),
            {
                "conversation_id": conversation_id
            }
        )

        current_title = result.fetchone()[0]

        if current_title == "New Chat":

            connection.execute(
                text("""
                    UPDATE conversations
                    SET title = :title
                    WHERE id = :conversation_id
                """),
                {
                    "title": prompt[:30],
                    "conversation_id": conversation_id
                }
            )

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
                "text": response
            }
        )

        connection.commit()

    return {
        "response": response
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

@router.delete("/conversation/{conversation_id}")
def delete_conversation(conversation_id: int):

    with engine.connect() as connection:

        # Delete messages first
        connection.execute(
            text("""
                DELETE FROM messages
                WHERE conversation_id = :conversation_id
            """),
            {
                "conversation_id": conversation_id
            }
        )

        # Delete conversation
        connection.execute(
            text("""
                DELETE FROM conversations
                WHERE id = :conversation_id
            """),
            {
                "conversation_id": conversation_id
            }
        )

        connection.commit()

    return {
        "message": "Conversation deleted"
    }

@router.put("/conversation/{conversation_id}")
def rename_conversation(
    conversation_id: int,
    title: str
):

    with engine.connect() as connection:

        connection.execute(
            text("""
                UPDATE conversations
                SET title = :title
                WHERE id = :conversation_id
            """),
            {
                "title": title,
                "conversation_id": conversation_id
            }
        )

        connection.commit()

    return {
        "message": "Conversation renamed"
    }

@router.get(
    "/export/{conversation_id}",
    response_class=PlainTextResponse
)
def export_conversation(
    conversation_id: int
):

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT role,text
                FROM messages
                WHERE conversation_id = :conversation_id
                ORDER BY id
            """),
            {
                "conversation_id": conversation_id
            }
        )

        messages = result.fetchall()

    output = ""

    for message in messages:

        output += (
            f"{message.role.upper()}:\n"
            f"{message.text}\n\n"
        )

    return output

@router.post("/upload")
async def upload_file(
    file: UploadFile
):

    content = (
        await file.read()
    ).decode("utf-8")
    chunks = [
        content[i:i+500]
        for i in range(
            0,
            len(content),
            500
        )
    ]

    with engine.begin() as connection:

        for chunk in chunks:

            connection.execute(
                text("""
                    INSERT INTO knowledge_chunks
                    (content)
                    VALUES
                    (:content)
                """),
                {
                    "content": chunk
                }
            )

    return {
        "message": "Uploaded"
    }

def get_knowledge(
    question
):

    keywords = (
        question.lower()
        .split()
    )

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT content
                FROM knowledge_chunks
            """)
        )

        rows = result.fetchall()

    matched_chunks = []

    for row in rows:

        chunk = row[0]

        for keyword in keywords:

            if keyword in chunk.lower():

                matched_chunks.append(
                    chunk
                )

                break

    return "\n\n".join(
        matched_chunks[:5]
    )