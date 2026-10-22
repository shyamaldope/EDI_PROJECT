from typing import Dict, Any, List
from sqlalchemy.orm import Session
from database.models import Citizen, Scheme
from modules.rule_engine.ast_evaluator import ast_evaluator

class PolicySimulator:
    """
    Policy Digital Twin:
    1. Forward What-If Sandbox: Evaluates the budgetary and beneficiary impact of tweaking eligibility criteria.
    2. Inverse Budget Goal-Seek: Optimizes income and land cutoffs to maximize coverage within a given expenditure target.
    """

    def forward_simulate(
        self,
        session: Session,
        scheme_id: str,
        adjusted_income_ceiling: float = None,
        adjusted_land_ceiling: float = None,
        adjusted_castes: List[str] = None
    ) -> Dict[str, Any]:
        """
        Simulates how parameter tweaks alter beneficiary counts and total state budget.
        """
        scheme = session.query(Scheme).filter(Scheme.id == scheme_id).first()
        if not scheme:
            return {"error": "Scheme not found"}

        citizens = session.query(Citizen).filter(Citizen.consent_granted == True).all()

        baseline_eligible = []
        scenario_eligible = []

        # Create scenario AST clone
        import copy
        scenario_ast = copy.deepcopy(scheme.ast_rule)

        def modify_ast(node):
            if not isinstance(node, dict):
                return
            field = node.get("field")
            if field == "annual_income" and adjusted_income_ceiling is not None:
                node["value"] = adjusted_income_ceiling
            elif field == "landholding_acres" and adjusted_land_ceiling is not None and node.get("operator") in ["LESS_EQUAL", "LESS_THAN"]:
                node["value"] = adjusted_land_ceiling
            elif field == "caste_category" and adjusted_castes is not None:
                node["operator"] = "IN"
                node["value"] = adjusted_castes
            for child in node.get("children", []):
                modify_ast(child)

        modify_ast(scenario_ast)

        district_distribution = {}
        caste_distribution = {}

        for c in citizens:
            c_dict = {
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

            # Baseline check
            p_base, _ = ast_evaluator.evaluate(scheme.ast_rule, c_dict)
            if p_base:
                baseline_eligible.append(c.id)

            # Scenario check
            p_scen, _ = ast_evaluator.evaluate(scenario_ast, c_dict)
            if p_scen:
                scenario_eligible.append(c.id)
                # Track demographics
                dist = c.district or "Other"
                district_distribution[dist] = district_distribution.get(dist, 0) + 1
                caste = c.caste_category or "Other"
                caste_distribution[caste] = caste_distribution.get(caste, 0) + 1

        benefit = scheme.benefit_amount
        base_count = len(baseline_eligible)
        scen_count = len(scenario_eligible)
        net_new = scen_count - base_count

        base_budget = base_count * benefit
        scen_budget = scen_count * benefit
        net_budget = net_new * benefit

        return {
            "scheme_id": scheme.id,
            "scheme_name": scheme.scheme_name,
            "benefit_per_citizen": benefit,
            "total_population_sample": len(citizens),
            "baseline": {
                "beneficiary_count": base_count,
                "budget_required": base_budget
            },
            "scenario": {
                "beneficiary_count": scen_count,
                "budget_required": scen_budget,
                "adjusted_income_ceiling": adjusted_income_ceiling,
                "adjusted_land_ceiling": adjusted_land_ceiling,
                "adjusted_castes": adjusted_castes
            },
            "impact": {
                "net_new_beneficiaries": net_new,
                "budget_increase": net_budget,
                "percentage_expansion": round((net_new / max(1, base_count)) * 100.0, 1)
            },
            "demographic_breakdown": {
                "by_district": district_distribution,
                "by_caste": caste_distribution
            }
        }

    def inverse_goal_seek(
        self,
        session: Session,
        scheme_id: str,
        target_budget: float = None,
        target_beneficiaries: int = None
    ) -> Dict[str, Any]:
        """
        Inverse solver: Computes the optimal income cutoff to hit target budget / beneficiaries.
        """
        scheme = session.query(Scheme).filter(Scheme.id == scheme_id).first()
        if not scheme:
            return {"error": "Scheme not found"}

        benefit = scheme.benefit_amount
        if target_budget and not target_beneficiaries:
            target_beneficiaries = int(target_budget // benefit)

        # Binary search over income cutoff from ₹30,000 to ₹15,00,000
        low = 30000.0
        high = 1500000.0
        best_cutoff = low
        best_diff = float("inf")
        best_sim = None

        for _ in range(25): # Binary search 25 iterations
            mid = round((low + high) / 2.0, -3) # Round to nearest thousand
            sim = self.forward_simulate(session, scheme_id, adjusted_income_ceiling=mid)
            cur_count = sim["scenario"]["beneficiary_count"]

            diff = abs(cur_count - target_beneficiaries)
            if diff < best_diff or (diff == best_diff and sim["scenario"]["budget_required"] <= (target_budget or float("inf"))):
                best_diff = diff
                best_cutoff = mid
                best_sim = sim

            if cur_count < target_beneficiaries:
                low = mid + 1000
            else:
                high = mid - 1000

        return {
            "scheme_id": scheme.id,
            "scheme_name": scheme.scheme_name,
            "target_budget": target_budget,
            "target_beneficiaries": target_beneficiaries,
            "recommended_income_cutoff": best_cutoff,
            "resulting_beneficiaries": best_sim["scenario"]["beneficiary_count"] if best_sim else 0,
            "resulting_budget": best_sim["scenario"]["budget_required"] if best_sim else 0,
            "budget_utilization_pct": round((best_sim["scenario"]["budget_required"] / target_budget) * 100.0, 1) if target_budget and best_sim else 100.0,
            "solver": "INVERSE_BINARY_SEARCH_OPTIMIZER"
        }

policy_simulator = PolicySimulator()
