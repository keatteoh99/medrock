import os
import boto3
import json
import re

aws_region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
runtime = boto3.client("bedrock-runtime", region_name=aws_region)


def _extract_json_from_text(text: str):
    # try direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # try fenced ```json ... ```
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass

    # try first {...} block
    m = re.search(r'(\{.*?\})', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass

    return None


def classify_severity(symptom_text: str, model_id="amazon.nova-lite-v1:0"):
    print(f"SYMPTOM: {symptom_text}")
    instruction = """
    You are a medical triage assistant.
    Classify the severity of the patient's symptoms into one of:
    - Mild: Mild, can be managed at home.
    - Moderate: Concerning, should visit a clinic within 24–48 hours.
    - Severe: Emergency, seek immediate hospital care.

    Respond with a single JSON object only.
    Do not use markdown, code fences, or any extra text.
    Output must be valid JSON with fields:
    - severity: string (mild | moderate | severe)
    - reason: string
    - recommendation: string
    - symptoms: array of objects with keys [name, severity, duration]
    - possible_conditions: array of strings
    """

    body = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"text": f"{instruction}\n\nSymptom description: {symptom_text}"}
                ]
            }
        ],
        "inferenceConfig": {
            "maxTokens": 300,
            "temperature": 0.3,
            "topP": 0.9
        }
    }

    response = runtime.invoke_model(
        modelId=model_id,
        body=json.dumps(body),
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response["body"].read())

    output_text = ""
    if "output" in result:
        message = result["output"].get("message", {})
        contents = message.get("content", [])
        if contents and "text" in contents[0]:
            output_text = contents[0]["text"].strip()

    structured = _extract_json_from_text(output_text)
    if not structured:
        structured = {
            "severity": "Unknown",
            "reason": output_text if output_text else "No response",
            "recommendation": "Retry classification",
            "symptoms": [],
            "possible_conditions": []
        }

    return structured


def lambda_handler(event, context):

    symptom_text = event.get("symptom_text", "")

    if not symptom_text:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Missing symptom_text"})
        }

    classification = classify_severity(symptom_text)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": classification
    }
