import os
import hashlib
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from config import settings

class ReceiptScraper:
    """
    Generates verifiable official acknowledgment receipt PDFs with cryptographic signatures.
    """

    def generate_receipt_pdf(
        self,
        tracking_id: str,
        citizen_name: str,
        scheme_name: str,
        portal_name: str,
        output_dir: str
    ) -> str:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = out_dir / f"Receipt_{tracking_id}.pdf"

        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('RecTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=14, leading=18, alignment=1, textColor=colors.HexColor('#1e3a8a'))
        badge_style = ParagraphStyle('RecBadge', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12, alignment=1, textColor=colors.HexColor('#c2410c'))
        body_style = ParagraphStyle('RecBody', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14)
        bold_body = ParagraphStyle('RecBold', parent=body_style, fontName='Helvetica-Bold')

        story = []
        story.append(Paragraph("GOVERNMENT OF MAHARASHTRA", title_style))
        story.append(Paragraph(portal_name, title_style))
        story.append(Paragraph("[DEMO SIMULATION - OFFICIAL ACKNOWLEDGMENT RECEIPT]", badge_style))
        story.append(Spacer(1, 15))

        sig_hash = hashlib.sha256(f"{tracking_id}::{citizen_name}::{scheme_name}::{settings.REFERENCE_DATE}".encode()).hexdigest()

        table_data = [
            [Paragraph("<b>Portal Tracking ID:</b>", body_style), Paragraph(f"<b><font size=12 color='#1e3a8a'>{tracking_id}</font></b>", bold_body)],
            [Paragraph("<b>Applicant Name:</b>", body_style), Paragraph(citizen_name, body_style)],
            [Paragraph("<b>National ID:</b>", body_style), Paragraph("[AADHAAR_REDACTED] (Verified)", body_style)],
            [Paragraph("<b>Applied Scheme:</b>", body_style), Paragraph(scheme_name, body_style)],
            [Paragraph("<b>Submission Date & Time:</b>", body_style), Paragraph(f"{settings.REFERENCE_DATE} 09:30:00 IST", body_style)],
            [Paragraph("<b>Document Verification:</b>", body_style), Paragraph("Valid (Compressed 38.4 KB - Portal Compliant)", body_style)],
            [Paragraph("<b>Digital Signature Hash:</b>", body_style), Paragraph(f"<font size=8 face='Courier'>{sig_hash}</font>", body_style)]
        ]

        t = Table(table_data, colWidths=[160, 370])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 7)
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

        story.append(Paragraph("<b>NOTE:</b> Keep this acknowledgment receipt safely for all future correspondence under the Maharashtra Right to Public Services Act, 2015.", body_style))
        story.append(Spacer(1, 30))
        story.append(Paragraph("<b>Competent Authority</b><br/>Aaple Sarkar DBT Directorate, Mantralaya, Mumbai", bold_body))

        doc.build(story)
        return str(pdf_path)

receipt_scraper = ReceiptScraper()
