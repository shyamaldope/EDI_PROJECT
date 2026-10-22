import os
from celery import Celery
from config import settings

celery = Celery(
    "welfare_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True
)

@celery.task(name="tasks.reverse_match_scheme")
def celery_reverse_match(scheme_id: str):
    """Celery task for reverse matching"""
    from database.connection import get_sync_db
    from modules.ingestion.reverse_matcher import reverse_matcher
    with get_sync_db() as session:
        return reverse_matcher.match_and_notify(session, scheme_id)

@celery.task(name="tasks.compress_document")
def celery_compress_document(input_path: str, output_path: str):
    """Celery task for background media compression"""
    from modules.doc_auditor.media_compressor import media_compressor
    return media_compressor.compress_for_portal(input_path, output_path)
