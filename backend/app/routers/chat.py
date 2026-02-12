from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import ChatRequest, ChatResponse
from app.services.gemini_service import (
    chat_with_gemini,
    generate_summary_stream,
    generate_report,
)
from app import models
from datetime import datetime
from typing import Optional
import json

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/conversations")
async def get_conversations(db: Session = Depends(get_db)):
    convs = (
        db.query(models.Conversation)
        .order_by(models.Conversation.created_at.desc())
        .all()
    )
    return [{"id": c.id, "title": c.title, "created_at": c.created_at} for c in convs]


@router.post("/conversations")
async def create_conversation(db: Session = Depends(get_db)):
    conv = models.Conversation(title="Nouvelle conversation")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return {"id": conv.id, "title": conv.title, "created_at": conv.created_at}


@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: int, db: Session = Depends(get_db)):
    conv = (
        db.query(models.Conversation).filter(models.Conversation.id == conv_id).first()
    )
    if conv:
        db.delete(conv)
        db.commit()
    return {"status": "deleted"}


@router.post("/{conv_id}", response_model=ChatResponse)
async def chat(conv_id: int, request: ChatRequest, db: Session = Depends(get_db)):
    conv = (
        db.query(models.Conversation).filter(models.Conversation.id == conv_id).first()
    )
    if not conv:
        conv = models.Conversation(title=request.message[:50])
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conv_id = conv.id

    if conv.title == "Nouvelle conversation":
        conv.title = request.message[:50] + ("..." if len(request.message) > 50 else "")
        db.commit()

    db.add(
        models.ChatMessage(
            conversation_id=conv_id, role="user", content=request.message
        )
    )
    db.commit()

    response = await chat_with_gemini(request.message, db)

    db.add(
        models.ChatMessage(conversation_id=conv_id, role="assistant", content=response)
    )
    db.commit()

    return ChatResponse(response=response)


@router.get("/summary/stream")
async def get_summary_stream(db: Session = Depends(get_db)):
    return StreamingResponse(
        generate_summary_stream(db),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/report")
async def get_report(
    db: Session = Depends(get_db),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    title: Optional[str] = Query(None, description="Custom report title"),
    save: bool = Query(True, description="Save report to history")
):
    """Generate APR report with optional date range and save to history"""
    
    # Parse dates
    start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    
    # Generate report
    result = await generate_report(db, start_dt, end_dt, title)
    
    # Save to history if requested
    if save and result.get("metadata"):
        report_record = models.Report(
            title=result["metadata"]["title"],
            report_type="full_apr",
            period_start=start_dt,
            period_end=end_dt,
            content=result["report"],
            metadata_json=json.dumps(result["metadata"])
        )
        db.add(report_record)
        db.commit()
        db.refresh(report_record)
        result["report_id"] = report_record.id
    
    return result


@router.get("/reports/history")
async def get_report_history(
    db: Session = Depends(get_db),
    limit: int = Query(20, description="Max number of reports to return")
):
    """Get report generation history"""
    reports = (
        db.query(models.Report)
        .order_by(models.Report.generated_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "title": r.title,
            "report_type": r.report_type,
            "period_start": r.period_start.isoformat() if r.period_start else None,
            "period_end": r.period_end.isoformat() if r.period_end else None,
            "generated_at": r.generated_at.isoformat() if r.generated_at else None,
        }
        for r in reports
    ]


@router.get("/reports/{report_id}")
async def get_saved_report(report_id: int, db: Session = Depends(get_db)):
    """Get a specific saved report"""
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {
        "id": report.id,
        "title": report.title,
        "report_type": report.report_type,
        "period_start": report.period_start.isoformat() if report.period_start else None,
        "period_end": report.period_end.isoformat() if report.period_end else None,
        "content": report.content,
        "metadata": json.loads(report.metadata_json) if report.metadata_json else None,
        "generated_at": report.generated_at.isoformat() if report.generated_at else None,
    }


@router.delete("/reports/{report_id}")
async def delete_saved_report(report_id: int, db: Session = Depends(get_db)):
    """Delete a saved report"""
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if report:
        db.delete(report)
        db.commit()
    return {"status": "deleted"}


@router.get("/{conv_id}/history")
async def get_history(conv_id: int, db: Session = Depends(get_db)):
    messages = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.conversation_id == conv_id)
        .order_by(models.ChatMessage.created_at)
        .all()
    )
    return [
        {"role": m.role, "content": m.content, "created_at": m.created_at}
        for m in messages
    ]
