from typing import Dict, Any, List

class ASTDiffer:
    """
    Computes a visual Git-style structural diff between old and new scheme ASTs.
    Identifies relaxed, tightened, added, and removed policy conditions.
    """

    def diff_asts(self, old_ast: Dict[str, Any], new_ast: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates differences between two recursive AST structures.
        """
        old_leaves = self._flatten_leaves(old_ast)
        new_leaves = self._flatten_leaves(new_ast)

        added = []
        removed = []
        modified = []
        unchanged = []

        old_map = {f"{c['field']}::{c['operator']}": c for c in old_leaves}
        new_map = {f"{c['field']}::{c['operator']}": c for c in new_leaves}

        # Check for modified or unchanged conditions
        for key, old_c in old_map.items():
            if key in new_map:
                new_c = new_map[key]
                if old_c.get("value") != new_c.get("value"):
                    # Threshold modified!
                    field = old_c.get("field")
                    old_val = old_c.get("value")
                    new_val = new_c.get("value")
                    direction = "RELAXED" if new_val > old_val else "TIGHTENED"
                    modified.append({
                        "field": field,
                        "operator": old_c.get("operator"),
                        "old_value": old_val,
                        "new_value": new_val,
                        "direction": direction,
                        "description": f"{field.replace('_', ' ').title()} changed from {old_val} to {new_val} ({direction})"
                    })
                else:
                    unchanged.append(old_c)
            else:
                removed.append(old_c)

        for key, new_c in new_map.items():
            if key not in old_map:
                added.append(new_c)

        diff_summary = []
        for mod in modified:
            diff_summary.append(f"~ MODIFIED: {mod['description']}")
        for add in added:
            diff_summary.append(f"+ ADDED: {add.get('label', add.get('field'))}")
        for rem in removed:
            diff_summary.append(f"- REMOVED: {rem.get('label', rem.get('field'))}")

        return {
            "has_changes": bool(modified or added or removed),
            "modified_conditions": modified,
            "added_conditions": added,
            "removed_conditions": removed,
            "unchanged_conditions": unchanged,
            "diff_summary": diff_summary,
            "total_changes": len(modified) + len(added) + len(removed)
        }

    def _flatten_leaves(self, ast_node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recursively extracts all leaf predicates from AST tree."""
        if not ast_node:
            return []
        operator = ast_node.get("operator", "")
        if operator in ["AND", "OR", "NOT"]:
            leaves = []
            for child in ast_node.get("children", []):
                leaves.extend(self._flatten_leaves(child))
            return leaves
        else:
            return [ast_node]

ast_differ = ASTDiffer()
