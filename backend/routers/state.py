import json
import secrets
import datetime
import asyncio
import os
import threading
from sqlalchemy import event, Column, Integer, Text, String, DateTime, ForeignKey, inspect
from sqlalchemy.orm import Session, relationship
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from backend.database import get_db, SessionLocal
from backend.models.admin.dashboard import student as StudentModel, Staff, teacher
from backend.models.admin.document import AttendanceLog, AcademicResult
from backend.models.state import InstitutionState

router = APIRouter(prefix="/state", tags=["Institutional Intelligence"])

# Global tracker for real-time pushing
active_connections = {}

def object_as_dict(obj):
    """Converts SQLAlchemy model objects to dictionaries for JSON serialization."""
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}

def perform_targeted_extraction(db: Session, inst_id: int, target_section: str = None):
    """
    The Core Engine: Crawls DB, partitions data into shards, and updates the registry.
    """
    # 1. Data Retrieval
    students = db.query(StudentModel).filter(StudentModel.institution_id == inst_id).all()
    attendance = db.query(AttendanceLog).filter(AttendanceLog.institution_id == inst_id).all()
    results = db.query(AcademicResult).filter(AcademicResult.institution_id == inst_id).all()
    staffs = db.query(Staff).filter(Staff.institution_id == inst_id).all()
    teachers = db.query(teacher).filter(teacher.institution_id == inst_id).all()

    # 2. State Management
    state_rec = db.query(InstitutionState).filter(InstitutionState.institution_id == inst_id).first()
    if not state_rec:
        state_rec = InstitutionState(institution_id=inst_id, key_registry='{"shards": {}}', full_data_blob='{}')
        db.add(state_rec)
        db.commit()
        db.refresh(state_rec)

    current_registry = json.loads(state_rec.key_registry)
    mass_data = {"sections": {}, "personal_state": {"staff": [], "teachers": []}}

    # 3. Section Mapping
    active_sections = set(
        [s.section for s in students if s.section] +
        [log.section_identifier for log in attendance if log.section_identifier] +
        [res.target_class for res in results if res.target_class]
    )

    # 4. Personal State Logic (Staff/Teachers)
    if "personal_state" not in current_registry["shards"] or target_section == "personal_state":
        current_registry["shards"]["personal_state"] = {
            "key": secrets.token_urlsafe(32),
            "mode": "update"
        }

    mass_data["personal_state"]["staff"] = [object_as_dict(st) for st in staffs]
    mass_data["personal_state"]["teachers"] = [object_as_dict(tc) for tc in teachers]

    # 5. Section Sharding Logic
    for sec_name in active_sections:
        mass_data["sections"][sec_name] = {
            "students": [object_as_dict(s) for s in students if s.section == sec_name],
            "results": [object_as_dict(r) for r in results if r.target_class == sec_name],
            "attendance": [object_as_dict(l) for l in attendance if l.section_identifier == sec_name]
        }

        # If it's a new section or the one that just changed, rotate the key
        if sec_name not in current_registry["shards"] or sec_name == target_section:
            current_registry["shards"][sec_name] = {
                "key": secrets.token_urlsafe(32),
                "mode": "update"
            }

    # 6. Cleanup Logic (DELETION MODE)
    # If a section exists in the registry but no longer has data in the DB
    for registered_sec in list(current_registry["shards"].keys()):
        if registered_sec == "personal_state": continue

        if registered_sec not in active_sections:
            current_registry["shards"][registered_sec] = {
                "key": "DELETED",
                "mode": "delete" # Signal frontend to delete local file
            }

    # 7. Persistence
    state_rec.key_registry = json.dumps(current_registry)
    state_rec.full_data_blob = json.dumps(mass_data)
    state_rec.last_updated = datetime.datetime.utcnow()
    db.commit()

    return current_registry

def run_extraction_task(inst_id, affected_section):
    """Background task to ensure the Registry is updated and pushed to all active sockets."""
    db = SessionLocal()
    try:
        new_registry = perform_targeted_extraction(db, inst_id, affected_section)

        # 🚀 REAL-TIME PUSH: Immediately notify all open WebSockets for this institution
        if inst_id in active_connections:
            # We use a separate thread-safe event loop for pushing from the background thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            for ws in active_connections[inst_id]:
                try:
                    loop.run_until_complete(ws.send_text(json.dumps(new_registry)))
                except Exception:
                    pass # Connection likely closed
            loop.close()
    finally:
        db.close()

def trigger_global_reindex(mapper, connection, target):
    """SQLAlchemy listener: Triggers when any student, staff, or result is changed."""
    inst_id = getattr(target, 'institution_id', None)
    affected_section = getattr(target, 'section', None) or getattr(target, 'section_identifier', None) or getattr(target, 'target_class', None)

    if not affected_section and isinstance(target, (Staff, teacher)):
        affected_section = "personal_state"

    if inst_id:
        # Run in thread to not block the main API response
        threading.Thread(target=run_extraction_task, args=(inst_id, affected_section)).start()

# Register Listeners
observed_models = [StudentModel, Staff, teacher, AttendanceLog, AcademicResult]
for model in observed_models:
    event.listen(model, 'after_insert', trigger_global_reindex)
    event.listen(model, 'after_update', trigger_global_reindex)
    event.listen(model, 'after_delete', trigger_global_reindex)

@router.websocket("/ws/institution-sync/{inst_id}")
async def sync_neural_state(websocket: WebSocket, inst_id: int):
    await websocket.accept()

    # 🏛️ TIMING FIX: Wait briefly for any background DB threads to finish before first push
    await asyncio.sleep(0.5)

    db = SessionLocal()
    try:
        current_registry = perform_targeted_extraction(db, inst_id)
        await websocket.send_text(json.dumps(current_registry))
    finally:
        db.close()

    # Register connection
    if inst_id not in active_connections:
        active_connections[inst_id] = []
    active_connections[inst_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming pings to prevent timeout
            if "ping" in data:
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        active_connections[inst_id].remove(websocket)

@router.get("/shard/{inst_id}/{section_name}")
async def get_raw_shard(inst_id: int, section_name: str, key: str, db: Session = Depends(get_db)):
    state = db.query(InstitutionState).filter(InstitutionState.institution_id == inst_id).first()
    if not state:
        raise HTTPException(status_code=404, detail="Sync State not initialized")

    registry = json.loads(state.key_registry)
    expected_data = registry.get("shards", {}).get(section_name)

    # Key Validation
    if not expected_data or expected_data.get("key") != key:
        raise HTTPException(status_code=403, detail="Key Mismatch or Expired")

    all_data = json.loads(state.full_data_blob)

    if section_name == "personal_state":
        return all_data.get("personal_state", {"staff": [], "teachers": []})

    return all_data.get("sections", {}).get(section_name, {"students": [], "results": [], "attendance": []})
