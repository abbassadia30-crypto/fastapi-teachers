import json
import secrets
import datetime
import asyncio
import os
import threading
from sqlalchemy import event, Column, Integer, Text, String, DateTime, ForeignKey , inspect
from sqlalchemy.orm import Session, relationship
from fastapi import APIRouter, WebSocket, WebSocketDisconnect , Depends
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
            if sec not in current_registry["shards"] or sec == target_section:
                current_registry["shards"][sec] = secrets.token_urlsafe(38)[:50]

        # Use the dynamic dict helper instead of manual mapping
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

def run_extraction_task(inst_id, affected_section):
    db = SessionLocal()
    try:
        perform_targeted_extraction(db, inst_id, affected_section)
    finally:
        db.close()

# Hook the watcher into your models
observed_models = [StudentModel, Staff, teacher, AttendanceLog, AcademicResult]
for model in observed_models:
    event.listen(model, 'after_insert', trigger_global_reindex)
    event.listen(model, 'after_update', trigger_global_reindex)
    event.listen(model, 'after_delete', trigger_global_reindex)

# --- 4. THE LIVE SYNC WEBSOCKET ---
@router.websocket("/ws/institution-sync/{inst_id}")
async def sync_neural_state(websocket: WebSocket, inst_id: int):
    await websocket.accept()
    db = SessionLocal()
    last_pushed_registry = None

    try:
        while True:
            # Query the DB to see if the registry string has changed
            state = db.query(InstitutionState).filter(InstitutionState.institution_id == inst_id).first()
            if state and state.key_registry != last_pushed_registry:
                await websocket.send_text(state.key_registry)
                last_pushed_registry = state.key_registry

            await asyncio.sleep(2) # Poll for state changes every 2 seconds
    except WebSocketDisconnect:
        pass
    finally:
        db.close()

@router.get("/shard/{inst_id}/{section_name}")
async def get_raw_shard(inst_id: int, section_name: str, key: str, db: Session = Depends(get_db)):
    # 1. Verification
    state = db.query(InstitutionState).filter(InstitutionState.institution_id == inst_id).first()
    if not state or json.loads(state.key_registry).get(section_name) != key:
        raise HTTPException(status_code=403, detail="Key Mismatch")

    # 2. Slice the Data
    # Instead of making a file, we just parse the long string and send the piece
    all_data = json.loads(state.full_data_blob)

    # Logic: Get section data or personal_state
    shard = all_data.get("sections", {}).get(section_name) if section_name != "personal_state" else all_data.get("personal_state")

    if not shard:
        raise HTTPException(status_code=404, detail="Data not found")

    return shard