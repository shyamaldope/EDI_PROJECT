from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from database.models import Citizen, Scheme, AuditLog, Notification
from modules.rule_engine.ast_evaluator import ast_evaluator

class ReverseMatcher:
    """
    Evaluates newly activated scheme AST against the entire citizen population.
    Dispatches automated proactive WhatsApp / SMS notifications for eligible individuals.
    """

    def match_and_notify(self, session: Session, scheme_id: str) -> Dict[str, Any]:
        """
        Executes batch deterministic evaluation for the scheme.
        """
        scheme = session.query(Scheme).filter(Scheme.id == scheme_id).first()
        if not scheme or scheme.status != "ACTIVE":
            return {"status": "SKIPPED", "reason": "Scheme not found or not in ACTIVE status."}

        # Query all consented citizens
        citizens = session.query(Citizen).filter(Citizen.consent_granted == True).all()

        matched_citizens = []
        now_iso = datetime.utcnow().isoformat()

        for c in citizens:
            citizen_dict = {
                "id": c.id,
                "full_name": c.full_name,
                "age": c.age,
                "gender": c.gender,
                "caste_category": c.caste_category,
                "annual_income": c.annual_income,
                "landholding_acres": c.landholding_acres,
                "occupation": c.occupation,
                "district": c.district,
                "state": c.state,
                "has_disability": c.has_disability,
                "is_student": c.is_student
            }

            passed, condition_results = ast_evaluator.evaluate(scheme.ast_rule, citizen_dict)
            if passed:
                sig = ast_evaluator.generate_audit_signature(c.id, scheme.id, "ELIGIBLE", scheme.ast_rule, now_iso)

                # 1. Create Audit Log
                audit = AuditLog(
                    citizen_id=c.id,
                    scheme_id=scheme.id,
                    action="REVERSE_MATCH_EVALUATION",
                    input_snapshot=citizen_dict,
                    rule_evaluated=scheme.ast_rule,
                    verdict="ELIGIBLE",
                    decision_signature=sig
                )
                session.add(audit)

                # 2. Queue Proactive Notification
                notif_msg = (
                    f"नमस्कार {c.full_name}, नवीन शासकीय योजना मंजूर झाली आहे: '{scheme.scheme_name}'. "
                    f"आपण या योजनेसाठी पात्र आहात! वार्षिक लाभ: ₹{scheme.benefit_amount:,.0f}."
                )
                notif = Notification(
                    citizen_id=c.id,
                    channel="WHATSAPP",
                    message=notif_msg,
                    status="SIMULATED"
                )
                session.add(notif)
                matched_citizens.append({"citizen_id": c.id, "name": c.full_name})

        session.commit()

        return {
            "scheme_id": scheme.id,
            "scheme_name": scheme.scheme_name,
            "total_citizens_evaluated": len(citizens),
            "matched_count": len(matched_citizens),
            "notifications_dispatched": len(matched_citizens),
            "matched_citizens_sample": matched_citizens[:5]
        }

reverse_matcher = ReverseMatcher()
