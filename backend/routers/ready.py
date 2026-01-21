from fastapi import APIRouter, Depends, HTTPException, Query, Body  ,status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
import csv
import io
from fastapi.responses import StreamingResponse
from .. import models, schemas, database
from .auth import get_current_user

router = APIRouter(prefix="/ready", tags=["Institution creation"])

@router.post("/create-school" , status_code=status.HTTP_201_CREATED)
async def create_school(
        payload: schemas.SchoolSchema,
        db: Session = Depends(database.get_db),
        current_user: models.User = Depends(get_current_user)
):
    # 1. Check if user already owns an institution
    existing = db.query(models.Institution).filter(models.Institution.owner_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already own an institution.")

    # 2. Create the School (SQLAlchemy handles the Institution part automatically)
    new_school = models.School(
        owner_id=current_user.id,
        name=payload.name,
        type="school", # Sets the polymorphic identity
        address=payload.address,
        email=payload.email,
        principal_name=payload.principal_name,
        campus=payload.campus,
        website=payload.website
    )

    current_user.has_institution = True
    current_user.institution_id = new_school.id

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    db.add(new_school )
    db.commit()
    db.refresh(new_school )

    return {
        "status": "success",
        "message": "Institution created successfully",
        "institution_id": new_school.institution_id
    }

@router.post("/create-academy", status_code=status.HTTP_201_CREATED)
async def create_academy(
        payload: schemas.AcademySchema,
        db: Session = Depends(database.get_db),
        current_user: models.User = Depends(get_current_user)
):
    # 1. Ownership Guard
    existing = db.query(models.Institution).filter(models.Institution.owner_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already owns an active institution.")

    # 2. Create the Academy
    # SQLAlchemy uses "polymorphic_identity": "academy" to map this to the academies table
    new_academy = models.Academy(
        owner_id=current_user.id,
        name=payload.name,
        type="academy",
        address=payload.address,
        email=payload.email,
        edu_type=payload.edu_type, # e.g., "Medical", "Technical", "Arts"
        campus_name=payload.campus_name,
        contact=payload.contact
    )

    current_user.has_institution = True
    current_user.institution_id = new_academy.id

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    db.add(new_academy )
    db.commit()
    db.refresh(new_academy )

    return {
        "status": "success",
        "message": "College/Academy registered successfully",
        "institution_id": new_academy.institution_id
    }

@router.post("/create-college", status_code=status.HTTP_201_CREATED)
async def create_college(
        payload: schemas.CollegeSchema,
        db: Session = Depends(database.get_db),
        current_user: models.User = Depends(get_current_user)
):
    # 1. Security: Check if this email already owns an institution
    existing = db.query(models.Institution).filter(models.Institution.owner_id == current_user.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already owns an active institution."
        )

    # 2. Instantiate the College polymorphic model
    new_college = models.College(
        owner_id=current_user.id,
        name=payload.name,
        type="college", # Matches polymorphic_identity
        address=payload.address,
        email=payload.email,
        dean_name=payload.dean_name,
        code=payload.code,
        uni=payload.uni
    )

    current_user.has_institution = True
    current_user.institution_id = new_college.id
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    db.add(new_college)
    db.commit()
    db.refresh(new_college)

    return {
        "status": "success",
        "message": "College registered under the institution successfully",
        "institution_id": new_college.institution_id
    }