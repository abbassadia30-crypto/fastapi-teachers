from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/get_teachers")
async def get_teachers():
    return [{"id": 1, "name": "Professor X", "subject": "Telepathy"}]
git remote add origin https://github.com/abbassadia30-crypto/fastapi-teachers.git
