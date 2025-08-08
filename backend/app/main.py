# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0

"""
FastAPI WebSocket Server for Virtual Banking Assistant

This module implements a WebSocket server using FastAPI that handles real-time audio communication
between clients and an AI banking assistant powered by AWS Nova Sonic. It processes audio streams,
manages transcription, and coordinates responses through a pipeline architecture.

Key Components:
- WebSocket endpoint for real-time audio streaming
- Audio processing pipeline with VAD (Voice Activity Detection)
- Integration with AWS Nova Sonic LLM service
- Context management for conversation history
- Credential management for AWS services

Dependencies:
- FastAPI for WebSocket server
- Pipecat for audio processing pipeline
- AWS Bedrock for LLM services
- Silero VAD for voice activity detection

Environment Variables:
- AWS_CONTAINER_CREDENTIALS_RELATIVE_URI: URI for AWS container credentials
- AWS_ACCESS_KEY_ID: AWS access key
- AWS_SECRET_ACCESS_KEY: AWS secret key
- AWS_SESSION_TOKEN: AWS session token
"""

import asyncio
import json
import base64
import traceback
import boto3
import os
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import FastAPI, WebSocket, Request, Response
import uvicorn

from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer, VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.aws_nova_sonic.aws import AWSNovaSonicLLMService, Params
# from aws import AWSNovaSonicLLMService, Params
from pipecat.services.llm_service import FunctionCallParams
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketTransport, FastAPIWebsocketParams
from pipecat.serializers.plivo import PlivoFrameSerializer
from pipecat.processors.logger import FrameLogger
from pipecat.processors.transcript_processor import TranscriptProcessor

from app.aws_client_assume import get_session_token
from base64_serializer import Base64AudioSerializer
from sql_generator import SQLQueryGenerator

SAMPLE_RATE = 16000
sql_generator = SQLQueryGenerator()
API_KEY = "Your-own-long-secret-text-to-access-the-api"

def update_dredentials():
    """
    Updates AWS credentials by fetching from ECS container metadata endpoint.
    Used in containerized environments to maintain fresh credentials.
    """
    try:

        access_id, secret_key, token = get_session_token()

        os.environ["AWS_ACCESS_KEY_ID"] = access_id
        os.environ["AWS_SECRET_ACCESS_KEY"] = secret_key
        os.environ["AWS_SESSION_TOKEN"] = token

        print("AWS credentials refreshed successfully", flush=True)

        return access_id, secret_key, token

    except Exception as e:
        print(f"Error refreshing credentials: {str(e)}", flush=True)

# async def get_balance_from_api(params: FunctionCallParams):
#     if params.arguments["username"] == 'suresh':
#         if params.arguments["secret_passcode"].lower() != 'nova sonic is awesome' or params.arguments["secret_passcode"].lower() != 'novasonic is awesome':
#             await params.result_callback(
#                 {
#                     "balance": 5000 if params.arguments["account_type"] == 'savings' else 14000
#                 }
#             )
#
#         else:
#             print('INCORRECT PASSCODE !')
#             await params.result_callback(
#                 {
#                     "message": "Incorrect passcode."
#                 }
#             )
#
#     else:
#         await params.result_callback(
#             {
#                 "message": "No such user found."
#             }
#         )

async def generate_sql_query(params: FunctionCallParams):
    """
    Generate SQL query from natural language text using Claude 3.5 Sonnet V2.
    """
    try:
        text = params.arguments["text"]
        print("Text by User", text)
        schema = params.arguments.get("schema")

        query = sql_generator.generate_query(text, schema)

        if query:
            await params.result_callback({"response": query})
        else:
            await params.result_callback({"error": "Generated query appears invalid"})

    except Exception as e:
        await params.result_callback({"error": str(e)})


# weather_function = FunctionSchema(
#     name="get_balance",
#     description="Get an account balance.",
#     properties={
#         "username": {
#             "type": "string",
#             "description": "The username for which the account balance is to be fetched.",
#         },
#         "secret_passcode": {
#             "type": "string",
#             "description": "A sentence to be used as the secret passcode to access the account details.",
#         },
#         "account_type": {
#             "type": "string",
#             "description": "The type of the account. Either savings or fixed deposit.",
#         }
#     },
#     required=["username", "account_type"],
# )

