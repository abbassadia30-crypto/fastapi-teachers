from fastapi import FastAPI, Depends
from pydantic import BaseModel
import ollama

app = FastAPI()

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.post("/chat")
async def chat_with_agent(request: ChatRequest):
    # IDENTITY INJECTION: We tell the model who the user is
    system_prompt = f"You are the personal assistant for Student ID: {request.user_id}. Access only their data."

    response = ollama.chat(model='llama3', messages=[
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': request.message},
    ])

    return {"response": response['message']['content']}