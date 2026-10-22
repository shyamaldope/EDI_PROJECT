from typing import Dict, Any, List, Tuple

class NearMissAnalyzer:
    """
    Analyzes ineligible scheme evaluations to identify 'Near Misses' (75%–99% match).
    Calculates proximity scores and synthesizes actionable citizen remediation pathways.
    """

    def analyze(
        self,
        scheme: Dict[str, Any],
        condition_results: List[Dict[str, Any]],
        citizen_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates condition results, computes weighted match percentage,
        and generates remediation recommendations.
        """
        if not condition_results:
            return {"is_near_miss": False, "match_percentage": 0.0, "remediations": []}

        total_conditions = len(condition_results)
        passed_count = sum(1 for c in condition_results if c.get("passed"))

        if passed_count == total_conditions:
            return {
                "is_near_miss": False,
                "match_percentage": 100.0,
                "remediations": []
            }

        # Calculate proximity score for failed numeric conditions
        partial_credits = 0.0
        remediations = []

        for cond in condition_results:
            if cond.get("passed"):
                continue

            field = cond.get("field")
            expected = cond.get("expected_value")
            actual = cond.get("actual_value")
            operator = cond.get("operator")

            # Check numeric proximity
            if operator in ["LESS_EQUAL", "LESS_THAN"] and isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
                if expected > 0:
                    diff_pct = (actual - expected) / expected
                    if diff_pct <= 0.20: # Within 20% of limit
                        credit = max(0.0, 1.0 - (diff_pct * 3.0))
                        partial_credits += credit
                        remediations.append({
                            "field": field,
                            "type": "THRESHOLD_PROXIMITY",
                            "severity": "LOW" if diff_pct <= 0.08 else "MEDIUM",
                            "message": f"Your {field.replace('_', ' ')} is ₹{actual:,.0f}, which is within {diff_pct*100:.1f}% of the statutory threshold ₹{expected:,.0f}.",
                            "action": f"Verify whether recent agricultural write-offs or deductions apply, or consult your local Talathi."
                        })
                    else:
                        remediations.append({
                            "field": field,
                            "type": "THRESHOLD_EXCEEDED",
                            "severity": "HIGH",
                            "message": f"{field.replace('_', ' ').title()} exceeds statutory ceiling (Current: {actual}, Limit: {expected}).",
                            "action": "Scheme criteria require lower ceiling."
                        })

            elif operator in ["GREATER_EQUAL", "GREATER_THAN"] and isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
                if expected > 0:
                    diff_pct = (expected - actual) / expected
                    if diff_pct <= 0.20:
                        credit = max(0.0, 1.0 - (diff_pct * 3.0))
                        partial_credits += credit
                        remediations.append({
                            "field": field,
                            "type": "THRESHOLD_PROXIMITY",
                            "severity": "LOW",
                            "message": f"{field.replace('_', ' ').title()} is {actual}, just below required {expected}.",
                            "action": "Ensure all operational land or age records are up-to-date."
                        })

            elif operator == "IN" and field == "caste_category":
                remediations.append({
                    "field": field,
                    "type": "CATEGORY_MISMATCH",
                    "severity": "HIGH",
                    "message": f"Caste category '{actual}' does not match required categories ({', '.join(expected)}).",
                    "action": "Verify if you hold an SEBC, EWS, or VJNT non-creamy layer certificate."
                })

            elif field == "is_student":
                remediations.append({
                    "field": field,
                    "type": "ENROLLMENT_REQUIRED",
                    "severity": "MEDIUM",
                    "message": "Scheme is reserved for actively enrolled students.",
                    "action": "Upload your current college bonafide or admission receipt once enrolled."
                })
            else:
                remediations.append({
                    "field": field,
                    "type": "CRITERIA_UNMET",
                    "severity": "MEDIUM",
                    "message": f"Condition failed: {cond.get('label')}",
                    "action": "Review eligibility document checklist."
                })

        # Final Weighted Match Percentage
        effective_passes = passed_count + partial_credits
        match_percentage = round((effective_passes / total_conditions) * 100.0, 1)

        is_near_miss = 75.0 <= match_percentage < 100.0

        return {
            "is_near_miss": is_near_miss,
            "match_percentage": match_percentage,
            "remediations": remediations
        }

near_miss_analyzer = NearMissAnalyzer()
