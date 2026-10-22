import re
import math
from typing import Dict, Any, List, Optional
from modules.voice_profile.pii_scrubber import scrub_pii

# Proactive Life Event Triggers
LIFE_EVENT_PATTERNS = {
    "CROP_LOSS": {
        "regex": re.compile(r"(crop\s*loss|flood|drought|unseasonal\s*rain|अवकाळी\s*पाऊस|दुष्काळ|पीक\s*नुकसान|गारपीट)", re.IGNORECASE),
        "event_name": "Agricultural Crop Damage / Natural Calamity",
        "recommended_schemes": ["pm_fasal_bima", "pm_kisan"],
        "message": "We detected you experienced agricultural damage. You may be eligible for immediate emergency relief under PM Fasal Bima Yojana."
    },
    "HIGHER_ED_ADMISSION": {
        "regex": re.compile(r"(college|admission|10th\s*pass|12th\s*pass|engineering|diploma|वसतिगृह|कॉलेज|प्रवेश|इंजिनिअरिंग)", re.IGNORECASE),
        "event_name": "Higher Education Enrolment",
        "recommended_schemes": ["mahadbt_post_matric_obc", "mahadbt_post_matric_sc", "dr_punjabrao_hostel"],
        "message": "Student enrollment detected. You qualify for post-matric tuition waivers and hostel maintenance allowances."
    },
    "SENIOR_CITIZEN_REACHED": {
        "regex": re.compile(r"(turned\s*60|turned\s*65|senior\s*citizen|६०\s*वर्षे|६५\s*वर्षे|वृद्ध|म्हातारे|पेंशन)", re.IGNORECASE),
        "event_name": "Attained Senior Citizen Age Threshold",
        "recommended_schemes": ["shravanbal_seva", "sanjay_gandhi_niradhar"],
        "message": "Senior citizen age reached. You may claim state old-age social security pension."
    },
    "GIRL_CHILD_BORN": {
        "regex": re.compile(r"(baby\s*girl|daughter\s*born|मुलगी\s*झाली|कन्या\s*रत्न)", re.IGNORECASE),
        "event_name": "Birth of Girl Child",
        "recommended_schemes": ["sukanya_samriddhi", "majhi_kanya_bhagyashree"],
        "message": "Congratulations on the birth of a girl child! Direct financial assistance and long-term savings schemes are available."
    },
    "DISABILITY_ACQUIRED": {
        "regex": re.compile(r"(handicap|disability|divyang|दिव्यांग|अपंग)", re.IGNORECASE),
        "event_name": "Benchmark Disability Registration",
        "recommended_schemes": ["divyang_swavalamban", "sanjay_gandhi_niradhar"],
        "message": "Disability welfare provisions unlocked. You can claim monthly pension and assistive aids."
    }
}

