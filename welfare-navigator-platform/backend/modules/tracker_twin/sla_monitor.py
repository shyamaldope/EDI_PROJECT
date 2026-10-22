from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from database.models import Application, Scheme, Citizen
from config import settings

class SLAMonitor:
    """
    Monitors statutory service delivery SLAs under the Maharashtra Right to Public Services Act, 2015.
    Flags applications where days_elapsed exceeds scheme.sla_days as BREACHED.
    """

    def evaluate_application_sla(self, application: Application, scheme: Scheme) -> Dict[str, Any]:
        """
        Evaluates SLA timeline metrics for an individual application.
        """
        ref_dt = datetime.strptime(settings.REFERENCE_DATE, "%Y-%m-%d")
        submitted_dt = application.submitted_at or ref_dt

        days_elapsed = (ref_dt - submitted_dt).days
        sla_limit_days = scheme.sla_days if scheme else 30
        is_breached = days_elapsed > sla_limit_days and application.application_status not in ["APPROVED", "REJECTED"]

        days_overdue = max(0, days_elapsed - sla_limit_days)
        progress_pct = min(100.0, round((days_elapsed / sla_limit_days) * 100.0, 1))

        status = application.application_status
        if is_breached:
            status = "BREACHED"

        return {
            "application_id": application.id,
            "portal_tracking_id": application.portal_tracking_id,
            "scheme_name": scheme.scheme_name if scheme else "Unknown Scheme",
            "department": scheme.department if scheme else "General Administration",
            "submitted_at": submitted_dt.strftime("%Y-%m-%d"),
            "reference_date": settings.REFERENCE_DATE,
            "days_elapsed": days_elapsed,
            "sla_limit_days": sla_limit_days,
            "days_overdue": days_overdue,
            "progress_percentage": progress_pct,
            "is_breached": is_breached,
            "status": status,
            "statutory_penalty_applicable": is_breached,
            "rts_appeal_ready": is_breached
        }

    def get_all_breaches(self, session: Session) -> List[Dict[str, Any]]:
        """
        Returns all applications across the platform currently in breach of statutory SLA.
        """
        apps = session.query(Application).all()
        breaches = []
        for app in apps:
            scheme = session.query(Scheme).filter(Scheme.id == app.scheme_id).first()
            metrics = self.evaluate_application_sla(app, scheme)
            if metrics["is_breached"]:
                citizen = session.query(Citizen).filter(Citizen.id == app.citizen_id).first()
                metrics["citizen_name"] = citizen.full_name if citizen else "Unknown Citizen"
                metrics["district"] = citizen.district if citizen else "Unknown District"
                breaches.append(metrics)
        return breaches

sla_monitor = SLAMonitor()
