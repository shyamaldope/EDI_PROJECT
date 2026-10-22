import json
import os
import sys
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from config import settings
from database.connection import init_sync_db, SyncSessionLocal
from database.models import Citizen, Scheme, Application, AuditLog, Notification

def compute_hash(value: str, salt: str = settings.SECRET_SALT) -> str:
    return hashlib.sha256(f"{value}_{salt}".encode("utf-8")).hexdigest()

def seed_database():
    print("Initializing database tables...")
    init_sync_db()

    session = SyncSessionLocal()
    try:
        # 1. Seed Schemes
        schemes_json_path = backend_dir / "database" / "seed_schemes.json"
        with open(schemes_json_path, "r", encoding="utf-8") as f:
            schemes_data = json.load(f)

        print(f"Seeding {len(schemes_data)} schemes...")
        for s in schemes_data:
            existing = session.query(Scheme).filter(Scheme.id == s["id"]).first()
            if not existing:
                scheme = Scheme(
                    id=s["id"],
                    scheme_code=s["scheme_code"],
                    scheme_name=s["scheme_name"],
                    scheme_name_mr=s.get("scheme_name_mr"),
                    department=s["department"],
                    target_beneficiary=s["target_beneficiary"],
                    benefit_amount=s["benefit_amount"],
                    benefit_type=s["benefit_type"],
                    sla_days=s.get("sla_days", 30),
                    status=s.get("status", "ACTIVE"),
                    version=s.get("version", 1),
                    dom_mapping_key=s.get("dom_mapping_key"),
                    mutual_exclusions=s.get("mutual_exclusions", []),
                    citations=s.get("citations", []),
                    ast_rule=s["ast_rule"]
                )
                session.add(scheme)
        session.commit()
        print("Schemes seeded successfully.")

        # 2. Seed 15 Households with 50 Synthetic Citizens
        # Ensure our primary demo citizen Ramesh Shamrao Patil is present!
        existing_citizen = session.query(Citizen).filter(Citizen.full_name == "Ramesh Shamrao Patil").first()
        if not existing_citizen:
            print("Seeding 50 synthetic citizens across 15 households...")

            districts = ["Kolhapur", "Pune", "Nashik", "Nagpur", "Chhatrapati Sambhajinagar", "Solapur", "Amravati", "Nanded"]
            castes = ["OBC", "OPEN", "SC", "ST", "VJNT", "EWS", "SEBC"]

            # Household 1: Patil Family (Kolhapur) - Primary Demo Persona
            h1_ration = "RC-MAHA-KOL-00101"
            h1_id = compute_hash(h1_ration)

            c1 = Citizen(
                id="c-patil-ramesh-001",
                full_name="Ramesh Shamrao Patil",
                phone_hash=compute_hash("9820012345"),
                household_id=h1_id,
                dob="1978-05-15",
                age=48,
                gender="MALE",
                caste_category="OBC",
                annual_income=180000.0,
                landholding_acres=2.5,
                occupation="Farmer",
                district="Kolhapur",
                state="Maharashtra",
                has_disability=False,
                is_student=False,
                education_level="Secondary",
                consent_granted=True,
                consent_timestamp="2026-10-22T08:00:00Z"
            )
            session.add(c1)

            c2 = Citizen(
                id="c-patil-sunita-002",
                full_name="Sunita Ramesh Patil",
                phone_hash=compute_hash("9820012346"),
                household_id=h1_id,
                dob="1982-08-20",
                age=44,
                gender="FEMALE",
                caste_category="OBC",
                annual_income=180000.0,
                landholding_acres=0.0,
                occupation="Homemaker",
                district="Kolhapur",
                state="Maharashtra",
                has_disability=False,
                is_student=False,
                education_level="Primary",
                consent_granted=True,
                consent_timestamp="2026-10-22T08:00:00Z"
            )
            session.add(c2)

            c3 = Citizen(
                id="c-patil-aditya-003",
                full_name="Aditya Ramesh Patil",
                phone_hash=compute_hash("9820012347"),
                household_id=h1_id,
                dob="2006-03-10",
                age=20,
                gender="MALE",
                caste_category="OBC",
                annual_income=180000.0,
                landholding_acres=0.0,
                occupation="Student",
                district="Kolhapur",
                state="Maharashtra",
                has_disability=False,
                is_student=True,
                education_level="Undergraduate Engineering",
                consent_granted=True,
                consent_timestamp="2026-10-22T08:00:00Z"
            )
            session.add(c3)

            # Generate remaining 47 synthetic citizens
            first_names_m = ["Sanjay", "Anil", "Ganesh", "Vijay", "Prakash", "Sachin", "Dattatray", "Santosh", "Deepak", "Mahesh"]
            first_names_f = ["Anita", "Shobha", "Mangal", "Rekha", "Usha", "Kavita", "Pooja", "Vaishali", "Snehal", "Priyanka"]
            last_names = ["Shinde", "Jadhav", "More", "Kadam", "Pawar", "Chavan", "Gaekwad", "Bhosale", "Deshmukh", "Kale"]

            citizen_counter = 4
            for h_idx in range(2, 20):
                if citizen_counter > 55:
                    break
                h_ration = f"RC-MAHA-DIST-{h_idx:05d}"
                current_hid = compute_hash(h_ration)
                district = districts[h_idx % len(districts)]
                caste = castes[h_idx % len(castes)]
                family_income = float(30000 + (h_idx * 25000))
                family_land = float(max(0.0, round((h_idx % 5) * 1.2, 1)))

                # Head of house
                fn_m = first_names_m[h_idx % len(first_names_m)]
                ln = last_names[h_idx % len(last_names)]
                age_m = 35 + (h_idx * 2) % 35
                c_head = Citizen(
                    id=f"c-synth-{citizen_counter:03d}",
                    full_name=f"{fn_m} {ln}",
                    phone_hash=compute_hash(f"98210{citizen_counter:05d}"),
                    household_id=current_hid,
                    dob=f"{2026 - age_m}-04-12",
                    age=age_m,
                    gender="MALE",
                    caste_category=caste,
                    annual_income=family_income,
                    landholding_acres=family_land,
                    occupation="Farmer" if family_land > 0 else "Daily Wage Labourer",
                    district=district,
                    state="Maharashtra",
                    has_disability=(h_idx == 7),
                    is_student=False,
                    education_level="Secondary",
                    consent_granted=True,
                    consent_timestamp="2026-10-22T08:00:00Z"
                )
                session.add(c_head)
                citizen_counter += 1

                # Spouse
                fn_f = first_names_f[h_idx % len(first_names_f)]
                age_f = age_m - 3
                c_spouse = Citizen(
                    id=f"c-synth-{citizen_counter:03d}",
                    full_name=f"{fn_f} {fn_m} {ln}",
                    phone_hash=compute_hash(f"98210{citizen_counter:05d}"),
                    household_id=current_hid,
                    dob=f"{2026 - age_f}-07-18",
                    age=age_f,
                    gender="FEMALE",
                    caste_category=caste,
                    annual_income=family_income,
                    landholding_acres=0.0,
                    occupation="Homemaker",
                    district=district,
                    state="Maharashtra",
                    has_disability=False,
                    is_student=False,
                    education_level="Primary",
                    consent_granted=True,
                    consent_timestamp="2026-10-22T08:00:00Z"
                )
                session.add(c_spouse)
                citizen_counter += 1

                # Dependent / Child
                if citizen_counter <= 50:
                    age_c = max(8, 20 - (h_idx % 12))
                    c_child = Citizen(
                        id=f"c-synth-{citizen_counter:03d}",
                        full_name=f"Rahul {fn_m} {ln}" if h_idx % 2 == 0 else f"Neha {fn_m} {ln}",
                        phone_hash=compute_hash(f"98210{citizen_counter:05d}"),
                        household_id=current_hid,
                        dob=f"{2026 - age_c}-11-05",
                        age=age_c,
                        gender="MALE" if h_idx % 2 == 0 else "FEMALE",
                        caste_category=caste,
                        annual_income=family_income,
                        landholding_acres=0.0,
                        occupation="Student",
                        district=district,
                        state="Maharashtra",
                        has_disability=False,
                        is_student=(age_c >= 16),
                        education_level="Higher Secondary" if age_c >= 16 else "School",
                        consent_granted=True,
                        consent_timestamp="2026-10-22T08:00:00Z"
                    )
                    session.add(c_child)
                    citizen_counter += 1

            session.commit()
            print(f"50 Citizens seeded successfully.")

            # 3. Seed Sample Applications (including an active SLA Breach for Grievance testing!)
            now = datetime(2026, 10, 22, 8, 30, 0)

            # Application 1: Ramesh Patil - PM-KISAN (Submitted 10 days ago, Within SLA)
            app1 = Application(
                id="app-patil-pmkisan-001",
                citizen_id=c1.id,
                scheme_id="pm_kisan",
                application_status="SUBMITTED",
                portal_tracking_id="PMK-2026-981245",
                submitted_at=now - timedelta(days=10),
                sla_deadline=now + timedelta(days=20),
                days_elapsed=10,
                grievance_filed=False,
                audit_hash="d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592"
            )
            session.add(app1)

            # Application 2: Aditya Patil - MahaDBT Scholarship (Submitted 52 days ago, SLA 45 days -> BREACHED!)
            app2 = Application(
                id="app-patil-scholarship-002",
                citizen_id=c3.id,
                scheme_id="mahadbt_post_matric_obc",
                application_status="BREACHED",
                portal_tracking_id="MHA-2026-442819",
                submitted_at=now - timedelta(days=52),
                sla_deadline=now - timedelta(days=7),
                days_elapsed=52,
                grievance_filed=False,
                audit_hash="a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f7a9b1c3d5e7f9a1b3c5d7e9f1a3b5"
            )
            session.add(app2)

            session.commit()
            print("Sample applications seeded successfully.")

    except Exception as e:
        session.rollback()
        print(f"Error during seeding: {e}")
        raise e
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
