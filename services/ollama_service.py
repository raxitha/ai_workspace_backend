import requests

def generate_ai_response(
    prompt,
    model
):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    )

    data = response.json()

    return data["response"]