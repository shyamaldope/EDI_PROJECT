import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

artifacts_dir = Path(__file__).resolve().parent

def generate_pdf_gr():
    pdf_path = artifacts_dir / "Artifact_A_Maharashtra_GR_2026.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'GRTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        alignment=1, # Center
        textColor=colors.HexColor('#1a365d')
    )

    header_style = ParagraphStyle(
        'GRHeader',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=1
    )

    body_style = ParagraphStyle(
        'GRBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#2d3748')
    )

    bold_body = ParagraphStyle(
        'GRBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    story = []

    # Header
    story.append(Paragraph("GOVERNMENT OF MAHARASHTRA", title_style))
    story.append(Paragraph("Agriculture, Animal Husbandry, Dairy Development and Fisheries Department", header_style))
    story.append(Paragraph("Government Resolution No.: NSM-2026/CR-88/11-A", bold_body))
    story.append(Paragraph("Mantralaya, Madam Cama Road, Hutatma Rajguru Chowk, Mumbai 400 032", header_style))
    story.append(Paragraph("Date: 15th January 2026", bold_body))
    story.append(Spacer(1, 15))

    # Title
    story.append(Paragraph("SUBJECT: Implementation of Maha Krishi Urja & Samruddhi Yojana 2026 for Marginal Farmers in Maharashtra", title_style))
    story.append(Spacer(1, 15))

    # Preamble
    story.append(Paragraph("<b>PREAMBLE:</b> In order to ensure comprehensive solar energy and direct agricultural income security for small cultivators in Maharashtra, the State Government hereby sanctions the 'Maha Krishi Urja & Samruddhi Yojana 2026'.", body_style))
    story.append(Spacer(1, 10))

    # Paragraph 1
    story.append(Paragraph("<b>1. SCOPE AND JURISDICTION:</b> The scheme shall apply across all 36 districts of Maharashtra with effect from financial year 2026-27.", body_style))
    story.append(Spacer(1, 8))

    # Paragraph 2: Eligibility Criteria (Citations)
    story.append(Paragraph("<b>2. STATUTORY ELIGIBILITY CRITERIA (Para 2.1 - Citations):</b>", bold_body))
    story.append(Paragraph("<b>(a) Occupation:</b> The beneficiary must be an active farmer cultivating agricultural land. (Citation: Page 1, Para 2.1)", body_style))
    story.append(Paragraph("<b>(b) Landholding:</b> The beneficiary must possess operational landholding of greater than 0.0 acres and not exceeding 5.0 acres as per Revenue 7/12 record. (Citation: Page 1, Para 2.2)", body_style))
    story.append(Paragraph("<b>(c) Annual Family Income:</b> The total annual family income from all sources must not exceed Rs. 2,50,000 (Two Lakh Fifty Thousand Rupees). (Citation: Page 2, Para 4.1)", body_style))
    story.append(Paragraph("<b>(d) Domicile:</b> The applicant must be a resident of the State of Maharashtra. (Citation: Page 2, Para 4.2)", body_style))
    story.append(Spacer(1, 10))

    # Paragraph 3: Financial Benefit
    story.append(Paragraph("<b>3. FINANCIAL ASSISTANCE & SUBSIDY:</b> Eligible beneficiaries shall be granted Rs. 45,000 one-time solar pump subsidy and an annual direct benefit transfer of Rs. 6,000. (Citation: Page 2, Para 5)", body_style))
    story.append(Spacer(1, 10))

    # Paragraph 4: Statutory Service SLA
    story.append(Paragraph("<b>4. RIGHT TO SERVICES (RTS) ACT SLA:</b> Under the Maharashtra Right to Public Services Act 2015, the Designated Officer shall verify and issue approval/disbursement within <b>30 working days</b> from online receipt. Failure to adhere shall attract statutory appellate grievance.", body_style))
    story.append(Spacer(1, 15))

    # Signoff
    story.append(Paragraph("By order and in the name of the Governor of Maharashtra,", body_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>(Dr. V. K. Patil)</b><br/>Joint Secretary to Government of Maharashtra", body_style))

    doc.build(story)
    print(f"Generated: {pdf_path}")

def generate_identity_card():
    img_path = artifacts_dir / "Artifact_B1_IdentityCard_Ramesh_Shamrao_Patil.jpg"
    w, h = 600, 380
    img = Image.new("RGB", (w, h), color="#f7fafc")
    draw = ImageDraw.Draw(img)

    # Header bar
    draw.rectangle([(0, 0), (w, 50)], fill="#1a365d")
    draw.rectangle([(0, 50), (w, 55)], fill="#dd6b20") # saffron accent

    # Border
    draw.rectangle([(1, 1), (w-2, h-2)], outline="#cbd5e0", width=2)

    # Photo box
    draw.rectangle([(40, 80), (160, 220)], fill="#e2e8f0", outline="#a0aec0", width=2)
    draw.ellipse([(70, 100), (130, 160)], fill="#cbd5e0")
    draw.chord([(50, 160), (150, 230)], 180, 360, fill="#a0aec0")

    # Text
    draw.text((190, 15), "GOVERNMENT OF INDIA - CITIZEN ID", fill="#ffffff")
    draw.text((190, 80), "NAME: RAMESH SHAMRAO PATIL", fill="#1a202c")
    draw.text((190, 110), "FATHER'S NAME: SHAMRAO PATIL", fill="#2d3748")
    draw.text((190, 140), "DATE OF BIRTH: 15/05/1978", fill="#2d3748")
    draw.text((190, 170), "GENDER: MALE", fill="#2d3748")
    draw.text((190, 200), "DISTRICT: KOLHAPUR, MAHARASHTRA", fill="#2d3748")

    # Aadhaar redaction badge
    draw.rectangle([(190, 240), (550, 290)], fill="#feebc8", outline="#dd6b20", width=1)
    draw.text((205, 255), "NATIONAL ID: [AADHAAR_REDACTED]", fill="#9c4221")

    # Footer
    draw.rectangle([(0, 330), (w, h)], fill="#edf2f7")
    draw.text((30, 345), "SYNTHETIC DEMO ASSET - PRIVACY SAFE (DPDP ACT 2023 ALIGNED)", fill="#718096")

    img.save(str(img_path), "JPEG", quality=90)
    print(f"Generated: {img_path}")

def generate_income_certificate_expired():
    img_path = artifacts_dir / "Artifact_B2_IncomeCert_Ramesh_S_Patil_Expired2023.jpg"
    w, h = 600, 420
    img = Image.new("RGB", (w, h), color="#fffaf0")
    draw = ImageDraw.Draw(img)

    # Border
    draw.rectangle([(10, 10), (w-10, h-10)], outline="#975a16", width=3)
    draw.rectangle([(15, 15), (w-15, h-15)], outline="#d69e2e", width=1)

    # Header
    draw.rectangle([(20, 20), (w-20, 60)], fill="#744210")
    draw.text((120, 30), "GOVERNMENT OF MAHARASHTRA - REVENUE DEPT", fill="#ffffff")

    # Content
    draw.text((40, 80), "TAHSILDAR OFFICE, KARVEER TALUKA, KOLHAPUR", fill="#744210")
    draw.text((40, 105), "CERTIFICATE OF ANNUAL FAMILY INCOME", fill="#1a202c")
    draw.line([(40, 125), (560, 125)], fill="#d69e2e", width=2)

    draw.text((40, 140), "Certificate No: REV/INC/2020/89412", fill="#4a5568")
    draw.text((40, 170), "Applicant Name: Ramesh S. Patil", fill="#1a202c")
    draw.text((40, 200), "Father's Name: Shamrao Patil", fill="#2d3748")
    draw.text((40, 230), "Annual Family Income: Rs. 1,80,000/- (One Lakh Eighty Thousand Only)", fill="#2d3748")
    draw.text((40, 260), "Issue Date: 10/04/2020", fill="#2d3748")

    # EXPIRED DATE (Crucial test vector against 2026-10-22)
    draw.rectangle([(35, 290), (565, 335)], fill="#fed7d7", outline="#e53e3e", width=2)
    draw.text((45, 302), "VALID UNTIL: 31/03/2023  [EXPIRED ON 2023-03-31]", fill="#9b2c2c")

    # Seal stamp simulation
    draw.ellipse([(450, 150), (550, 250)], outline="#e53e3e", width=2)
    draw.text((465, 190), "TAHSILDAR\n KOLHAPUR", fill="#e53e3e")

    # Footer
    draw.text((40, 385), "RapidFuzz Name Test: 'Ramesh S. Patil' vs Profile 'Ramesh Shamrao Patil'", fill="#718096")

    img.save(str(img_path), "JPEG", quality=90)
    print(f"Generated: {img_path}")

def generate_caste_certificate():
    img_path = artifacts_dir / "Artifact_B3_Valid_Caste_Cert.jpg"
    w, h = 600, 400
    img = Image.new("RGB", (w, h), color="#f7fafc")
    draw = ImageDraw.Draw(img)

    # Border
    draw.rectangle([(10, 10), (w-10, h-10)], outline="#2b6cb0", width=3)

    # Header
    draw.rectangle([(20, 20), (w-20, 60)], fill="#2b6cb0")
    draw.text((100, 30), "GOVERNMENT OF MAHARASHTRA - CASTE CERTIFICATE", fill="#ffffff")

    draw.text((40, 80), "SUB-DIVISIONAL OFFICER, KOLHAPUR DIVISION", fill="#2b6cb0")
    draw.line([(40, 105), (560, 105)], fill="#cbd5e0", width=1)

    draw.text((40, 120), "Certificate No: CASTE/SDO/KOL/2021/4482", fill="#4a5568")
    draw.text((40, 155), "This is to certify that:", fill="#2d3748")
    draw.text((40, 185), "SHRI RAMESH SHAMRAO PATIL", fill="#1a202c")
    draw.text((40, 215), "Son of Shri Shamrao Patil, Resident of Kolhapur", fill="#2d3748")
    draw.text((40, 245), "Belongs to Caste: KUNBI (OBC - Other Backward Class)", fill="#2c5282")
    draw.text((40, 275), "Under Govt of Maharashtra Resolution No. CBC-1484/3807/D-V", fill="#4a5568")

    draw.rectangle([(35, 310), (565, 345)], fill="#c6f6d5", outline="#38a169", width=1)
    draw.text((45, 320), "STATUS: VALID PERMANENT CERTIFICATE (VALID UNTIL: LIFETIME)", fill="#22543d")

    # Seal
    draw.ellipse([(450, 140), (550, 240)], outline="#2b6cb0", width=2)
    draw.text((465, 180), "SUB-DIV OFF\n  KOLHAPUR", fill="#2b6cb0")

    img.save(str(img_path), "JPEG", quality=90)
    print(f"Generated: {img_path}")

if __name__ == "__main__":
    generate_pdf_gr()
    generate_identity_card()
    generate_income_certificate_expired()
    generate_caste_certificate()
    print("All sample artifacts generated successfully.")
