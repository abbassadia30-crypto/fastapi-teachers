from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.database import get_db
from backend.models.user import User
from backend.models.admin.institution import Institution, Owner
from typing import Optional

router = APIRouter(prefix="/explore", tags=["explore"])

@router.get("/users")
async def get_all_users(
        query: Optional[str] = Query(None),
        db: Session = Depends(get_db)
):
    # Filter out users who haven't finished verification
    base_query = db.query(User).filter(User.type != "verified_user")

    if query:
        # Search in name or email
        base_query = base_query.filter(
            or_(
                User.user_name.ilike(f"%{query}%"),
                User.user_email.ilike(f"%{query}%")
            )
        )

    users = base_query.limit(20).all() # Limit for performance
    return [
        {
            "name": u.user_name,
            "role": u.type.capitalize(),
            "email": u.user_email,
            "subject": "General Member"
        } for u in users
    ]

@router.get("/institutions")
async def get_all_institutions(
        query: Optional[str] = Query(None),
        db: Session = Depends(get_db)
):
    # Join with owner to show who created it
    base_query = db.query(Institution, Owner).join(Owner)

    if query:
        # Search by Institution Name, Type, or 8-digit Reference
        base_query = base_query.filter(
            or_(
                Institution.name.ilike(f"%{query}%"),
                Institution.type.ilike(f"%{query}%"),
                Institution.inst_ref.ilike(f"%{query}%")
            )
        )

    results = base_query.limit(20).all()
    return [
        {
            "name": inst.name,
            "type": inst.type,
            "owner": owner.user_name,
            "ref": inst.inst_ref
        } for inst, owner in results
    ]