import pytest
from modules.rule_engine.scheme_stacker import scheme_stacker

def test_mwis_mutual_exclusion_resolution():
    # Scheme A (benefit 65,000) mutually exclusive with Scheme B (benefit 35,000)
    # Scheme C (benefit 10,000) non-exclusive
    eligible = [
        {
            "id": "scheme_sc",
            "scheme_name": "SC Post-Matric Scholarship",
            "benefit_amount": 65000.0,
            "mutual_exclusions": ["scheme_obc"]
        },
        {
            "id": "scheme_obc",
            "scheme_name": "OBC Post-Matric Scholarship",
            "benefit_amount": 35000.0,
            "mutual_exclusions": ["scheme_sc"]
        },
        {
            "id": "scheme_kisan",
            "scheme_name": "PM-KISAN Samman Nidhi",
            "benefit_amount": 6000.0,
            "mutual_exclusions": []
        }
    ]

    opt = scheme_stacker.optimize_individual_stack(eligible)

    # Optimal should pick Scheme SC (65,000) + PM-KISAN (6,000) = 71,000
    assert opt["total_benefit"] == 71000.0
    rec_ids = [s["id"] for s in opt["recommended_schemes"]]
    assert "scheme_sc" in rec_ids
    assert "scheme_kisan" in rec_ids
    assert "scheme_obc" not in rec_ids
    assert len(opt["conflicts_resolved"]) > 0

def test_mwis_household_aggregation():
    members = [
        {
            "citizen_id": "c1",
            "citizen_name": "Ramesh Patil",
            "eligible_schemes": [
                {"id": "pm_kisan", "scheme_name": "PM-KISAN", "benefit_amount": 6000.0, "mutual_exclusions": []},
                {"id": "namo_shetkari", "scheme_name": "Namo Shetkari", "benefit_amount": 6000.0, "mutual_exclusions": []}
            ]
        },
        {
            "citizen_id": "c2",
            "citizen_name": "Aditya Patil",
            "eligible_schemes": [
                {"id": "scholarship", "scheme_name": "OBC Scholarship", "benefit_amount": 35000.0, "mutual_exclusions": []}
            ]
        }
    ]

    hh_opt = scheme_stacker.optimize_household_stack(members)
    assert hh_opt["total_household_annual_benefit"] == 47000.0
    assert hh_opt["household_size"] == 2
