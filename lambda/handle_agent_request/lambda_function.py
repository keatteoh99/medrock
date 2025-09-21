import boto3
import json
import os

# Initialize the Bedrock Agent Runtime client
client = boto3.client('bedrock-agent-runtime')

# Retrieve agent details from environment variables for security and flexibility
AGENT_ID = os.environ.get('AGENT_ID')
AGENT_ALIAS_ID = os.environ.get('AGENT_ALIAS_ID')

def lambda_handler(event, context):
    """
    Handles requests from API Gateway to interact with the Bedrock Agent.

    This function is designed to handle two types of requests based on the
    event body:
    1. An initial prompt from the user.
    2. A follow-up request containing the result of a function that the 
       mobile app was asked to execute (return_control).
    """
    try:
        # Validate environment variables
        if not AGENT_ID or not AGENT_ALIAS_ID:
            return {'statusCode': 500, 'body': json.dumps('Error: AGENT_ID and AGENT_ALIAS_ID must be set.')}
        # The body from API Gateway is a string, so we need to parse it
        raw_body = event.get("body", "{}")
        if isinstance(raw_body, str):
            body = json.loads(raw_body)
        else:
            body = raw_body 

        
        session_id = body.get('sessionId')
        if not session_id:
            return {'statusCode': 400, 'body': json.dumps('Error: sessionId is required.')}

        # Check if this is a follow-up call with a function result
        if 'returnControl' in body:
            print(f"Handling return_control for session: {session_id}")
            invocation_input = body['returnControl']
            
            required_fields = ['invocationId', 'actionGroup', 'function', 'invocationResult']
            missing_fields = [field for field in required_fields if field not in invocation_input]
            if missing_fields:
                return {'statusCode': 400, 'body': json.dumps(f'Error: Missing required fields: {missing_fields}')}
    
            # This is the result from your mobile app's native code
            # We are just passing it back to the agent
            response = client.invoke_agent(
                sessionId=session_id,
                agentId=AGENT_ID,
                agentAliasId=AGENT_ALIAS_ID,
                  sessionState={
                    'invocationId': invocation_input['invocationId'],
                    'returnControlInvocationResults': [{
                        "functionResult": {
                            "actionGroup": invocation_input['actionGroup'],
                            "function": invocation_input['function'],
                            "responseBody": {
                                "TEXT": {
                                    "body": invocation_input['invocationResult']
                                }
                            }
                        }
                    }]
                }
            )
        
        # This is an initial prompt from the user
        elif 'prompt' in body:
            print(f"Handling new prompt for session: {session_id}")
            prompt = body.get('prompt')
            
            response = client.invoke_agent(
                sessionId=session_id,
                agentId=AGENT_ID,
                agentAliasId=AGENT_ALIAS_ID,
                inputText=prompt,
                enableTrace=True
            )
        
        else:
            return {'statusCode': 400, 'body': json.dumps('Error: Request body must contain either "prompt" or "returnControl".')}

        # Process the response stream from the agent
        # and prepare the final response for the mobile app
        agent_response = process_agent_response(response)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': agent_response
        }

    except Exception as e:
        print(f"An error occurred: {e}")
        return {'statusCode': 500, 'body': json.dumps(f'Internal server error: {str(e)}')}


def process_agent_response(response_stream):
    """
    Parses the streaming response from invoke_agent and returns a structured object.
    """
    final_completion = ""
    return_control_payload = None

    try:
        for event in response_stream['completion']:
            if 'chunk' in event:
                final_completion += event['chunk']['bytes'].decode()
            elif 'returnControl' in event:
                # If the agent returns control, we capture that payload
                # to send back to the mobile app.
                return_control_payload = event['returnControl']
                #break # Stop processing, as the app needs to take over
    except (KeyError, UnicodeDecodeError) as e:
        print(f"Error processing agent response: {e}")
    
    return {
        'completion': final_completion,
        'returnControl': return_control_payload,
        'contentType': 'application/json'
    }