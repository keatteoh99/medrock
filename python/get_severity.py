import os
from dotenv import load_dotenv
import boto3
import json

load_dotenv()

aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
aws_session_token = os.environ.get("AWS_SESSION_TOKEN")
aws_region = os.environ.get("AWS_DEFAULT_REGION")

# ---- Runtime client for invoking Nova
runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=aws_region,
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    aws_session_token=aws_session_token
)

def classify_severity(symptom_text: str, model_id="amazon.nova-lite-v1:0"):
    """Classify severity color from user symptom description using Nova chat schema."""

    instruction = """
    You are a medical triage assistant.
    Classify the severity of the patient's symptoms into one of:
    - Mild: Mild, can be managed at home.
    - Moderate: Concerning, should visit a clinic within 24–48 hours.
    - Severe: Emergency, seek immediate hospital care.

    Respond ONLY in JSON with fields: severity (mild | moderate | severe), reason, recommendation.
    """

    body = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"text": f"{instruction}\n\nPatient description: {symptom_text}"}
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

    # Extract text
    output_text = ""
    if "output" in result:
        message = result["output"].get("message", {})
        contents = message.get("content", [])
        if contents and "text" in contents[0]:
            output_text = contents[0]["text"].strip()

    # Try to parse JSON safely
    try:
        structured = json.loads(output_text)
    except:
        # fallback: wrap into JSON
        structured = {
            "severity": "Unknown",
            "reason": output_text if output_text else "No response",
            "recommendation": "Retry classification"
        }

    return structured

    # ---- Debugging & Test Run
if __name__ == "__main__":
    test_input = "I have chest pain and shortness of breath for the past hour."

    # Run classification via our function
    classification = classify_severity(test_input)

    # Debug: Print raw response directly from Nova
    print("\n--- RAW RESPONSE ---")
    response = runtime.invoke_model(
        modelId="amazon.nova-lite-v1:0",
        body=json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"text": f"Classify severity of symptoms: {test_input}"}
                    ]
                }
            ],
            "inferenceConfig": {"maxTokens": 300}
        }),
        contentType="application/json",
        accept="application/json"
    )
    raw = json.loads(response["body"].read())
    print(json.dumps(raw, indent=2))

    # Parsed classification result
    print("\n--- PARSED CLASSIFICATION ---")
    print(json.dumps(classification, indent=2))


