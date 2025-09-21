import boto3
import logging
from dotenv import load_dotenv
import os
from botocore.exceptions import ClientError


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# load_dotenv()

aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
aws_session_token = os.environ.get("AWS_SESSION_TOKEN")
aws_region     = os.environ.get("AWS_DEFAULT_REGION")

# def invoke_agent(prompt:str, session_id: str) -> str:
#     client=boto3.client(
#         service_name="bedrock-agent-runtime",
#             # aws_access_key_id=aws_access_key,
#             # aws_secret_access_key=aws_secret_key,
#             # aws_session_token=aws_session_token,
#             # region_name=aws_region
#             region_name = "us-east-1"
#     ) 
    
#     agent_id = "HEGWMK0P43"
#     alias_id = "EGYZ1ACRL6"

#     response = client.invoke_agent(
#         agentId=agent_id,
#         agentAliasId=alias_id,
#         enableTrace=True,
#         sessionId = session_id,
#         inputText=prompt,
#         streamingConfigurations = { 
#             "applyGuardrailInterval" : 20,
#             "streamFinalResponse" : False
#         }
#     )
#     completion = ""
    
    
#     # print(response.get("completion"))
#     # for event in response.get("completion"):
#     #     #Collect agent output.
#     #     if 'chunk' in event:
#     #         chunk = event["chunk"]
#     #         completion += chunk["bytes"].decode()
        
#     #     # Log trace output.
#     #     if 'trace' in event:
#     #         trace_event = event.get("trace")
#     #         trace = trace_event['trace']

#     #          # Check for action group invocation
#     #         invocation_input = trace.get("invocationInput")
#     #         if invocation_input and "actionGroupInvocationInput" in invocation_input:
#     #             action_group_details = invocation_input["actionGroupInvocationInput"]
#     #             print(f"Action group invoked! Details: {action_group_details}")
#     #             # You can also add a flag or return this information
                
#     #         for key, value in trace.items():
#     #             logging.info("%s: %s",key,value)
    
#     for event in response['completion']:
#         if 'returnControl' in event:
#             return_control_payload = event['returnControl']
#             print(return_control_payload)
#             break

#     return completion



# if __name__ == "__main__":
   
#     # prompt = "What's the current time?"
#     prompt = "Hello"

#     try:
#         response = invoke_agent(prompt, "123123")
#         # print(response)
#     except ClientError as e:
#         print(f"Client error: {str(e)}")
#         logger.error("Client error: %s", {str(e)})


client = boto3.client("bedrock-agent-runtime")

# Step 1: Initial invoke to get inputs and invocationId
response = client.invoke_agent(
    inputText='User input',
    # other params
)

invocationId = response['invocationId']
invocationInputs = response['invocationInputs']
actionGroup = response['actionGroup']

# Step 2: Handle the invocationInputs as needed externally
result = 'blue'

# Step 3: Send back result using same invocationId and actionGroup
invoke_response = client.invoke_agent(
                sessionId="123123",
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
                                    "body": "SYMPTOMS ARE SEVERE"
                                }
                            }
                        }
                    }]
                }
            )