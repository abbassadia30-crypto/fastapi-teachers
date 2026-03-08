import json
import secrets
import datetime
import asyncio
import threading
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from backend.database import get_db, SessionLocal
from backend.models.state import InstitutionState
# Import your specific institution models
from backend.models.admin.dashboard import student as StudentModel, Staff
from backend.models.admin.document import AttendanceLog, AcademicResult

router = APIRouter(prefix="/state", tags=["Institutional Intelligence"])

# Tracker for real-time WebSocket pushing
active_connections = {}

def object_as_dict(obj):
    """Converts any SQLAlchemy model instance into a standard Python Dictionary."""
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}

def perform_targeted_extraction(db: Session, inst_id: int, target_section: str = None):
    """
    The Core Engine:
    1. Crawls DB for all data related to the institution.
    2. Shards data into logical sections (Classes/Staff).
    3. Updates the 'Registry' (the map of keys) in the DB.
    """
    # 1. Fetch Raw Data Pools
    students = db.query(StudentModel).filter_by(institution_id=inst_id).all()
    attendance = db.query(AttendanceLog).filter_by(institution_id=inst_id).all()
    results = db.query(AcademicResult).filter_by(institution_id=inst_id).all()
    staffs = db.query(Staff).filter_by(institution_id=inst_id).all()

    # 2. Manage the InstitutionState Record (The Persistence Layer)
    state_rec = db.query(InstitutionState).filter_by(institution_id=inst_id).first()
    if not state_rec:
        state_rec = InstitutionState(institution_id=inst_id, key_registry='{"shards": {}}', full_data_blob='{}')
        db.add(state_rec)
        db.commit()
        db.refresh(state_rec)

    current_registry = json.loads(state_rec.key_registry)
    mass_data = {"sections": {}, "personal_state": {"staff": []}}

    # 3. Identify Active Sections (Classes)
    active_sections = set([s.section for s in students if s.section])

    # 4. Handle Staff/Teachers (Personal State)
    mass_data["personal_state"]["staff"] = [object_as_dict(st) for st in staffs]
    if "personal_state" not in current_registry["shards"] or target_section == "personal_state":
        current_registry["shards"]["personal_state"] = {"key": secrets.token_hex(16), "mode": "update"}

    # 5. Section Sharding (The Loop)
    for sec_name in active_sections:
        mass_data["sections"][sec_name] = {
            "students": [object_as_dict(s) for s in students if s.section == sec_name],
            "results": [object_as_dict(r) for r in results if r.target_class == sec_name],
            "attendance": [object_as_dict(l) for l in attendance if l.section_identifier == sec_name]
        }

        # If it's new or was the target of a change, rotate the key
        if sec_name not in current_registry["shards"] or sec_name == target_section:
            current_registry["shards"][sec_name] = {"key": secrets.token_hex(16), "mode": "update"}

    # 6. Cleanup Logic (DELETION MODE)
    for registered_sec in list(current_registry["shards"].keys()):
        if registered_sec != "personal_state" and registered_sec not in active_sections:
            current_registry["shards"][registered_sec] = {"key": "NULL", "mode": "delete"}

    # 7. Persistence
    state_rec.key_registry = json.dumps(current_registry)
    state_rec.full_data_blob = json.dumps(mass_data)
    state_rec.last_updated = datetime.datetime.utcnow()
    db.commit()

    return current_registry

# --- REAL-TIME LISTENERS ---

def trigger_reindex(mapper, connection, target):
    """Listener: Detects DB changes and triggers a background sync."""
    inst_id = getattr(target, 'institution_id', None)
    if not inst_id: return

    def run_sync():
        db = SessionLocal()
        try:
            new_reg = perform_targeted_extraction(db, inst_id)
            # Push to WebSocket if active
            if inst_id in active_connections:
                loop = asyncio.new_event_loop()
                for ws in active_connections[inst_id]:
                    try: loop.run_until_complete(ws.send_json(new_reg))
                    except: pass
                loop.close()
        finally: db.close()

    threading.Thread(target=run_sync).start()

# Registering the 'Observed Models'
for model in [StudentModel, Staff, AttendanceLog, AcademicResult]:
    event.listen(model, 'after_insert', trigger_reindex)
    event.listen(model, 'after_update', trigger_reindex)
    event.listen(model, 'after_delete', trigger_reindex)

# --- API ENDPOINTS ---

@router.websocket("/ws/institution-sync/{inst_id}")
async def sync_websocket(websocket: WebSocket, inst_id: int):
    await websocket.accept()

    db = SessionLocal()
    try:
        # Initial Push
        reg = perform_targeted_extraction(db, inst_id)
        await websocket.send_json(reg)
    finally: db.close()

    if inst_id not in active_connections: active_connections[inst_id] = []
    active_connections[inst_id].append(websocket)

    try:
        while True:
            msg = await websocket.receive_text()
            if msg == "ping": await websocket.send_text("pong")
    except WebSocketDisconnect:
        active_connections[inst_id].remove(websocket)

@router.get("/shard/{inst_id}/{section_name}")
async def get_shard(inst_id: int, section_name: str, key: str, db: Session = Depends(get_db)):
    state = db.query(InstitutionState).filter_by(institution_id=inst_id).first()
    if not state: raise HTTPException(status_code=404)

    registry = json.loads(state.key_registry)
    shard_info = registry.get("shards", {}).get(section_name)

    if not shard_info or shard_info['key'] != key:
        raise HTTPException(status_code=403, detail="Key Mismatch")

    all_data = json.loads(state.full_data_blob)
    if section_name == "personal_state":
        return all_data.get("personal_state")
    return all_data.get("sections", {}).get(section_name)
