import os
import boto3
import json
from datetime import datetime
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
aws_session_token = os.environ.get("AWS_SESSION_TOKEN")
aws_region = os.environ.get("AWS_DEFAULT_REGION")

#DynamoDB client
dynamodb = boto3.resource(
    'dynamodb',
    region_name='ap-southeast-5',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    aws_session_token=aws_session_token
)

#Table reference
table_name = 'MedicalAI_ChatHistory'
table = dynamodb.Table(table_name)

def save_chat(patient_id, role, message, severity=None, recommendation=None, facilities=None):
    """Save chat messages into DynamoDB with optional metadata."""
    item = {
        'patient_id':patient_id,
        'timestamp': datetime.utcnow().isoformat(),
        'conversation_id': str(uuid.uuid4()),
        'message_role': role,
        'message_text': message
    }

    if severity:
        item['severity'] = severity
    if recommendation:
        item['recommendation'] = recommendation
    if facilities:
        item['facilities'] = json.dumps(facilities)
    
    table.put_item(Item=item)
    return item

def get_patient_history(patient_id, limit=10):
    """Retrieve last N message for a patient."""
    response = table.query(
        KeyConditionExpression = boto3.dynamodb.conditions.Key('patient_id').eq(patient_id),
        Limit = limit,
        ScanIndexForward = False
    )
    return response.get('Items', [])

#Example Usage
#Save a user message
save_chat(
    patient_id = 'patient_123',
    role = 'user',
    message = 'I have a chest pain and feeling shortness of breath since yesterday.'
)

save_chat(
    patient_id = 'patient_123',
    role = 'assistant',
    message = 'This looks serious, you should go to ER.',
    severity = 'Red',
    recommendation = 'Seek immediate hospital care.'
)

#Retrieve history
history = get_patient_history('patient_123')
print(json.dumps(history, indent=2))

