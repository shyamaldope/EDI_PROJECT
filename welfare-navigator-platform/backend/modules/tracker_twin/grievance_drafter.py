import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from config import settings

class GrievanceDrafter:
    """
    Generates formal legal appellate grievance PDFs under the
    Maharashtra Right to Public Services Act, 2015 (RTS Act) & CPGRAMS.
    """

    def draft_rts_appeal_pdf(
        self,
        citizen_name: str,
        phone_masked: str,
        application_id: str,
        portal_tracking_id: str,
        scheme_name: str,
        department: str,
        days_elapsed: int,
        sla_days: int,
        days_overdue: int,
        output_dir: str
    ) -> str:
        """
        Drafts the statutory Form-1 First Appeal under Section 8 of the Maharashtra RTS Act 2015.
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = out_dir / f"RTS_Appeal_{portal_tracking_id}_{citizen_name.replace(' ', '_')}.pdf"

        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'RTSHeader',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            alignment=1,
            textColor=colors.HexColor('#9b2c2c')
        )
        sub_style = ParagraphStyle('RTSSub', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=14, alignment=1)
        body_style = ParagraphStyle('RTSBody', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=13)
        bold_body = ParagraphStyle('RTSBoldBody', parent=body_style, fontName='Helvetica-Bold')

        story = []
        story.append(Paragraph("FORM NO. 1", title_style))
        story.append(Paragraph("[See Rule 5(1)]", sub_style))
        story.append(Paragraph("FIRST APPEAL MEMORANDUM UNDER SECTION 8(1) OF", sub_style))
        story.append(Paragraph("THE MAHARASHTRA RIGHT TO PUBLIC SERVICES ACT, 2015", sub_style))
        story.append(Spacer(1, 15))

        # Addressee
        story.append(Paragraph("<b>To,</b><br/>The First Appellate Authority,<br/>" + department + ",<br/>District Collectorate / Competent Authority, Maharashtra", body_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph(f"<b>Subject:</b> First Appeal regarding statutory SLA delay in providing public service: <u>{scheme_name}</u> (Application ID: {portal_tracking_id})", bold_body))
        story.append(Spacer(1, 12))

        # Details Table
        table_data = [
            [Paragraph("<b>Appellant Name:</b>", body_style), Paragraph(citizen_name, body_style)],
            [Paragraph("<b>Portal Tracking ID:</b>", body_style), Paragraph(portal_tracking_id, bold_body)],
            [Paragraph("<b>Public Service / Scheme:</b>", body_style), Paragraph(scheme_name, body_style)],
            [Paragraph("<b>Department:</b>", body_style), Paragraph(department, body_style)],
            [Paragraph("<b>Statutory SLA Limit:</b>", body_style), Paragraph(f"{sla_days} Working Days", body_style)],
            [Paragraph("<b>Total Days Elapsed:</b>", body_style), Paragraph(f"<b>{days_elapsed} Days</b>", bold_body)],
            [Paragraph("<b>Unlawful Delay (Breach):</b>", body_style), Paragraph(f"<font color='#e53e3e'><b>{days_overdue} Days Delayed</b></font>", bold_body)],
            [Paragraph("<b>Reference Date:</b>", body_style), Paragraph(settings.REFERENCE_DATE, body_style)]
        ]
        t = Table(table_data, colWidths=[160, 370])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fff5f5')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#feb2b2')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6)
        ]))
        story.append(t)
        story.append(Spacer(1, 15))

        # Grounds
        story.append(Paragraph("<b>GROUNDS OF APPEAL:</b>", bold_body))
        story.append(Paragraph("1. That the appellant duly submitted an application for the aforesaid notified public service along with all verified documentation through the state government portal.", body_style))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"2. That under Section 3 of the Maharashtra Right to Public Services Act, 2015, the Designated Officer was statutorily mandated to dispose of the application within <b>{sla_days} days</b>.", body_style))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"3. That <b>{days_elapsed} days</b> have elapsed without delivery of service or communication of reason for rejection, thereby constituting a direct statutory SLA breach of <b>{days_overdue} days</b>.", body_style))
        story.append(Spacer(1, 6))
        story.append(Paragraph("4. That under Section 9(1) of the Act, a penalty at the rate of Rs. 250 per day up to Rs. 5,000 is liable to be imposed on the concerned Designated Officer for failure to deliver notified service.", body_style))
        story.append(Spacer(1, 15))

        # Prayer
        story.append(Paragraph("<b>PRAYER / RELIEF SOUGHT:</b>", bold_body))
        story.append(Paragraph("The Appellant prays that this Hon'ble First Appellate Authority be pleased to:<br/>"
                               "(a) Direct the Designated Officer to immediately sanction and disburse the scheme benefit;<br/>"
                               "(b) Recommend disciplinary proceedings and penalty under Section 9(1) of the RTS Act 2015;<br/>"
                               "(c) Award statutory compensation to the appellant for undue administrative delay.", body_style))
        story.append(Spacer(1, 20))

        story.append(Paragraph(f"<b>Verification:</b> I, {citizen_name}, verify that the contents of this memorandum are true and correct to the best of my knowledge.", body_style))
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"<b>(Signature of Appellant)</b><br/>{citizen_name}<br/>Contact: [PHONE_REDACTED]", bold_body))

        doc.build(story)
        return str(pdf_path)

grievance_drafter = GrievanceDrafter()
