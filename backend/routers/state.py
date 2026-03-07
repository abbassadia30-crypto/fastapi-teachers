import json
import secrets
import datetime
import asyncio
import os
import threading
from sqlalchemy import event, Column, Integer, Text, String, DateTime, ForeignKey , inspect
from sqlalchemy.orm import Session, relationship
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from backend.database import get_db
# Import your existing database and models
from backend.database import Base, SessionLocal
from backend.models.admin.dashboard import student as StudentModel, Staff, teacher
from backend.models.admin.document import AttendanceLog, AcademicResult
from backend.models.admin.institution import Institution
from backend.models.state import InstitutionState

router = APIRouter(prefix="/state", tags=["Institutional Intelligence"])

def object_as_dict(obj):
    """
    Automatically converts any SQLAlchemy model object to a dictionary.
    This replaces manual mapping and prevents AttributeError when columns change.
    """
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}

def perform_targeted_extraction(db: Session, inst_id: int, target_section: str = None):
    # 1. Fetch all data pools
    students = db.query(StudentModel).filter(StudentModel.institution_id == inst_id).all()
    attendance = db.query(AttendanceLog).filter(AttendanceLog.institution_id == inst_id).all()
    results = db.query(AcademicResult).filter(AcademicResult.institution_id == inst_id).all()
    staffs = db.query(Staff).filter(Staff.institution_id == inst_id).all()
    teachers = db.query(teacher).filter(teacher.institution_id == inst_id).all()

    # 2. Setup state and registry
    state_rec = db.query(InstitutionState).filter(InstitutionState.institution_id == inst_id).first()
    current_registry = json.loads(state_rec.key_registry) if state_rec else {"shards": {}}
    mass_data = {"sections": {}, "personal_state": {"staff": [], "teachers": []}}

    # 3. Identify all "Active" sections across all data types
    # We collect every unique section name that has at least one record
    active_sections = set(
        [s.section for s in students] +
        [log.section_identifier for log in attendance] +
        [res.target_class for res in results]
    )

    # 4. Process Personal State (Staff/Teachers) - This is always 'update' mode
    current_registry["shards"]["personal_state"] = {
        "key": secrets.token_urlsafe(38)[:50] if target_section == "personal_state" else current_registry["shards"].get("personal_state", {}).get("key"),
        "mode": "update"
    }
    mass_data["personal_state"]["staff"] = [object_as_dict(st) for st in staffs]
    mass_data["personal_state"]["teachers"] = [object_as_dict(tc) for tc in teachers]

    # 5. Build Section Shards
    for sec_name in active_sections:
        mass_data["sections"][sec_name] = {
            "students": [object_as_dict(s) for s in students if s.section == sec_name],
            "results": [object_as_dict(r) for r in results if r.target_class == sec_name],
            "attendance": [object_as_dict(l) for l in attendance if l.section_identifier == sec_name]
        }

        # 🔄 MODE: UPDATE
        # If it's a new section or the target of an update, give it a new key
        if sec_name not in current_registry["shards"] or sec_name == target_section:
            current_registry["shards"][sec_name] = {
                "key": secrets.token_urlsafe(38)[:50],
                "mode": "update"
            }

    # 🗑️ MODE: DELETE (The Kill Signal for ALL data types)
    for registered_sec in list(current_registry["shards"].keys()):
        if registered_sec == "personal_state": continue

        if registered_sec not in active_sections:
            current_registry["shards"][registered_sec] = {
                "key": None,
                "mode": "delete"
            }

    # ... Save state_rec logic ...
    return current_registry

# 🔥 FIX 1: Define the missing background task
def run_extraction_task(inst_id, affected_section):
    """Background task to refresh the state and notify connected apps"""
    db = SessionLocal()
    try:
        # Perform the actual data extraction
        new_registry = perform_targeted_extraction(db, inst_id, affected_section)

        # 🔥 FIX 2: Check active_connections and push the new registry
        # We use the global active_connections dict to find the right institution
        if inst_id in active_connections:
            # Create a loop for the thread to send the message safely
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            for ws in active_connections[inst_id]:
                try:
                    loop.run_until_complete(ws.send_text(json.dumps(new_registry)))
                except Exception as e:
                    print(f"Failed to push to a socket: {e}")
    except Exception as e:
        print(f"Extraction Task Error: {e}")
    finally:
        db.close()

# --- 3. THE EVENT WATCHER (Insert, Update, Delete) ---
def trigger_global_reindex(mapper, connection, target):
    """Detects any change and triggers targeted re-indexing"""
    inst_id = getattr(target, 'institution_id', None) or getattr(target, 'institution_ref', None)

    # Identify which section changed
    affected_section = getattr(target, 'section', None) or getattr(target, 'section_identifier', None)
    if not affected_section and isinstance(target, (Staff, teacher)):
        affected_section = "personal_state"

    if inst_id:
        # Background thread to avoid blocking the main POST/PUT/PATCH request
        thread = threading.Thread(target=run_extraction_task, args=(inst_id, affected_section))
        thread.start()

# Hook the watcher into your models
observed_models = [StudentModel, Staff, teacher, AttendanceLog, AcademicResult]
for model in observed_models:
    event.listen(model, 'after_insert', trigger_global_reindex)
    event.listen(model, 'after_update', trigger_global_reindex)
    event.listen(model, 'after_delete', trigger_global_reindex)

# --- 4. THE LIVE SYNC WEBSOCKET ---
# A simple global list to keep track of active sockets
active_connections = {}

@router.websocket("/ws/institution-sync/{inst_id}")
async def sync_neural_state(websocket: WebSocket, inst_id: int, db: Session = Depends(get_db)):
    await websocket.accept()

    # 🔥 1. IMMEDIATE PUSH: Send current state as soon as they connect
    # This covers everything that happened while they were offline
    current_registry = perform_targeted_extraction(db, inst_id)
    await websocket.send_text(json.dumps(current_registry))

    if inst_id not in active_connections:
        active_connections[inst_id] = []
    active_connections[inst_id].append(websocket)

    try:
        while True:
            await websocket.receive_text() # Keep-alive
    except WebSocketDisconnect:
        active_connections[inst_id].remove(websocket)

@router.get("/shard/{inst_id}/{section_name}")
async def get_raw_shard(inst_id: int, section_name: str, key: str, db: Session = Depends(get_db)):
    state = db.query(InstitutionState).filter(InstitutionState.institution_id == inst_id).first()
    if not state:
        raise HTTPException(status_code=404, detail="Institution State not initialized")

    registry = json.loads(state.key_registry)
    expected_key = registry.get("shards", {}).get(section_name)

    if expected_key != key:
        raise HTTPException(status_code=403, detail="Key Mismatch")

    all_data = json.loads(state.full_data_blob)

    # 🏛️ REFINED LOGIC: Never return 404 if the key was valid
    if section_name == "personal_state":
        shard = all_data.get("personal_state", {"staff": [], "teachers": []})
    else:
        # If section is missing in blob but has a key, return an empty template
        shard = all_data.get("sections", {}).get(section_name, {
            "students": [], "results": [], "attendance": []
        })

    return shard