sql_function = FunctionSchema(
    name="generate_sql_query",
    description="Generate an SQL query from natural language text using Claude 3.5 Sonnet model.",
    properties={
        "text": {
            "type": "string",
            "description": "Natural language description of the desired SQL query.",
        }
    },
    required=["text"],
)

# Create tools schema
# tools = ToolsSchema(standard_tools=[weather_function, sql_function])
tools = ToolsSchema(standard_tools=[sql_function])

async def setup(websocket: WebSocket):
    """
    Sets up the audio processing pipeline and WebSocket connection.
    
    Args:
        websocket: The WebSocket connection to set up

    Configures:
    - Audio transport with VAD and transcription
    - AWS Nova Sonic LLM service
    - Context management
    - Event handlers for client connection/disconnection
    """
    update_dredentials()

    prompt_text = None

    with open("/home/pulkitaa/Desktop/AWS PACE/virtual-assistant/backend/app/prompt.txt") as f:
        prompt_text = f.read()

    system_instruction = prompt_text + f"\n{AWSNovaSonicLLMService.AWAIT_TRIGGER_ASSISTANT_RESPONSE_INSTRUCTION}"

    print("System instruction: ", system_instruction)

    # Configure WebSocket transport with audio processing capabilities
    transport = FastAPIWebsocketTransport(websocket, FastAPIWebsocketParams(
        serializer=Base64AudioSerializer(),
        audio_in_enabled=True,
        audio_out_enabled=True,
        add_wav_header=False,
        vad_analyzer=SileroVADAnalyzer(
            params=VADParams(stop_secs=0.5)
        ),
        transcription_enabled=True
    ))

    # Configure AWS Nova Sonic parameters
    params = Params()
    params.input_sample_rate = SAMPLE_RATE
    params.output_sample_rate = SAMPLE_RATE

    # Initialize LLM service
    llm = AWSNovaSonicLLMService(
        secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        session_token=os.environ["AWS_SESSION_TOKEN"],
        region='us-east-1',
        voice_id="tiffany",  # Available voices: matthew, tiffany, amy
        params=params
    )

    # Register function for function calls
    # llm.register_function("get_balance", get_balance_from_api)
    llm.register_function("generate_sql_query", generate_sql_query)

    # Set up conversation context
    context = OpenAILLMContext(
        messages=[
            {"role": "system", "content": f"{system_instruction}"},
        ],
        tools=tools,
    )
    context_aggregator = llm.create_context_aggregator(context)

    # Create transcript processor
    transcript = TranscriptProcessor()

    # Configure processing pipeline
    pipeline = Pipeline(
        [
            transport.input(),  # Transport user input
            context_aggregator.user(),
            llm, 
            transport.output(),  # Transport bot output
            transcript.user(),
            transcript.assistant(), 
            context_aggregator.assistant(),
        ]
    )

    # Create pipeline task
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
            audio_in_sample_rate=SAMPLE_RATE,
            audio_out_sample_rate=SAMPLE_RATE
        ),
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        """Handles new client connections and initiates conversation."""
        print(f"Client connected")
        await task.queue_frames([context_aggregator.user().get_context_frame()])
        await llm.trigger_assistant_response()

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        """Handles client disconnection and cleanup."""
        print(f"Client disconnected")
        await task.cancel()

    @transcript.event_handler("on_transcript_update")
    async def handle_transcript_update(processor, frame):
        """Logs transcript updates with timestamps."""
        for message in frame.messages:
            print(f"Transcript: [{message.timestamp}] {message.role}: {message.content}")

    runner = PipelineRunner(handle_sigint=False, force_gc=True)
    await runner.run(task)

# Initialize FastAPI application
app = FastAPI()

@app.get('/health')
async def health(request: Request):
    """Health check endpoint."""
    return 'ok'

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint handling client connections.
    Validates API key and sets up the audio processing pipeline.
    """
    protocol = websocket.headers.get('sec-websocket-protocol')
    print('protocol ', protocol)

    await websocket.accept(subprotocol=API_KEY)
    await setup(websocket)

# Configure and start uvicorn server
server = uvicorn.Server(uvicorn.Config(
    app=app,
    host='0.0.0.0',
    port=8000,
    log_level="error"
))

async def serve():
    """Starts the FastAPI server."""
    await server.serve()

# Run the server
asyncio.run(serve())
