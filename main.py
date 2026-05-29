from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

from database import engine
from sqlalchemy import text

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "AI Workspace Backend Running"}

@app.get("/chat")
def chat(prompt: str):

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    data = response.json()

    ai_response = data["response"]

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

@app.get("/history")
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

   