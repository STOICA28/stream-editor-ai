from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.project import TimelineEvent, TranscriptSegment, TranscriptWord, Scene, TranscriptRun, Project
from ..schemas.analysis import TimelineEventResponse, TranscriptSegmentResponse, SceneResponse, TranscriptWordResponse

router = APIRouter(prefix="/projects/{project_id}", tags=["analysis"])

@router.get("/timeline", response_model=List[TimelineEventResponse])
def get_timeline(project_id: str, db: Session = Depends(get_db)):
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    events = (
        db.query(TimelineEvent)
        .filter(TimelineEvent.project_id == project_id)
        .order_by(TimelineEvent.start_time.asc())
        .all()
    )
    return events

@router.get("/transcripts", response_model=List[TranscriptSegmentResponse])
def get_transcripts(project_id: str, db: Session = Depends(get_db)):
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Find the transcript run for this project
    # Assuming the most recent or completed run
    run = (
        db.query(TranscriptRun)
        .filter(TranscriptRun.project_id == project_id)
        .order_by(TranscriptRun.created_at.desc())
        .first()
    )
    
    if not run:
        return []

    segments = (
        db.query(TranscriptSegment)
        .filter(TranscriptSegment.transcript_run_id == run.id)
        .order_by(TranscriptSegment.start_time.asc())
        .all()
    )

    if not segments:
        return []

    segment_ids = [seg.id for seg in segments]
    words = (
        db.query(TranscriptWord)
        .filter(TranscriptWord.segment_id.in_(segment_ids))
        .order_by(TranscriptWord.start_time.asc())
        .all()
    )

    words_by_segment = {}
    for w in words:
        words_by_segment.setdefault(w.segment_id, []).append(w)

    response = []
    for seg in segments:
        seg_dict = {
            "id": seg.id,
            "start_time": seg.start_time,
            "end_time": seg.end_time,
            "text": seg.text,
            "speaker": seg.speaker,
            "confidence": seg.confidence,
            "sequence": seg.sequence,
            "words": words_by_segment.get(seg.id, [])
        }
        response.append(seg_dict)

    return response

@router.get("/scenes", response_model=List[SceneResponse])
def get_scenes(project_id: str, db: Session = Depends(get_db)):
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    scenes = (
        db.query(Scene)
        .filter(Scene.project_id == project_id)
        .order_by(Scene.start_time.asc())
        .all()
    )
    return scenes
