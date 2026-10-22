import networkx as nx
from typing import List, Dict, Any, Tuple

class SchemeStacker:
    """
    Maximum Weight Independent Set (MWIS) graph optimizer.
    Finds the non-conflicting subset of eligible welfare schemes that
    maximizes total monetary benefit for an individual and family household.
    """

    def optimize_individual_stack(self, eligible_schemes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Solves MWIS over eligible schemes for an individual citizen.
        """
        if not eligible_schemes:
            return {
                "total_benefit": 0.0,
                "recommended_schemes": [],
                "conflicts_resolved": [],
                "solver": "MWIS_GRAPH_EXACT"
            }

        # Build conflict graph
        G = nx.Graph()
        scheme_map = {}

        for s in eligible_schemes:
            s_id = s["id"]
            benefit = float(s.get("benefit_amount", 0.0))
            scheme_map[s_id] = s
            G.add_node(s_id, weight=benefit, name=s.get("scheme_name", s_id))

        # Add conflict edges based on statutory mutual exclusions
        conflicts_present = []
        for s in eligible_schemes:
            s_id = s["id"]
            exclusions = s.get("mutual_exclusions", [])
            for excl_id in exclusions:
                if excl_id in scheme_map:
                    G.add_edge(s_id, excl_id)
                    conflicts_present.append((s_id, excl_id))

        # Solve Maximum Weight Independent Set
        # Because |V| <= 20 in welfare discovery, exact enumeration of maximal cliques/independent sets
        # is instant (<1ms) and guarantees mathematical optimality.
        all_independent_sets = list(nx.find_cliques(nx.complement(G)))

        best_set = []
        max_weight = -1.0

        for ind_set in all_independent_sets:
            weight = sum(G.nodes[node]["weight"] for node in ind_set)
            if weight > max_weight:
                max_weight = weight
                best_set = ind_set

        # Reconstruct explanations for excluded schemes
        conflicts_resolved = []
        for u, v in set(conflicts_present):
            u_in = u in best_set
            v_in = v in best_set
            if u_in and not v_in:
                conflicts_resolved.append(
                    f"Selected '{scheme_map[u]['scheme_name']}' (₹{scheme_map[u]['benefit_amount']:,.0f}) over '{scheme_map[v]['scheme_name']}' (₹{scheme_map[v]['benefit_amount']:,.0f}) to maximize financial support."
                )
            elif v_in and not u_in:
                conflicts_resolved.append(
                    f"Selected '{scheme_map[v]['scheme_name']}' (₹{scheme_map[v]['benefit_amount']:,.0f}) over '{scheme_map[u]['scheme_name']}' (₹{scheme_map[u]['benefit_amount']:,.0f}) to maximize financial support."
                )

        recommended = [scheme_map[node] for node in best_set]
        # Sort recommended by benefit amount descending
        recommended.sort(key=lambda x: x.get("benefit_amount", 0.0), reverse=True)

        return {
            "total_benefit": max_weight if max_weight > 0 else 0.0,
            "recommended_schemes": recommended,
            "conflicts_resolved": list(set(conflicts_resolved)),
            "total_schemes_count": len(recommended),
            "solver": "MWIS_GRAPH_EXACT"
        }

    def optimize_household_stack(self, household_members_eligibility: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregates and optimizes the combined welfare payout across an entire family household.
        household_members_eligibility: list of dicts with citizen_name, citizen_id, eligible_schemes
        """
        total_household_benefit = 0.0
        member_stacks = []

        for member in household_members_eligibility:
            eligible = member.get("eligible_schemes", [])
            stack = self.optimize_individual_stack(eligible)
            total_household_benefit += stack["total_benefit"]
            member_stacks.append({
                "citizen_id": member.get("citizen_id"),
                "citizen_name": member.get("citizen_name"),
                "individual_benefit": stack["total_benefit"],
                "recommended_schemes": stack["recommended_schemes"],
                "conflicts_resolved": stack["conflicts_resolved"]
            })

        return {
            "total_household_annual_benefit": total_household_benefit,
            "member_stacks": member_stacks,
            "household_size": len(member_stacks)
        }

scheme_stacker = SchemeStacker()
