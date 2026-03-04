import json
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

# Internal Imports
from ..database import get_db
from ..models.chat import Message, Conversation, ChatType
from ..models.User import User
from .auth import get_current_user

router = APIRouter(prefix="/chat", tags=["Neural Chat Hub"])

# --- 🚀 CONNECTION MANAGER (Internal Logic) ---
class ChatManager:
    def __init__(self):
        # Maps user_id to their active WebSocket connection
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"📡 User {user_id} linked to Neural Hub.")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"🔌 User {user_id} disconnected.")

    async def send_personal_message(self, message: dict, recipient_id: int):
        if recipient_id in self.active_connections:
            await self.active_connections[recipient_id].send_json(message)
            return True
        return False

chat_manager = ChatManager()

# --- 🛰️ WEBSOCKET ROUTE ---
@router.websocket("/ws/{token}")
async def chat_endpoint(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    # 1. Secure Handshake: Verify JWT
    try:
        user = await get_current_user(token, db)
    except Exception:
        await websocket.close(code=1008)
        return

    await chat_manager.connect(user.id, websocket)

    try:
        while True:
            # Receive JSON from App (Student or Teacher)
            data = await websocket.receive_json()
            # Expected format: {"conversation_id": 1, "content": "Hello Teacher"}

            # 2. Institutional Archiving (Save to Postgres)
            new_msg = Message(
                conversation_id=data['conversation_id'],
                sender_id=user.id,
                content=data['content']
            )
            db.add(new_msg)
            db.commit()
            db.refresh(new_msg)

            # 3. Dynamic Routing
            conversation = db.query(Conversation).filter(Conversation.id == data['conversation_id']).first()

            if conversation:
                # Surpass Microsoft Tools: Instant delivery to all participants
                for participant in conversation.participants:
                    if participant.id != user.id:
                        # Attempt WebSocket Delivery
                        delivered = await chat_manager.send_personal_message({
                            "msg_id": new_msg.id,
                            "sender_id": user.id,
                            "sender_name": user.user_name,
                            "role": user.type, # 'student', 'teacher', etc.
                            "content": new_msg.content,
                            "timestamp": datetime.utcnow().isoformat()
                        }, participant.id)

                        # 4. Neural Link Fallback (FCM)
                        if not delivered:
                            # If they are offline, we trigger the FCM alert you set up earlier
                            from .fcm_logic import send_push_notification # Hypothetical helper
                            send_push_notification(
                                token=participant.fcm_token,
                                title=f"New message from {user.user_name}",
                                body=new_msg.content[:50],
                                data={"type": "chat", "conv_id": str(conversation.id)}
                            )

    except WebSocketDisconnect:
        chat_manager.disconnect(user.id)
    except Exception as e:
        print(f"⚠️ Hub Error: {e}")
        chat_manager.disconnect(user.id)