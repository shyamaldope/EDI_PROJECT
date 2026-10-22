import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["reference_date"] == "2026-10-22"

def test_get_citizens():
    res = client.get("/api/v1/citizens")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 50
    # Ramesh Patil check
    names = [c["full_name"] for c in data]
    assert "Ramesh Shamrao Patil" in names

def test_get_schemes():
    res = client.get("/api/v1/schemes")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 20

def test_citizen_eligibility_and_mwis_stack():
    # Test Ramesh Patil
    res = client.get("/api/v1/citizens/c-patil-ramesh-001/schemes")
    assert res.status_code == 200
    data = res.json()
    assert "eligible_schemes" in data
    assert "optimal_benefit_stack" in data
    # Ramesh is farmer with 2.5 acres, income 1.8L -> Should be eligible for PM-KISAN and Namo Shetkari
    el_ids = [s["id"] for s in data["eligible_schemes"]]
    assert "pm_kisan" in el_ids
    assert "namo_shetkari" in el_ids
    assert data["optimal_benefit_stack"]["total_benefit"] >= 12000.0

def test_vault_purge_endpoint():
    # Create temporary citizen to test 1-click purge
    create_res = client.post("/api/v1/citizens", json={
        "id": "c-temp-purge-test",
        "full_name": "Temporary Citizen To Purge",
        "phone": "9820099887",
        "ration_card_number": "RC-TEMP-1234",
        "annual_income": 120000.0,
        "consent_granted": True
    })
    assert create_res.status_code == 200

    # Purge
    purge_res = client.delete("/api/v1/citizens/c-temp-purge-test/purge")
    assert purge_res.status_code == 200
    pdata = purge_res.json()
    assert pdata["status"] == "PURGED"
    assert "purge_receipt_hash" in pdata

    # Verify citizen no longer exists
    get_res = client.get("/api/v1/citizens/c-temp-purge-test")
    assert get_res.status_code == 404
