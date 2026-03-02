import json
import secrets
import datetime
import asyncio
import os
import threading
from sqlalchemy import event, Column, Integer, Text, String, DateTime, ForeignKey
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

# --- 1. THE PERSISTENCE TABLE (The State Cache) ---
class InstitutionState(Base):
    __tablename__ = "institution_intelligence_state"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), unique=True)

    # Store the massive JSON of all sections
    full_data_blob = Column(Text, nullable=False)
    # Store the 50-character key map (The Registry)
    key_registry = Column(Text, nullable=False)
    last_indexed = Column(DateTime, default=datetime.datetime.utcnow)

    institution = relationship("Institution")

# --- 2. THE TARGETED EXTRACTION ENGINE ---
def perform_targeted_extraction(db: Session, inst_id: int, target_section: str = None):
    """
    Crawls the DB, partitions data, and ONLY rotates the key for target_section.
    """
    # A. Fetch All Data for the Institution
    students = db.query(StudentModel).filter(StudentModel.institution_id == inst_id).all()
    attendance = db.query(AttendanceLog).filter(AttendanceLog.institution_id == inst_id).all()
    results = db.query(AcademicResult).filter(AcademicResult.institution_id == inst_id).all()
    staffs = db.query(Staff).filter(Staff.institution_id == inst_id).all()
    teachers = db.query(teacher).filter(teacher.institution_id == inst_id).all()

    # B. Load Current State (to preserve existing keys)
    state_rec = db.query(InstitutionState).filter(InstitutionState.institution_id == inst_id).first()

    current_registry = {"last_update": "", "shards": {}}
    if state_rec:
        try:
            current_registry = json.loads(state_rec.key_registry)
        except: pass

    # C. Build Massive Data Blob
    mass_data = {"sections": {}, "personal_state": {"staff": [], "teachers": []}}

    for s in students:
        sec = s.section
        if sec not in mass_data["sections"]:
            mass_data["sections"][sec] = {"students": [], "results": [], "attendance": []}
            # If section key doesn't exist OR it's the target section, generate new 50-char key
            if sec not in current_registry["shards"] or sec == target_section:
                current_registry["shards"][sec] = secrets.token_urlsafe(38)[:50]

        mass_data["sections"][sec]["students"].append({
            "id": s.id, "name": s.name, "father": s.father_name, "fee": s.fee, "active": s.is_active
        })

    # D. Attach Academic Data
    for res in results:
        if res.target_class in mass_data["sections"]:
            mass_data["sections"][res.target_class]["results"].append(res.content)

    for log in attendance:
        if log.section_identifier in mass_data["sections"]:
            mass_data["sections"][log.section_identifier]["attendance"].append(log.attendance_data)

    # E. Handle Personal State (Staff/Teachers)
    if target_section == "personal_state" or "personal_state" not in current_registry["shards"]:
        current_registry["shards"]["personal_state"] = secrets.token_urlsafe(38)[:50]

    for st in staffs: mass_data["personal_state"]["staff"].append({"name": st.name, "pos": st.position})
    for tc in teachers: mass_data["personal_state"]["teachers"].append({"name": tc.name, "sub": tc.subject_expertise})

    # F. Save and Finalize
    current_registry["last_update"] = datetime.datetime.now().isoformat()
    final_blob = json.dumps(mass_data)
    final_registry = json.dumps(current_registry)

    if not state_rec:
        state_rec = InstitutionState(institution_id=inst_id)
        db.add(state_rec)

    state_rec.full_data_blob = final_blob
    state_rec.key_registry = final_registry
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