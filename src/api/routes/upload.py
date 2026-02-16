import os
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from src.api.dependencies import get_or_create_session
from src.api.models import UploadResponse
from src.parsers import get_parser

router = APIRouter()


@router.post("/api/upload", response_model=UploadResponse)
async def upload_dive_log(
    file: UploadFile = File(...),
    session_id: str = Form(default=None),
):
    """Upload a dive log file, parse it, and store in the session."""
    filename = file.filename or "upload.ssrf"
    try:
        parser = get_parser(filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None

    # Write to temp file for parsing
    suffix = os.path.splitext(filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        df = parser.parse(tmp_path)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to parse file: {str(e)}"
        ) from None
    finally:
        os.unlink(tmp_path)

    sid, agent = get_or_create_session(session_id)
    agent.set_dive_data(df)
    dive_numbers = agent.get_dive_numbers()

    return UploadResponse(
        session_id=sid,
        dive_count=len(dive_numbers),
        dive_numbers=[str(d) for d in dive_numbers],
        message=f"Successfully parsed {len(dive_numbers)} dives from {filename}",
    )
