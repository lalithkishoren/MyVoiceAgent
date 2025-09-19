#!/usr/bin/env python3

import asyncio
import os
import sys
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import structlog

# Pipecat imports
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.services.gemini_multimodal_live.gemini import GeminiMultimodalLiveLLMService
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketTransport,
    FastAPIWebsocketParams,
)
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.frames.frames import LLMRunFrame, EndFrame, TextFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext

# Load environment variables
load_dotenv()

# Configure logging
logger = structlog.get_logger(__name__)

# Import Gmail email functionality and enhanced features
from gmail_routes import router as gmail_router
from enhanced_appointment_functions import enhanced_appointment_tools, ENHANCED_FUNCTION_REGISTRY

# Import call logging and patient storage
from call_logger import CallLogger, CallRecord
from google_sheets_service import GoogleSheetsService, PatientRecord, CallLogRecord
import uuid

# Global variables
active_sessions = {}
session_call_records = {}  # Store call records by session ID
patient_database = {}  # Simple in-memory patient database {phone: patient_info}

# Initialize call logger
call_logger = CallLogger()

# Helper function to update call record during conversations
def update_call_record(session_id: str, **kwargs):
    """Update call record with patient information during conversation"""
    if session_id in session_call_records:
        call_record = session_call_records[session_id]
        for key, value in kwargs.items():
            if hasattr(call_record, key) and value:
                setattr(call_record, key, value)
        logger.info(f"Updated call record for session {session_id}: {list(kwargs.keys())}")
    else:
        logger.warning(f"No call record found for session {session_id}")

# Initialize Google credentials once at startup
logger.info("Initializing Google credentials at startup...")
try:
    from googel_auth_manger import get_credentials
    global_google_credentials = get_credentials()
    logger.info("SUCCESS: Google credentials initialized successfully")

    # Initialize Google Sheets service with the same credentials
    logger.info("Initializing Google Sheets service...")
    global_sheets_service = GoogleSheetsService(global_google_credentials)
    logger.info("SUCCESS: Google Sheets service initialized successfully")
except Exception as e:
    logger.error(f"ERROR: Failed to initialize Google services: {e}")
    logger.error("Google services (Gmail/Calendar/Sheets) will not work!")
    global_google_credentials = None
    global_sheets_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Pipecat server with proper transport")
    yield
    logger.info("Shutting down Pipecat server")

