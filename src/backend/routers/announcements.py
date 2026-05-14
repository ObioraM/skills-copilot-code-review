"""Announcement endpoints for the High School Management System API."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from bson.errors import InvalidId
from bson.objectid import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementPayload(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    expiration_date: str
    start_date: Optional[str] = None


def _validate_and_normalize_dates(
    expiration_date: str,
    start_date: Optional[str]
) -> Dict[str, Optional[str]]:
    try:
        expiration = date.fromisoformat(expiration_date)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Expiration date must be in YYYY-MM-DD format"
        ) from exc

    normalized_start: Optional[str] = None
    if start_date:
        try:
            start = date.fromisoformat(start_date)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Start date must be in YYYY-MM-DD format"
            ) from exc

        if start > expiration:
            raise HTTPException(
                status_code=400,
                detail="Start date must be on or before expiration date"
            )
        normalized_start = start.isoformat()

    return {
        "expiration_date": expiration.isoformat(),
        "start_date": normalized_start
    }


def _require_signed_in_user(teacher_username: Optional[str]) -> Dict[str, Any]:
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    return teacher


def _serialize_announcement(announcement: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(announcement["_id"]),
        "message": announcement.get("message", ""),
        "start_date": announcement.get("start_date"),
        "expiration_date": announcement.get("expiration_date", ""),
        "created_by": announcement.get("created_by"),
        "created_at": announcement.get("created_at"),
        "updated_at": announcement.get("updated_at")
    }


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get currently active announcements for public display."""
    today = date.today().isoformat()
    query = {
        "expiration_date": {"$gte": today},
        "$or": [
            {"start_date": None},
            {"start_date": ""},
            {"start_date": {"$lte": today}}
        ]
    }
    cursor = announcements_collection.find(query).sort([
        ("expiration_date", 1),
        ("_id", -1)
    ])
    return [_serialize_announcement(item) for item in cursor]


@router.get("/manage", response_model=List[Dict[str, Any]])
def get_all_announcements(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Get all announcements for signed-in staff management."""
    _require_signed_in_user(teacher_username)
    cursor = announcements_collection.find({}).sort([
        ("expiration_date", 1),
        ("_id", -1)
    ])
    return [_serialize_announcement(item) for item in cursor]


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_announcement(
    payload: AnnouncementPayload,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Create a new announcement. Signed-in staff only."""
    teacher = _require_signed_in_user(teacher_username)
    dates = _validate_and_normalize_dates(
        expiration_date=payload.expiration_date,
        start_date=payload.start_date
    )

    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    doc = {
        "message": payload.message.strip(),
        "start_date": dates["start_date"],
        "expiration_date": dates["expiration_date"],
        "created_by": teacher.get("username"),
        "created_at": now,
        "updated_at": now
    }
    result = announcements_collection.insert_one(doc)
    created = announcements_collection.find_one({"_id": result.inserted_id})
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create announcement")
    return _serialize_announcement(created)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementPayload,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Update an existing announcement. Signed-in staff only."""
    _require_signed_in_user(teacher_username)
    dates = _validate_and_normalize_dates(
        expiration_date=payload.expiration_date,
        start_date=payload.start_date
    )

    try:
        object_id = ObjectId(announcement_id)
    except (InvalidId, TypeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid announcement ID") from exc

    updates = {
        "message": payload.message.strip(),
        "start_date": dates["start_date"],
        "expiration_date": dates["expiration_date"],
        "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z"
    }
    result = announcements_collection.update_one(
        {"_id": object_id},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    updated = announcements_collection.find_one({"_id": object_id})
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to load announcement")
    return _serialize_announcement(updated)


@router.delete("/{announcement_id}", response_model=Dict[str, str])
def delete_announcement(
    announcement_id: str,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, str]:
    """Delete an announcement. Signed-in staff only."""
    _require_signed_in_user(teacher_username)

    try:
        object_id = ObjectId(announcement_id)
    except (InvalidId, TypeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid announcement ID") from exc

    result = announcements_collection.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted"}
