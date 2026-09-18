import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from storage3.exceptions import StorageApiError
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.profile import Profile, ProfileStatus
from app.services.supabase_storage import (
    upload_resume,
    download_file,
    delete_file,
    RESUME_BUCKET,
)
from app.services.files import sanitize_filename
from app.routes.validators import validate_profile_user
from uuid import UUID
from app.core.rate_limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile_resumes", tags=["Profile Resumes"])

MAX_RESUME_SIZE_BYTES = 2 * 1024 * 1024
PDF_MAGIC_BYTES = b"%PDF-"


def resume_path(profile_id: UUID) -> str:
    return f"profiles/{profile_id}/resume.pdf"


# Upload profile resume - POST /profile_resumes/{profile_id}/resume - protected route
@router.post("/{profile_id}/resume")
@limiter.limit("5/hour")
async def upload_profile_resume(
    request: Request,
    profile_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    profile = validate_profile_user(profile_id, current_user, db)

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only PDF is allowed."
        )

    # read one byte past the cap so an oversized upload is caught without
    # ever buffering the full file into memory
    file_bytes = await file.read(MAX_RESUME_SIZE_BYTES + 1)

    if len(file_bytes) > MAX_RESUME_SIZE_BYTES:
        raise HTTPException(
            status_code=400, detail="File too large. Resumes must be 2MB or smaller."
        )

    # the client-supplied content_type is unverified input -- confirm the
    # actual bytes are a PDF rather than trusting the declared header
    if not file_bytes.startswith(PDF_MAGIC_BYTES):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only PDF is allowed."
        )

    public_url = upload_resume(
        file_bytes=file_bytes,
        path=resume_path(profile_id),
        content_type=file.content_type,
    )

    profile.resume_url = public_url
    try:
        db.commit()
        db.refresh(profile)
    except Exception:
        db.rollback()
        raise

    return {"message": "Resume uploaded successfully", "profile": profile}


# Delete profile resume - DELETE /profile_resumes/{profile_id}/resume - protected route
@router.delete("/{profile_id}/resume")
def delete_profile_resume(
    profile_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    profile = validate_profile_user(profile_id, current_user, db)

    if not profile.resume_url:
        raise HTTPException(status_code=400, detail="No resume to delete.")

    try:
        delete_file(RESUME_BUCKET, resume_path(profile_id))
    except Exception:
        # don't clear resume_url on a storage failure -- leaving it set is
        # what makes this route retryable. Clearing it here would report
        # success while orphaning the object in the bucket with no way to
        # retry the deletion (a subsequent DELETE would just 400 with
        # "No resume to delete").
        logger.exception(
            "Failed to delete resume from storage bucket=%s path=%s profile_id=%s",
            RESUME_BUCKET,
            resume_path(profile_id),
            profile_id,
        )
        raise HTTPException(
            status_code=502,
            detail="Failed to delete the stored resume. Please try again.",
        )

    profile.resume_url = None
    try:
        db.commit()
        db.refresh(profile)
    except Exception:
        db.rollback()
        raise

    return {"message": "Resume deleted successfully", "profile": profile}


# Get public profile resume - GET /profile_resumes/public/{profile_id}/resume - public route
@router.get("/public/{profile_id}/resume")
def get_public_profile_resume(profile_id: UUID, db: Session = Depends(get_db)):
    profile = (
        db.query(Profile)
        .filter(
            Profile.profile_id == profile_id,
            Profile.profile_status == ProfileStatus.active,
        )
        .first()
    )

    if not profile or not profile.resume_url:
        raise HTTPException(status_code=404, detail="Resume not found")

    try:
        file_bytes = download_file(RESUME_BUCKET, resume_path(profile_id))
    except StorageApiError as exc:
        # a real 404 from Supabase means resume_url is stale (object missing
        # from the bucket) -- that's the only case that should read as "not
        # found" to the client. Any other status (403, 500, ...) is a storage
        # problem, not a missing-file problem, and needs manual attention.
        if str(exc.status) == "404":
            raise HTTPException(status_code=404, detail="Resume not found")

        logger.exception(
            "Storage error downloading resume bucket=%s path=%s profile_id=%s",
            RESUME_BUCKET,
            resume_path(profile_id),
            profile_id,
        )
        raise HTTPException(
            status_code=502, detail="Failed to retrieve the resume. Please try again."
        )
    except Exception:
        # network-level failures (timeouts, connection errors) aren't wrapped
        # in StorageApiError by the storage client -- they're genuinely
        # transient, not evidence the file is missing, so this must not 404
        logger.exception(
            "Unexpected error downloading resume bucket=%s path=%s profile_id=%s",
            RESUME_BUCKET,
            resume_path(profile_id),
            profile_id,
        )
        raise HTTPException(
            status_code=502, detail="Failed to retrieve the resume. Please try again."
        )

    filename = f"{sanitize_filename(profile.profile_name, fallback='resume')} Resume.pdf"

    return Response(
        content=file_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
