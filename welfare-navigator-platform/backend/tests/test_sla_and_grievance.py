import pytest
from datetime import datetime, timedelta
from database.models import Application, Scheme
from modules.tracker_twin.sla_monitor import sla_monitor
from modules.tracker_twin.grievance_drafter import grievance_drafter

def test_sla_breach_detection():
    # Scheme with 30 days SLA
    scheme = Scheme(id="test_scheme", scheme_name="Solar Pump Scheme", sla_days=30)

    # App submitted 45 days before reference date 2026-10-22
    ref_dt = datetime(2026, 10, 22)
    app = Application(
        id="app_123",
        scheme_id="test_scheme",
        application_status="SUBMITTED",
        portal_tracking_id="MHA-2026-98124",
        submitted_at=ref_dt - timedelta(days=45)
    )

    metrics = sla_monitor.evaluate_application_sla(app, scheme)
    assert metrics["is_breached"] is True
    assert metrics["days_elapsed"] == 45
    assert metrics["days_overdue"] == 15
    assert metrics["statutory_penalty_applicable"] is True

def test_grievance_pdf_generation(tmp_path):
    pdf_path = grievance_drafter.draft_rts_appeal_pdf(
        citizen_name="Ramesh Shamrao Patil",
        phone_masked="[PHONE_REDACTED]",
        application_id="app_test_456",
        portal_tracking_id="MHA-2026-442819",
        scheme_name="Post-Matric Scholarship",
        department="Social Welfare Department",
        days_elapsed=52,
        sla_days=30,
        days_overdue=22,
        output_dir=str(tmp_path)
    )
    from pathlib import Path
    assert Path(pdf_path).exists()
    assert Path(pdf_path).stat().st_size > 1000