# FastAPI app
app = FastAPI(
    title="Pipecat Voice Server with Proper Transport",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Gmail routes
app.include_router(gmail_router)

# Patient information storage functions
def store_patient_info(phone: str, patient_data: dict):
    """Store patient information in Google Sheets and local database"""
    customer_type = patient_data.get('customer_type', 'new')

    # For existing/returning customers, merge with existing data
    existing_data = {}
    if phone in patient_database:
        existing_data = patient_database[phone].copy()
        logger.info(f"Updating existing customer data for: {phone}")

    # Store in local memory (for immediate access during session)
    patient_database[phone] = {
        'name': patient_data.get('name', existing_data.get('name', '')),
        'email': patient_data.get('email', existing_data.get('email', '')),
        'phone': phone,
        'last_appointment': patient_data.get('notes', existing_data.get('last_appointment', '')),
        'preferred_doctor': patient_data.get('preferred_doctor', existing_data.get('preferred_doctor', '')),
        'department': patient_data.get('department', existing_data.get('department', '')),
        'language_preference': patient_data.get('language', existing_data.get('language_preference', 'english')),
        'customer_type': customer_type,
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'visit_count': existing_data.get('visit_count', 0) + 1 if customer_type in ['existing', 'returning'] else 1
    }

    # Store in Google Sheets (persistent storage)
    if global_sheets_service:
        try:
            patient_record = PatientRecord(
                phone=phone,
                name=patient_data.get('name', ''),
                email=patient_data.get('email', ''),
                last_visit=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                preferred_doctor=patient_data.get('preferred_doctor', ''),
                department=patient_data.get('department', ''),
                language=patient_data.get('language', 'english'),
                customer_type=patient_data.get('customer_type', 'unknown'),
                notes=patient_data.get('notes', '')
            )
            global_sheets_service.save_patient_data(patient_record)
            logger.info(f"Stored patient info in Google Sheets for: {phone}")
        except Exception as e:
            logger.error(f"Failed to store patient in Google Sheets: {e}")

    logger.info(f"Stored patient info for: {phone}")

def get_patient_info(phone: str) -> dict:
    """Retrieve patient information from Google Sheets and local database"""
    # First check local memory for current session
    local_patient = patient_database.get(phone, None)

    # Then check Google Sheets for persistent data
    sheets_patient = None
    if global_sheets_service:
        try:
            patient_record = global_sheets_service.get_patient_by_phone(phone)
            if patient_record:
                sheets_patient = {
                    'name': patient_record.name,
                    'email': patient_record.email,
                    'phone': patient_record.phone,
                    'last_appointment': patient_record.last_visit,
                    'preferred_doctor': patient_record.preferred_doctor,
                    'department': patient_record.department,
                    'language_preference': patient_record.language,
                    'customer_type': patient_record.customer_type,
                    'last_updated': patient_record.updated
                }
                logger.info(f"Retrieved patient info from Google Sheets for: {phone}")
        except Exception as e:
            logger.error(f"Failed to retrieve patient from Google Sheets: {e}")

    # Return merged data (local takes precedence for current session)
    if local_patient and sheets_patient:
        # Merge with local data taking precedence
        merged = sheets_patient.copy()
        merged.update(local_patient)
        return merged
    elif local_patient:
        return local_patient
    elif sheets_patient:
        # Store in local memory for this session
        patient_database[phone] = sheets_patient
        return sheets_patient
    else:
        return None

def update_call_record(session_id: str, updates: dict):
    """Update call record with new information"""
    if session_id in session_call_records:
        call_record = session_call_records[session_id]
        for key, value in updates.items():
            if hasattr(call_record, key):
                setattr(call_record, key, value)
        logger.info(f"Updated call record for session: {session_id}")

async def run_bot(websocket: WebSocket, session_id: str, voice_id: str = "Charon"):
    """Run a Pipecat bot using proper FastAPI WebSocket transport."""
    try:
        # Create FastAPI WebSocket transport with high quality audio settings
        transport = FastAPIWebsocketTransport(
            websocket=websocket,
            params=FastAPIWebsocketParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                add_wav_header=False,
                vad_analyzer=SileroVADAnalyzer(),
                serializer=ProtobufFrameSerializer(),
                # High quality audio settings
                audio_out_sample_rate=24000,  # Higher sample rate for better quality
                audio_in_sample_rate=16000,
                audio_out_channels=1,
            )
        )

        # Initialize Gemini Multimodal Live service with selected voice and function calling
        llm = GeminiMultimodalLiveLLMService(
            api_key=os.getenv("GEMINI_API_KEY"),
            voice_id=voice_id,  # Configurable voice: Puck, Charon, Kore, Fenrir
            model="models/gemini-2.0-flash-exp",  # Use latest model
            tools=enhanced_appointment_tools,  # Add enhanced appointment function tools
            # System instruction for natural conversation and greeting
            system_instruction=f"""You are Archana, a patient service voice assistant for Renova Hospitals.

Your main role is to answer patient questions briefly, clearly, and politely regarding our services, appointments, opening hours, or emergency notices.

LANGUAGE SUPPORT: Detect the user's language and respond ONLY in that language. Do NOT mix languages in your response.
- If user speaks Telugu → respond ONLY in Telugu
- If user speaks Hindi → respond ONLY in Hindi
- If user speaks English → respond ONLY in English
Never provide translations or repeat the same message in multiple languages.

FUNCTION CALLING: When calling any function, ALWAYS provide all parameters in English only (names, emails, addresses, etc.) regardless of the conversation language. This ensures consistent data processing.

PRONUNCIATION RULES:
- Phone numbers: Pronounce each digit separately (1-2-3-4 not "twelve thirty-four")
- Email addresses: Spell out character by character when needed
- Numbers in time/dates: Use the same language as the conversation (Telugu "పదకొండు గంటలు" not "11 hours")
- All content including numbers, times, dates must be in the detected language

VOICE INSTRUCTION: Use natural, native pronunciation for the detected language only. Speak as a fluent native speaker would.

CURRENT DATE CONTEXT:
Today's date is: {datetime.now().strftime('%Y-%m-%d')} ({datetime.now().strftime('%A, %B %d, %Y')})

DATE INTERPRETATION GUIDELINES:
- "today" = {datetime.now().strftime('%Y-%m-%d')}
- "tomorrow" = {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}
- "day after tomorrow" = {(datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')}
- "next Monday/Tuesday/etc" = calculate the next occurrence of that weekday
- Always convert dates to YYYY-MM-DD format when calling the appointment function
- If patient says relative dates like "tomorrow" or "next week", convert to exact dates

CORRECT APPOINTMENT BOOKING PROCESS (Follow this exact sequence):

STEP 1: INITIAL CONTACT & BASIC INFO
1. Greet patient: "Hi! I'm Archana, your AI assistant from Renova Hospitals. How can I help you today?"
2. Collect patient name
3. Collect phone number

STEP 2: CUSTOMER DETECTION (MANDATORY - NO EXCEPTIONS)
4. AS SOON AS YOU HAVE NAME AND PHONE, IMMEDIATELY call detect_customer_type(phone_number, patient_name):
   - This is NOT OPTIONAL - you MUST call this function
   - Do this BEFORE asking any other questions
   - Do this BEFORE collecting email or appointment details
   - Say "Let me check if you're in our system" then call the function
   - Wait for the function result before continuing

STEP 3: PERSONALIZED RESPONSE BASED ON CUSTOMER TYPE
5a. FOR RETURNING CUSTOMERS: "Welcome back [Name]! I see you've visited us before. Would you like to book with [Previous Doctor] again?"
5b. FOR NEW CUSTOMERS: "Thank you [Name]. I'll need to collect some additional information to help you."

STEP 4: INFORMATION COLLECTION (Based on customer type)
6. Collect email address (skip if returning customer with email on file)
7. Collect appointment preferences (use previous preferences for returning customers)
   - Preferred date/time - ALWAYS convert relative dates to YYYY-MM-DD format
   - Department/specialty needed
   - Doctor preference (suggest previous doctor for returning customers)

STEP 5: APPOINTMENT VERIFICATION & BOOKING
8. CRITICAL: ALWAYS call check_appointment_availability() first to verify the time slot is available
9. If available: Proceed with booking by calling book_appointment() function
10. If not available: Suggest alternative times from the availability check results

CUSTOMER RECOGNITION RULES:
- NEVER proceed with appointment details until customer type is determined
- Always personalize the experience based on customer history
- Use previous preferences to speed up the process for returning customers
- Be explicit about recognizing returning customers to build trust

CUSTOMER TYPE RESPONSES:
- NEW CUSTOMER: "Thank you [Name]. I'll help you book your first appointment with us."
- RETURNING CUSTOMER: "Welcome back [Name]! I see you visited us before. Would you like to book with Dr. [Previous Doctor] again?"
- EXISTING CUSTOMER: "I have your information from our earlier conversation."

CRITICAL BUSINESS FLOW (SEQUENTIAL STEPS - DO NOT SKIP):
1. Customer calls → Greet and ask how to help
2. Collect name → Collect phone number
3. STOP! Say "Let me check if you're in our system"
4. MANDATORY: Call detect_customer_type(phone_number, patient_name) function NOW
5. Based on function result:
   - If returning customer: "Welcome back! I found your information. Email: [email]"
   - If new customer: "I'll help you book your first appointment"
6. Collect remaining info (skip email if returning customer)
7. ALWAYS call check_appointment_availability(date, time) FIRST
8. If available → Call book_appointment() to complete booking
9. If not available → Present alternatives and repeat availability check

EXAMPLE FLOW:
User: "I want to book an appointment"
You: "I'd be happy to help! What's your name?"
User: "John Doe"
You: "And your phone number?"
User: "555-1234"
You: "Let me check if you're in our system" → CALL detect_customer_type("555-1234", "John Doe")
Result: Returning customer with email john@email.com
You: "Welcome back John! I found your information. Your email is john@email.com. What type of appointment would you like?"

You have access to the following functions:
- detect_customer_type: MANDATORY - Check customer type and retrieve existing info after collecting phone number
- check_appointment_availability: Check if a time slot is available and get alternatives
- book_appointment: Book appointment with email confirmation AND calendar entry
- cancel_appointment: Cancel existing appointments
- log_call_information: Log call details for record keeping

Start every conversation with: "Hi! How are you? I'm Archana, your AI assistant from Renova Hospitals. How can I help you today?"

Speak naturally with contractions and natural rhythm."""
        )

        # Create session-aware error-wrapped function handlers
        def create_session_aware_handler(original_handler, func_name):
            async def wrapped_handler(params):
                try:
                    # Add session_id to params for call record updates
                    if hasattr(params, 'arguments'):
                        params.arguments['session_id'] = session_id

                    result = await original_handler(params)

                    # Update call record with any patient information collected
                    if hasattr(params, 'arguments') and session_id in session_call_records:
                        args = params.arguments
                        call_record = session_call_records[session_id]

                        # Update call record based on function type and arguments
                        if func_name in ['book_appointment', 'send_appointment_email']:
                            phone = args.get('phone')
                            patient_name = args.get('patient_name')
                            email = args.get('email')

                            # Customer detection logic
                            customer_type = "new"
                            if phone:
                                # Check local memory first (current session patients)
                                if phone in patient_database:
                                    customer_type = "existing"
                                    logger.info(f"Found existing customer in local memory: {phone}")
                                else:
                                    # Check Google Sheets for historical patients
                                    if global_sheets_service:
                                        try:
                                            existing_patient = global_sheets_service.get_patient_by_phone(phone)
                                            if existing_patient:
                                                customer_type = "returning"
                                                logger.info(f"Found returning customer in Google Sheets: {phone}")

                                                # Update local memory with returning customer info
                                                patient_database[phone] = {
                                                    'name': existing_patient.name,
                                                    'email': existing_patient.email,
                                                    'phone': phone,
                                                    'last_appointment': existing_patient.last_visit,
                                                    'preferred_doctor': existing_patient.preferred_doctor,
                                                    'department': existing_patient.department,
                                                    'language_preference': existing_patient.language,
                                                    'customer_type': 'returning',
                                                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                }
                                        except Exception as e:
                                            logger.error(f"Error checking Google Sheets for existing customer: {e}")

                            # Update call record with patient info
                            if patient_name:
                                call_record.customer_name = patient_name
                            if email:
                                call_record.customer_email = email
                            if phone:
                                call_record.caller_phone = phone
                            if args.get('department'):
                                call_record.department_enquired = args['department']
                            if args.get('doctor_name'):
                                call_record.doctor_enquired = args['doctor_name']
                            if args.get('appointment_date'):
                                call_record.appointment_date = args['appointment_date']
                            if args.get('appointment_time'):
                                call_record.appointment_time = args['appointment_time']

                            call_record.call_type = "appointment_booking"
                            call_record.customer_type = customer_type

                            # Store/update patient information
                            if phone and patient_name:
                                store_patient_info(phone, {
                                    'name': patient_name,
                                    'email': email or '',
                                    'department': args.get('department', ''),
                                    'preferred_doctor': args.get('doctor_name', ''),
                                    'language': call_record.language_used,
                                    'customer_type': customer_type,
                                    'notes': f"Last appointment: {args.get('appointment_date', '')} {args.get('appointment_time', '')}"
                                })
                                logger.info(f"Stored/updated patient info for {customer_type} customer: {phone}")

                        elif func_name == 'cancel_appointment':
                            phone = args.get('patient_phone')
                            patient_name = args.get('patient_name')

                            # Customer detection for cancellation
                            customer_type = "unknown"
                            if phone:
                                if phone in patient_database:
                                    customer_type = "existing"
                                elif global_sheets_service:
                                    try:
                                        existing_patient = global_sheets_service.get_patient_by_phone(phone)
                                        if existing_patient:
                                            customer_type = "returning"
                                    except Exception as e:
                                        logger.error(f"Error checking customer for cancellation: {e}")

                            call_record.call_type = "appointment_cancellation"
                            call_record.customer_type = customer_type
                            if patient_name:
                                call_record.customer_name = patient_name
                            if phone:
                                call_record.caller_phone = phone
                            if args.get('doctor_name'):
                                call_record.doctor_enquired = args['doctor_name']
                            if args.get('appointment_date'):
                                call_record.appointment_date = args['appointment_date']
                            if args.get('appointment_time'):
                                call_record.appointment_time = args['appointment_time']

                        # Update resolution based on result
                        if isinstance(result, dict) and result.get('success'):
                            call_record.resolution_status = "resolved"
                            call_record.agent_notes = result.get('message', '')
                        else:
                            call_record.resolution_status = "unresolved"

                    return result

                except Exception as e:
                    logger.error(f"Error in function {func_name}: {e}")

                    # Update call record for errors
                    if session_id in session_call_records:
                        call_record = session_call_records[session_id]
                        call_record.resolution_status = "error"
                        call_record.agent_notes = f"Function error: {str(e)}"

                    return {
                        'success': False,
                        'error': f"Service temporarily unavailable. Please try again.",
                        'internal_error': str(e)
                    }
            return wrapped_handler

        # Register all enhanced functions with session-aware error handling
        for func_name, func_handler in ENHANCED_FUNCTION_REGISTRY.items():
            wrapped_handler = create_session_aware_handler(func_handler, func_name)
            llm.register_function(func_name, wrapped_handler)

        # Create context with tools for function calling support
        context = OpenAILLMContext(
            messages=[
                {
                    "role": "system",
                    "content": f"""You are Archana, a patient service voice assistant for Renova Hospitals.

Your main role is to answer patient questions briefly, clearly, and politely regarding our services, appointments, opening hours, or emergency notices.

LANGUAGE SUPPORT: Detect the user's language and respond ONLY in that language. Do NOT mix languages in your response.
- If user speaks Telugu → respond ONLY in Telugu
- If user speaks Hindi → respond ONLY in Hindi
- If user speaks English → respond ONLY in English
Never provide translations or repeat the same message in multiple languages.

FUNCTION CALLING: When calling any function, ALWAYS provide all parameters in English only (names, emails, addresses, etc.) regardless of the conversation language. This ensures consistent data processing.

PRONUNCIATION RULES:
- Phone numbers: Pronounce each digit separately (1-2-3-4 not "twelve thirty-four")
- Email addresses: Spell out character by character when needed
- Numbers in time/dates: Use the same language as the conversation (Telugu "పదకొండు గంటలు" not "11 hours")
- All content including numbers, times, dates must be in the detected language

VOICE INSTRUCTION: Use natural, native pronunciation for the detected language only. Speak as a fluent native speaker would.

CURRENT DATE CONTEXT:
Today's date is: {datetime.now().strftime('%Y-%m-%d')} ({datetime.now().strftime('%A, %B %d, %Y')})

DATE INTERPRETATION GUIDELINES:
- "today" = {datetime.now().strftime('%Y-%m-%d')}
- "tomorrow" = {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}
- "day after tomorrow" = {(datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')}
- "next Monday/Tuesday/etc" = calculate the next occurrence of that weekday
- Always convert dates to YYYY-MM-DD format when calling the appointment function
- If patient says relative dates like "tomorrow" or "next week", convert to exact dates

CORRECT APPOINTMENT BOOKING PROCESS (Follow this exact sequence):

STEP 1: INITIAL CONTACT & BASIC INFO
1. Greet patient: "Hi! I'm Archana, your AI assistant from Renova Hospitals. How can I help you today?"
2. Collect patient name
3. Collect phone number

STEP 2: CUSTOMER DETECTION (MANDATORY - NO EXCEPTIONS)
4. AS SOON AS YOU HAVE NAME AND PHONE, IMMEDIATELY call detect_customer_type(phone_number, patient_name):
   - This is NOT OPTIONAL - you MUST call this function
   - Do this BEFORE asking any other questions
   - Do this BEFORE collecting email or appointment details
   - Say "Let me check if you're in our system" then call the function
   - Wait for the function result before continuing

STEP 3: PERSONALIZED RESPONSE BASED ON CUSTOMER TYPE
5a. FOR RETURNING CUSTOMERS: "Welcome back [Name]! I see you've visited us before. Would you like to book with [Previous Doctor] again?"
5b. FOR NEW CUSTOMERS: "Thank you [Name]. I'll need to collect some additional information to help you."

STEP 4: INFORMATION COLLECTION (Based on customer type)
6. Collect email address (skip if returning customer with email on file)
7. Collect appointment preferences (use previous preferences for returning customers)
   - Preferred date/time - ALWAYS convert relative dates to YYYY-MM-DD format
   - Department/specialty needed
   - Doctor preference (suggest previous doctor for returning customers)

STEP 5: APPOINTMENT VERIFICATION & BOOKING
8. CRITICAL: ALWAYS call check_appointment_availability() first to verify the time slot is available
9. If available: Proceed with booking by calling book_appointment() function
10. If not available: Suggest alternative times from the availability check results

CUSTOMER RECOGNITION RULES:
- NEVER proceed with appointment details until customer type is determined
- Always personalize the experience based on customer history
- Use previous preferences to speed up the process for returning customers
- Be explicit about recognizing returning customers to build trust

CUSTOMER TYPE RESPONSES:
- NEW CUSTOMER: "Thank you [Name]. I'll help you book your first appointment with us."
- RETURNING CUSTOMER: "Welcome back [Name]! I see you visited us before. Would you like to book with Dr. [Previous Doctor] again?"
- EXISTING CUSTOMER: "I have your information from our earlier conversation."

CRITICAL BUSINESS FLOW (SEQUENTIAL STEPS - DO NOT SKIP):
1. Customer calls → Greet and ask how to help
2. Collect name → Collect phone number
3. STOP! Say "Let me check if you're in our system"
4. MANDATORY: Call detect_customer_type(phone_number, patient_name) function NOW
5. Based on function result:
   - If returning customer: "Welcome back! I found your information. Email: [email]"
   - If new customer: "I'll help you book your first appointment"
6. Collect remaining info (skip email if returning customer)
7. ALWAYS call check_appointment_availability(date, time) FIRST
8. If available → Call book_appointment() to complete booking
9. If not available → Present alternatives and repeat availability check

EXAMPLE FLOW:
User: "I want to book an appointment"
You: "I'd be happy to help! What's your name?"
User: "John Doe"
You: "And your phone number?"
User: "555-1234"
You: "Let me check if you're in our system" → CALL detect_customer_type("555-1234", "John Doe")
Result: Returning customer with email john@email.com
You: "Welcome back John! I found your information. Your email is john@email.com. What type of appointment would you like?"

You have access to the following functions:
- detect_customer_type: MANDATORY - Check customer type and retrieve existing info after collecting phone number
- check_appointment_availability: Check if a time slot is available and get alternatives
- book_appointment: Book appointment with email confirmation AND calendar entry
- cancel_appointment: Cancel existing appointments
- log_call_information: Log call details for record keeping

Start every conversation with: "Hi! How are you? I'm Archana, your AI assistant from Renova Hospitals. How can I help you today?"

Speak naturally with contractions and natural rhythm."""
                }
            ],
            tools=enhanced_appointment_tools
        )

        # Create context aggregator for function calling support
        context_aggregator = llm.create_context_aggregator(context)

        # Create pipeline using RECOMMENDED PATTERN for Gemini Live with function calling
        pipeline = Pipeline([
            transport.input(),              # Audio input from client
            context_aggregator.user(),      # User context aggregation
            llm,                           # Gemini Multimodal Live processing (handles STT + LLM + TTS + Function Calling)
            transport.output(),            # Audio output to client
            context_aggregator.assistant() # Assistant context aggregation
        ])

        # Create task
        task = PipelineTask(
            pipeline,
            idle_timeout_secs=30
        )

        # Event handlers
        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            logger.info(f"Client connected: {session_id}")

            # Initialize call record for this session
            # Track call start time
            call_start_time = datetime.now()

            call_record = CallRecord(
                call_id=str(uuid.uuid4()),
                timestamp=call_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                caller_phone="Unknown",  # Will be updated when available
                duration_seconds=0,
                customer_type="unknown",
                customer_name="",
                customer_email="",
                call_type="appointment_inquiry",
                department_enquired="",
                doctor_enquired="",
                appointment_date="",
                appointment_time="",
                language_used="english",
                call_summary="Call initiated",
                resolution_status="pending",
                agent_notes="",
                session_id=session_id,
                hangup_reason=""
            )
            call_record.call_start_time = call_start_time  # Store for duration calculation
            session_call_records[session_id] = call_record

            # Start with initial LLM run to trigger greeting
            await task.queue_frames([LLMRunFrame()])

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            logger.info(f"Client disconnected: {session_id}")
            await cleanup_session(session_id, "completed", "Normal disconnection")

        @transport.event_handler("on_error")
        async def on_error(transport, error):
            logger.error(f"Transport error for session {session_id}: {error}")
            await cleanup_session(session_id, "error", f"Transport error: {str(error)}")

        async def cleanup_session(session_id: str, status: str = "completed", reason: str = ""):
            """Centralized session cleanup with error handling"""
            try:
                # Finalize and log the call record
                if session_id in session_call_records:
                    call_record = session_call_records[session_id]

                    # Calculate call duration
                    if hasattr(call_record, 'call_start_time'):
                        call_end_time = datetime.now()
                        duration = call_end_time - call_record.call_start_time
                        call_record.duration_seconds = int(duration.total_seconds())

                    call_record.resolution_status = status
                    call_record.call_summary = f"Call {status}. Duration: {call_record.duration_seconds}s. {reason}"

                    if reason:
                        call_record.hangup_reason = reason

                    # Log to CSV with error handling (convert CallRecord to dict)
                    try:
                        call_data_dict = {
                            'call_id': call_record.call_id,
                            'timestamp': call_record.timestamp,
                            'caller_phone': call_record.caller_phone,
                            'duration_seconds': call_record.duration_seconds,
                            'customer_type': call_record.customer_type,
                            'customer_name': call_record.customer_name,
                            'customer_email': call_record.customer_email,
                            'call_type': call_record.call_type,
                            'department_enquired': call_record.department_enquired,
                            'doctor_enquired': call_record.doctor_enquired,
                            'appointment_date': call_record.appointment_date,
                            'appointment_time': call_record.appointment_time,
                            'language_used': call_record.language_used,
                            'call_summary': call_record.call_summary,
                            'resolution_status': call_record.resolution_status,
                            'agent_notes': call_record.agent_notes,
                            'session_id': call_record.session_id,
                            'hangup_reason': call_record.hangup_reason
                        }
                        call_logger.log_call(call_data_dict)
                        logger.info(f"Call logged to CSV: {call_record.call_id}")
                    except Exception as e:
                        logger.error(f"Failed to log call to CSV: {e}")

                    # MANDATORY: Log to Google Sheets (silent, no customer notification)
                    if global_sheets_service:
                        try:
                            call_log_record = CallLogRecord(
                                call_id=call_record.call_id,
                                timestamp=call_record.timestamp,
                                phone=call_record.caller_phone,
                                name=call_record.customer_name,
                                duration=call_record.duration_seconds,
                                language=call_record.language_used,
                                call_type=call_record.call_type,
                                department=call_record.department_enquired,
                                doctor=call_record.doctor_enquired,
                                status=call_record.resolution_status,
                                resolution=call_record.call_summary,
                                notes=call_record.agent_notes or call_record.hangup_reason
                            )
                            global_sheets_service.log_call_record(call_log_record)
                            logger.info(f"MANDATORY: Call logged to Google Sheets: {call_record.call_id}")
                        except Exception as e:
                            logger.error(f"CRITICAL: Failed to log call to Google Sheets: {e}")
                            # Continue anyway - don't block session cleanup

                    # Remove from active sessions
                    del session_call_records[session_id]

                # Cancel task safely
                if hasattr(task, 'cancel'):
                    await task.cancel()

            except Exception as e:
                logger.error(f"Error during session cleanup: {e}")
                # Ensure session is removed even if logging fails
                session_call_records.pop(session_id, None)

        # Store session
        active_sessions[session_id] = task

        # Run pipeline with Windows-compatible runner and error handling
        runner = PipelineRunner(handle_sigint=False)
        try:
            await runner.run(task)
        except Exception as e:
            logger.error(f"Pipeline error for session {session_id}: {e}")
            await cleanup_session(session_id, "pipeline_error", f"Pipeline failure: {str(e)}")
            raise  # Re-raise to allow proper error propagation

    except Exception as e:
        logger.error(f"Bot error for session {session_id}: {e}")
        # Ensure session cleanup on any error
        try:
            await cleanup_session(session_id, "bot_error", f"Bot initialization/runtime error: {str(e)}")
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup for session {session_id}: {cleanup_error}")
    finally:
        # Cleanup session from active sessions
        if session_id in active_sessions:
            del active_sessions[session_id]
        logger.info(f"Session {session_id} fully cleaned up")

