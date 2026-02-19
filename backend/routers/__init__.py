import firebase_admin
from firebase_admin import messaging, credentials
import os

# Initialize Firebase here (Safe and centralized)

# This gets the directory where 'backend' folder lives (the project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# For Render, this should point to /opt/render/project/src/
cred_path = os.path.join(BASE_DIR, "firebase-adminsdk.json")

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Firebase Init Error: {e}")

def send_push_to_user(user_fcm_token, title, body):
    if not user_fcm_token:
        return None
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=user_fcm_token,
        )
        response = messaging.send(message)
        return response
    except Exception as e:
        print(f"FCM Send Error: {e}")
        return None