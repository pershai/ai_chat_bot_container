from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.services import ingestion_service

router = APIRouter(tags=["upload"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = await ingestion_service.ingest_pdf(file, current_user.id, db)
    if "Error" in result:
        raise HTTPException(status_code=500, detail=result)
    return {"message": result}
