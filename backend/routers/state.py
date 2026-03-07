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
    """
    Crawls the DB, partitions data, and dynamicallly serializes all shards.
    """
    # A. Fetch All Data (Using the correct 'institution_id' column we fixed in pgAdmin)
    students = db.query(StudentModel).filter(StudentModel.institution_id == inst_id).all()
    attendance = db.query(AttendanceLog).filter(AttendanceLog.institution_id == inst_id).all()
    results = db.query(AcademicResult).filter(AcademicResult.institution_id == inst_id).all()
    staffs = db.query(Staff).filter(Staff.institution_id == inst_id).all()
    teachers = db.query(teacher).filter(teacher.institution_id == inst_id).all()

    # B. Load Current State
    state_rec = db.query(InstitutionState).filter(InstitutionState.institution_id == inst_id).first()
    current_registry = {"last_update": "", "shards": {}}
    if state_rec:
        try:
            current_registry = json.loads(state_rec.key_registry)
        except: pass

    # C. Build Data Blob with Dynamic Mapping
    mass_data = {"sections": {}, "personal_state": {"staff": [], "teachers": []}}

    # Partition Students and rotate keys if necessary
    for s in students:
        sec = s.section
        if sec not in mass_data["sections"]:
            mass_data["sections"][sec] = {"students": [], "results": [], "attendance": []}

            # 🔄 Update Key Logic: If data exists, ensure a valid key exists
            if sec not in current_registry["shards"] or sec == target_section or current_registry["shards"][sec] is None:
                current_registry["shards"][sec] = secrets.token_urlsafe(38)[:50]

        mass_data["sections"][sec]["students"].append(object_as_dict(s))

    # D. Attach Academic Data (FIXED: No longer uses 'res.content')
    for res in results:
        # res.target_class should match a student section (e.g., '10th-A')
        if res.target_class in mass_data["sections"]:
            mass_data["sections"][res.target_class]["results"].append(object_as_dict(res))

    # E. Attach Attendance Logs
    for log in attendance:
        if log.section_identifier in mass_data["sections"]:
            mass_data["sections"][log.section_identifier]["attendance"].append(object_as_dict(log))

    # F. Handle Personal State (Staff/Teachers)
    if target_section == "personal_state" or "personal_state" not in current_registry["shards"]:
        current_registry["shards"]["personal_state"] = secrets.token_urlsafe(38)[:50]

    for st in staffs:
        mass_data["personal_state"]["staff"].append(object_as_dict(st))
    for tc in teachers:
        mass_data["personal_state"]["teachers"].append(object_as_dict(tc))

    # If it's NOT in our new mass_data, it means the section is now empty/deleted.
    for registered_sec in list(current_registry["shards"].keys()):
        # Skip personal_state as it usually always exists
        if registered_sec == "personal_state":
            continue

        if registered_sec not in mass_data["sections"]:
            # 🎯 This sends the 'null' to the frontend as the key
            # The Sync Manager will see 'null' and delete the local .json file
            current_registry["shards"][registered_sec] = None
            print(f"📡 System: Section {registered_sec} is empty. Sending Null Signal.")

    # G. Finalize and Save
    current_registry["last_update"] = datetime.datetime.now().isoformat()

    if not state_rec:
        state_rec = InstitutionState(institution_id=inst_id)
        db.add(state_rec)

    state_rec.full_data_blob = json.dumps(mass_data, default=str) # default=str handles datetime objects
    state_rec.key_registry = json.dumps(current_registry)
    state_rec.last_indexed = datetime.datetime.utcnow()
    db.commit()

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