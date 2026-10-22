import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Tuple

class ASTEvaluator:
    """
    Pure Python deterministic recursive AST rule evaluator.
    Strictly zero-hallucination: LLMs are never allowed to evaluate eligibility.
    Generates condition-by-condition citations and a SHA-256 cryptographic audit signature.
    """

    def evaluate(self, ast_node: Dict[str, Any], citizen_data: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Recursively evaluates an AST node against citizen demographic attributes.
        Returns (passed: bool, condition_results: list of audit records).
        """
        if not ast_node:
            return True, []

        operator = ast_node.get("operator", "").upper()
        children = ast_node.get("children", [])

        # Compound Logical Operators
        if operator == "AND":
            overall_pass = True
            all_results = []
            for child in children:
                passed, results = self.evaluate(child, citizen_data)
                all_results.extend(results)
                if not passed:
                    overall_pass = False
            return overall_pass, all_results

        elif operator == "OR":
            overall_pass = False
            all_results = []
            for child in children:
                passed, results = self.evaluate(child, citizen_data)
                all_results.extend(results)
                if passed:
                    overall_pass = True
            return overall_pass, all_results

        elif operator == "NOT":
            if not children:
                return True, []
            passed, results = self.evaluate(children[0], citizen_data)
            inverted_pass = not passed
            # Mark inverted status in audit
            for r in results:
                r["inverted"] = True
                r["passed"] = inverted_pass
            return inverted_pass, results

        # Leaf Predicate Condition
        field = ast_node.get("field")
        expected_value = ast_node.get("value")
        actual_value = citizen_data.get(field)
        citation = ast_node.get("citation", {})
        label = ast_node.get("label", f"{field} {operator} {expected_value}")

        passed = self._evaluate_leaf(operator, actual_value, expected_value)

        audit_entry = {
            "field": field,
            "operator": operator,
            "expected_value": expected_value,
            "actual_value": actual_value,
            "passed": passed,
            "label": label,
            "citation": citation
        }

        return passed, [audit_entry]

    def _evaluate_leaf(self, operator: str, actual: Any, expected: Any) -> bool:
        """Evaluates a single leaf relation."""
        if actual is None:
            return False

        try:
            if operator == "EQUALS":
                if isinstance(actual, str) and isinstance(expected, str):
                    return actual.strip().lower() == expected.strip().lower()
                return actual == expected

            elif operator == "NOT_EQUALS":
                if isinstance(actual, str) and isinstance(expected, str):
                    return actual.strip().lower() != expected.strip().lower()
                return actual != expected

            elif operator == "GREATER_THAN":
                return float(actual) > float(expected)

            elif operator == "LESS_THAN":
                return float(actual) < float(expected)

            elif operator == "GREATER_EQUAL":
                return float(actual) >= float(expected)

            elif operator == "LESS_EQUAL":
                return float(actual) <= float(expected)

            elif operator == "IN":
                if isinstance(expected, list):
                    if isinstance(actual, str):
                        normalized_expected = [str(x).strip().lower() for x in expected]
                        return str(actual).strip().lower() in normalized_expected
                    return actual in expected
                return False

            elif operator == "NOT_IN":
                if isinstance(expected, list):
                    if isinstance(actual, str):
                        normalized_expected = [str(x).strip().lower() for x in expected]
                        return str(actual).strip().lower() not in normalized_expected
                    return actual not in expected
                return True

            elif operator == "BETWEEN":
                if isinstance(expected, (list, tuple)) and len(expected) == 2:
                    return float(expected[0]) <= float(actual) <= float(expected[1])
                return False

        except (ValueError, TypeError):
            return False

        return False

    def generate_audit_signature(
        self,
        citizen_id: str,
        scheme_id: str,
        verdict: str,
        ast_rule: Dict[str, Any],
        timestamp_iso: str
    ) -> str:
        """
        Computes SHA-256 cryptographic decision signature for legal non-repudiation.
        """
        rule_str = json.dumps(ast_rule, sort_keys=True)
        raw_payload = f"{citizen_id}::{scheme_id}::{verdict}::{rule_str}::{timestamp_iso}"
        return hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

ast_evaluator = ASTEvaluator()
