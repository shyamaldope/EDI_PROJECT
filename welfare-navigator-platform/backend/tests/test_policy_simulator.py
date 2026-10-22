import pytest
from modules.tracker_twin.policy_simulator import policy_simulator

def test_forward_what_if_simulation(db_session):
    # Simulating PM-KISAN by raising landholding ceiling
    sim = policy_simulator.forward_simulate(
        session=db_session,
        scheme_id="pm_kisan",
        adjusted_land_ceiling=10.0
    )
    assert "baseline" in sim
    assert "scenario" in sim
    assert "impact" in sim
    assert sim["scenario"]["beneficiary_count"] >= sim["baseline"]["beneficiary_count"]

def test_inverse_goal_seek(db_session):
    # Goal-seek for target 20 beneficiaries for MahaDBT OBC Scholarship
    res = policy_simulator.inverse_goal_seek(
        session=db_session,
        scheme_id="mahadbt_post_matric_obc",
        target_beneficiaries=5
    )
    assert "recommended_income_cutoff" in res
    assert res["recommended_income_cutoff"] > 0