@app.get("/")
async def root():
    """Root endpoint."""
    print("Root endpoint accessed!")  # Debug log
    return {
        "message": "Pipecat Voice Server with Gmail Integration",
        "websocket_url": "ws://localhost:8090/ws",
        "status": "running",
        "active_sessions": len(active_sessions),
        "gmail_enabled": True
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "websocket_endpoint": "ws://localhost:8090/ws",
        "total_patients": len(patient_database),
        "active_calls": len(session_call_records)
    }

@app.get("/call-logs")
async def get_call_logs():
    """Get recent call logs from both CSV and Google Sheets."""
    try:
        # Read recent logs from CSV
        csv_logs = call_logger.get_recent_calls(limit=25)

        # Read recent logs from Google Sheets (if available)
        sheets_logs = []
        if global_sheets_service:
            try:
                sheets_logs = global_sheets_service.get_recent_call_logs(limit=25)
            except Exception as e:
                logger.error(f"Failed to get Sheets logs: {e}")

        return {
            "status": "success",
            "csv_logs": csv_logs,
            "sheets_logs": sheets_logs,
            "total_csv_logs": len(csv_logs),
            "total_sheets_logs": len(sheets_logs),
            "sheets_enabled": global_sheets_service is not None
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/patients")
async def get_patients():
    """Get patient database."""
    return {
        "status": "success",
        "patients": list(patient_database.values()),
        "total_patients": len(patient_database)
    }

@app.get("/patient/{phone}")
async def get_patient(phone: str):
    """Get specific patient information."""
    patient = get_patient_info(phone)
    if patient:
        return {"status": "success", "patient": patient}
    else:
        return {"status": "not_found", "message": "Patient not found"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, voice_id: str = "Charon"):
    """WebSocket endpoint using proper Pipecat transport."""
    print(f"=== WEBSOCKET LOG: Connection attempt received ===")
    print(f"=== WEBSOCKET LOG: Voice ID: {voice_id} ===")

    try:
        await websocket.accept()
        print(f"=== WEBSOCKET LOG: WebSocket accepted ===")
    except Exception as e:
        print(f"=== WEBSOCKET ERROR: Failed to accept: {e} ===")
        return

    # Generate session ID
    session_id = f"session-{len(active_sessions) + 1}"
    print(f"=== WEBSOCKET LOG: Session ID generated: {session_id} ===")
    logger.info(f"WebSocket connection accepted: {session_id} with voice: {voice_id}")

    try:
        # Run the bot using RECOMMENDED Pipecat pattern
        await run_bot(websocket, session_id, voice_id)

    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        logger.info(f"WebSocket connection closed: {session_id}")

if __name__ == "__main__":
    # Check required environment variables
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY environment variable is required")
        sys.exit(1)

    logger.info("Starting Pipecat server with proper transport pattern")
    logger.info("Using FastAPIWebsocketTransport as recommended in documentation")

    # Run the server
    uvicorn.run(
        app,
        host="127.0.0.1",  # Force IPv4 instead of localhost
        port=8090,
        log_level="info"
    )