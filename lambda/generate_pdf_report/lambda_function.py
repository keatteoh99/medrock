import os
import boto3
import json
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

s3_client = boto3.client("s3")

def lambda_handler(event, context):
    body = json.loads(event["body"])

    # Patient info
    patient = body.get("patient", {})
    patient_id = patient.get("patient_id", "N/A")
    name = patient.get("name", "N/A")
    age = patient.get("age", "N/A")
    gender = patient.get("gender", "N/A")
    medical_history = patient.get("medical_history", [])

    # Clinical info
    severity = body.get("severity", "Unknown")
    reason = body.get("reason", "N/A")
    recommendation = body.get("recommendation", "N/A")
    symptoms = body.get("symptoms", [])
    possible_conditions = body.get("possible_conditions", [])

    # Setup PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []

    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        "Header",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=6
    )
    subheader_style = ParagraphStyle(
        "SubHeader",
        parent=styles["Heading2"],
        fontSize=14,
        spaceAfter=8
    )
    normal = styles["Normal"]

    # Title
    story.append(Paragraph("Medical Report", header_style))
    report_time = datetime.now().strftime("%d %b %Y, %I:%M %p")
    story.append(Paragraph(f"Report Generated: {report_time}", normal))
    story.append(Spacer(1, 12))

    # Patient info section
    story.append(Paragraph("Patient Information", subheader_style))
    patient_table_data = [
        ["Patient ID", patient_id],
        ["Name", name],
        ["Age", str(age)],
        ["Gender", gender]
    ]
    patient_table = Table(patient_table_data, hAlign="LEFT", colWidths=[100, 300])
    patient_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 8))

    if medical_history:
        story.append(Paragraph("Medical History:", normal))
        for history_item in medical_history:
            story.append(Paragraph(f"• {history_item}", normal))
        story.append(Spacer(1, 12))

    # Severity section
    story.append(Paragraph("Overall Severity", subheader_style))
    story.append(Paragraph(severity, normal))
    story.append(Spacer(1, 12))

    # Reason
    story.append(Paragraph("Reason", subheader_style))
    story.append(Paragraph(reason, normal))
    story.append(Spacer(1, 12))

    # Recommendation
    story.append(Paragraph("Recommendation", subheader_style))
    story.append(Paragraph(recommendation, normal))
    story.append(Spacer(1, 12))

    # Symptoms (Table)
    if symptoms:
        story.append(Paragraph("Reported Symptoms", subheader_style))
        table_data = [["Name", "Severity", "Duration"]]
        for s in symptoms:
            table_data.append([
                s.get("name", ""),
                s.get("severity", ""),
                s.get("duration", "")
            ])

        table = Table(table_data, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

    # Possible conditions (Bullet list)
    if possible_conditions:
        story.append(Paragraph("Possible Conditions", subheader_style))
        for condition in possible_conditions:
            story.append(Paragraph(f"• {condition}", normal))
        story.append(Spacer(1, 12))

    # Build PDF
    doc.build(story)

    # Upload to S3
    buffer.seek(0)
    bucket = os.environ.get("S3_BUCKET_NAME")
    key = f"reports/medical_report_{patient_id}.pdf"

    s3_client.upload_fileobj(buffer, bucket, key, ExtraArgs={"ContentType": "application/pdf"})

    pdf_url = f"https://{bucket}.s3.amazonaws.com/{key}"

    return {
        "statusCode": 200,
        "body": json.dumps({"pdf_url": pdf_url})
    }