class SlotFiller:
    """
    Extracts profile slots from vernacular speech/text and computes
    Shannon Entropy / Information Gain to determine the most informative next question.
    """
    def extract_slots_from_text(self, text: str) -> Dict[str, Any]:
        """Extracts demographic slot values from natural text."""
        slots = {}
        scrubbed = scrub_pii(text)
        clean = scrubbed["clean_text"]

        # Income extraction (e.g. 1.8 लाख, 1,80,000, 2.5 lakhs, 250000)
        income_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:लाख|lakh|lakhs)', clean, re.IGNORECASE)
        if income_match:
            slots["annual_income"] = float(income_match.group(1)) * 100000.0
        else:
            raw_num_match = re.search(r'(?:उत्पन्न|income|रु|rs\.?)\s*[:=]?\s*(\d{5,7})', clean, re.IGNORECASE)
            if raw_num_match:
                slots["annual_income"] = float(raw_num_match.group(1))

        # Landholding extraction (e.g. 2.5 एकर, 3 acres, 5 acre)
        land_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:एकर|acre|acres)', clean, re.IGNORECASE)
        if land_match:
            slots["landholding_acres"] = float(land_match.group(1))

        # Caste category
        for cat in ["OBC", "SC", "ST", "VJNT", "EWS", "SEBC", "OPEN"]:
            if re.search(rf'\b{cat}\b', clean, re.IGNORECASE):
                slots["caste_category"] = cat.upper()
                break

        # Occupation
        if re.search(r'(शेतकरी|farmer|शेती|cultivator)', clean, re.IGNORECASE):
            slots["occupation"] = "Farmer"
        elif re.search(r'(विद्यार्थी|student|कॉलेज)', clean, re.IGNORECASE):
            slots["occupation"] = "Student"
            slots["is_student"] = True
        elif re.search(r'(मजूर|labourer|daily\s*wage|कामगार)', clean, re.IGNORECASE):
            slots["occupation"] = "Daily Wage Labourer"
        elif re.search(r'(फेरीवाला|vendor|street\s*vendor)', clean, re.IGNORECASE):
            slots["occupation"] = "Street Vendor"

        # Gender
        if re.search(r'(महिला|स्त्री|female|woman)', clean, re.IGNORECASE):
            slots["gender"] = "FEMALE"
        elif re.search(r'(पुरुष|male|man)', clean, re.IGNORECASE):
            slots["gender"] = "MALE"

        # District
        districts = ["Kolhapur", "Pune", "Nashik", "Nagpur", "Chhatrapati Sambhajinagar", "Solapur", "Amravati", "Nanded", "Thane", "Satara", "Sangli"]
        for d in districts:
            if re.search(rf'\b{d}\b', clean, re.IGNORECASE):
                slots["district"] = d
                break

        return slots

    def detect_life_events(self, text: str) -> List[Dict[str, Any]]:
        """Scans citizen utterances for proactive life event triggers."""
        detected = []
        for key, config in LIFE_EVENT_PATTERNS.items():
            if config["regex"].search(text):
                detected.append({
                    "event_key": key,
                    "event_name": config["event_name"],
                    "recommended_schemes": config["recommended_schemes"],
                    "message": config["message"]
                })
        return detected

    def compute_next_best_question(self, current_profile: Dict[str, Any], all_schemes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Uses Shannon Entropy / Information Gain to determine which missing demographic
        attribute resolves the most eligibility uncertainty across all statutory schemes.
        """
        potential_slots = [
            {"slot": "annual_income", "label": "Annual Family Income", "label_mr": "वार्षिक कौटुंबिक उत्पन्न", "type": "number"},
            {"slot": "landholding_acres", "label": "Agricultural Landholding (in Acres)", "label_mr": "शेतीचे क्षेत्र (एकर मध्ये)", "type": "number"},
            {"slot": "caste_category", "label": "Social Category / Caste (e.g. OBC, SC, ST, OPEN)", "label_mr": "सामाजिक प्रवर्ग / जात (उदा. OBC, SC, ST, OPEN)", "type": "select", "options": ["OPEN", "OBC", "SC", "ST", "VJNT", "EWS", "SEBC"]},
            {"slot": "gender", "label": "Gender", "label_mr": "लिंग", "type": "select", "options": ["MALE", "FEMALE", "OTHER"]},
            {"slot": "occupation", "label": "Primary Occupation", "label_mr": "मुख्य व्यवसाय", "type": "select", "options": ["Farmer", "Student", "Daily Wage Labourer", "Street Vendor", "Other"]},
            {"slot": "age", "label": "Age", "label_mr": "वय", "type": "number"},
            {"slot": "is_student", "label": "Currently Enrolled Student", "label_mr": "सध्या विद्यार्थी आहात का?", "type": "boolean"},
            {"slot": "has_disability", "label": "Person with Benchmark Disability (Divyang)", "label_mr": "दिव्यांग व्यक्ती आहात का?", "type": "boolean"}
        ]

        # Filter out slots already known in the citizen profile
        missing = [s for s in potential_slots if current_profile.get(s["slot"]) is None]
        if not missing:
            return None

        # Calculate Information Gain score: count how many scheme ASTs depend on this slot
        def count_ast_dependencies(ast_node: Dict[str, Any], target_slot: str) -> int:
            if not isinstance(ast_node, dict):
                return 0
            count = 0
            if ast_node.get("field") == target_slot:
                count += 1
            for child in ast_node.get("children", []):
                count += count_ast_dependencies(child, target_slot)
            return count

        scored_slots = []
        for s in missing:
            dep_count = 0
            for scheme in all_schemes:
                ast = scheme.get("ast_rule", {})
                dep_count += count_ast_dependencies(ast, s["slot"])
            # Information gain proxy: proportional to frequency of constraint across policies
            info_gain = dep_count * math.log2(len(all_schemes) + 1)
            scored_slots.append((info_gain, s))

        scored_slots.sort(key=lambda x: x[0], reverse=True)
        best = scored_slots[0][1]
        best["information_gain_score"] = round(scored_slots[0][0], 2)
        return best

slot_filler = SlotFiller()
