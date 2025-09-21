import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
import boto3
from get_nearby_facilities import search_nearby_places, normalize_places

# --- Load environment variables ---
load_dotenv()
aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
aws_session_token = os.environ.get("AWS_SESSION_TOKEN")
aws_region = os.environ.get("AWS_DEFAULT_REGION")

# --- DynamoDB setup ---
dynamodb = boto3.resource(
    "dynamodb",
    region_name="ap-southeast-5",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    aws_session_token=aws_session_token
)
table = dynamodb.Table("MedicalAI_ChatHistory")

# --- Bedrock client setup ---
bedrock = boto3.client(
    "bedrock-runtime",
    region_name="us-east-1",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    aws_session_token=aws_session_token
)

# --- Helper: Save message to DynamoDB ---
def save_message(patient_id, role, message):
    table.put_item(Item={
        "patient_id": patient_id,
        "timestamp": str(uuid.uuid4()),
        "role": role,
        "message": message,
        "created_at": datetime.utcnow().isoformat()
    })

# --- Helper: Generate AI response ---
def chat_with_medrock(patient_id, user_message, history):
    history.append({"role": "user", "content": user_message})
    save_message(patient_id, "user", user_message)

    # Prepare prompt with instructions
    context_summary = history[-10:]  # last 10 messages for context
    missing_info_prompt = "\nIf any vitals (blood pressure, heart rate, oxygen saturation, temperature) are missing, politely ask the user to provide them. It is not mandatory but advised for better assessment."
    
    prompt = f"""
You are MedRock, a professional and empathetic medical assistant.
Current patient context: {json.dumps(context_summary, indent=2)}
User's new message: "{user_message}"

Instructions:
1. Provide a helpful, human-like response.
2. Ask for missing information in a polite and interactive way if needed.
3. Only issue high-risk warnings ⚠️ if new severe symptoms appear and avoid repeating.
4. Give follow-up questions based on patient's previous responses.
5. Include disclaimer: 'I am an AI assistant providing guidance; this is not a substitute for professional medical advice.'
{missing_info_prompt}
"""

    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 400,
            "messages": [{"role": "user", "content": prompt}]
        })
    )

    response_body = json.loads(response["body"].read())
    ai_reply = response_body["content"][0]["text"]

    save_message(patient_id, "assistant", ai_reply)
    history.append({"role": "assistant", "content": ai_reply})
    return ai_reply

# --- Nearby facility helpers ---
def get_facilities_for_user(lat, lon, category="hospital"):
    raw = search_nearby_places(lon, lat, category=category, radius=5000)
    return normalize_places(raw)

def format_facilities(facilities):
    if not facilities:
        return "Sorry, I could not find any nearby facilities."
    msg = "Here are some nearby facilities:\n"
    for i, f in enumerate(facilities, start=1):
        msg += f"{i}. {f['name']} ({f['category']})\n"
        msg += f"   Address: {f['address']}\n"
        msg += f"   Phone: {f['phone']}\n"
        if f['open_now'] is not None:
            msg += f"   Open now: {'Yes' if f['open_now'] else 'No'}\n"
        msg += f"   Distance: {f['distance_m']} meters\n"
    return msg

# --- Main Chat Loop ---
if __name__ == "__main__":
    patient_id = "patient_123"
    conversation_history = []

    print("Start chat with MedRock. Type 'exit' to quit.\n")
    print("MedRock: Hello! I'm MedRock, your AI medical assistant. I can help assess symptoms, suggest next steps, and recommend nearby medical facilities.\n")

    while True:
        user_message = input("You: ")
        if user_message.lower() in ["exit", "quit"]:
            print("Chat ended.")
            break

        # Special handling for nearby facility request
        if "nearby" in user_message.lower() or "clinic" in user_message.lower() or "hospital" in user_message.lower():
            print("MedRock: To recommend nearby facilities, please provide your location (latitude,longitude).")
            try:
                loc_input = input("You (lat,lon): ")
                lat, lon = map(float, loc_input.strip().split(","))
                facilities = get_facilities_for_user(lat, lon)
                print(f"MedRock: {format_facilities(facilities)}\n")
                # continue to next loop
                continue
            except:
                print("MedRock: Sorry, I couldn't understand your location. Please provide in the format lat,lon (e.g., 3.1390,101.6869).")
                continue

        # Normal conversation handled by Bedrock
        medrock_reply = chat_with_medrock(patient_id, user_message, conversation_history)
        print(f"MedRock: {medrock_reply}\n")
