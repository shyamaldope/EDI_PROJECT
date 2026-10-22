import pytest
from modules.rule_engine.ast_evaluator import ast_evaluator

def test_ast_evaluator_and_conditions():
    ast = {
        "operator": "AND",
        "children": [
            {"field": "occupation", "operator": "EQUALS", "value": "Farmer"},
            {"field": "landholding_acres", "operator": "LESS_EQUAL", "value": 5.0},
            {"field": "annual_income", "operator": "LESS_EQUAL", "value": 250000.0}
        ]
    }
    # Passing citizen
    c_pass = {"occupation": "Farmer", "landholding_acres": 2.5, "annual_income": 180000.0}
    passed, results = ast_evaluator.evaluate(ast, c_pass)
    assert passed is True
    assert len(results) == 3
    assert all(r["passed"] for r in results)

    # Failing citizen (exceeds land)
    c_fail = {"occupation": "Farmer", "landholding_acres": 6.2, "annual_income": 180000.0}
    passed, results = ast_evaluator.evaluate(ast, c_fail)
    assert passed is False
    assert results[1]["passed"] is False

def test_ast_evaluator_or_and_in_conditions():
    ast = {
        "operator": "AND",
        "children": [
            {"field": "caste_category", "operator": "IN", "value": ["OBC", "SC", "ST"]},
            {
                "operator": "OR",
                "children": [
                    {"field": "is_student", "operator": "EQUALS", "value": True},
                    {"field": "has_disability", "operator": "EQUALS", "value": True}
                ]
            }
        ]
    }
    # OBC Student
    c1 = {"caste_category": "OBC", "is_student": True, "has_disability": False}
    p1, _ = ast_evaluator.evaluate(ast, c1)
    assert p1 is True

    # OPEN Category Student (Fails caste)
    c2 = {"caste_category": "OPEN", "is_student": True, "has_disability": False}
    p2, _ = ast_evaluator.evaluate(ast, c2)
    assert p2 is False

def test_ast_audit_signature_reproducibility():
    ast = {"field": "annual_income", "operator": "LESS_EQUAL", "value": 250000.0}
    sig1 = ast_evaluator.generate_audit_signature("c1", "scheme_a", "ELIGIBLE", ast, "2026-10-22T08:00:00Z")
    sig2 = ast_evaluator.generate_audit_signature("c1", "scheme_a", "ELIGIBLE", ast, "2026-10-22T08:00:00Z")
    sig3 = ast_evaluator.generate_audit_signature("c1", "scheme_a", "INELIGIBLE", ast, "2026-10-22T08:00:00Z")

    assert sig1 == sig2
    assert sig1 != sig3
    assert len(sig1) == 64
