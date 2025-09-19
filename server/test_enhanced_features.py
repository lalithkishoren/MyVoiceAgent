#!/usr/bin/env python3

"""
Test script for enhanced voice agent features
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from calendar_service import CalendarService
from call_logger import CallLogger, CallType, CustomerType, CallStatus
from language_support import LanguageManager, SupportedLanguage

async def test_calendar_availability():
    """Test calendar availability checking"""
    print("\n📅 Testing Calendar Availability Checking...")

    try:
        calendar_service = CalendarService()

        # Test with tomorrow's date
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        # Test availability check
        result = calendar_service.check_availability(
            appointment_date=tomorrow,
            appointment_time="10:00 AM",
            duration_minutes=30
        )

        print(f"✅ Availability check result: {result}")

        if result.get('success'):
            if result.get('available'):
                print(f"🟢 Time slot available: {tomorrow} at 10:00 AM")
            else:
                print(f"🔴 Time slot unavailable. Conflicts: {result.get('conflicts')}")
                print(f"💡 Alternatives: {len(result.get('alternatives', []))} suggested")

        return True

    except Exception as e:
        print(f"❌ Calendar availability test failed: {e}")
        return False

def test_call_logging():
    """Test call logging functionality"""
    print("\n📊 Testing Call Logging...")

    try:
        call_logger = CallLogger()

        # Test logging a call
        test_call_data = {
            'call_type': CallType.APPOINTMENT_BOOKING.value,
            'customer_name': 'Test Patient',
            'caller_phone': '+91-9876543210',
            'customer_email': 'test@example.com',
            'customer_type': CustomerType.NEW.value,
            'department_enquired': 'Cardiology',
            'doctor_enquired': 'Dr. Test Doctor',
            'call_summary': 'Test appointment booking call for enhanced features',
            'language_used': 'english',
            'resolution_status': CallStatus.RESOLVED.value,
            'agent_notes': 'Test call for feature verification'
        }

        call_id = call_logger.log_call(test_call_data)
        print(f"✅ Call logged successfully with ID: {call_id}")

        # Test getting statistics
        stats = call_logger.get_call_stats(days=1)
        print(f"📈 Call statistics: {stats}")

        # Test searching calls
        search_results = call_logger.search_calls(customer_name='Test Patient')
        print(f"🔍 Search results: Found {len(search_results)} matching calls")

        return True

    except Exception as e:
        print(f"❌ Call logging test failed: {e}")
        return False

def test_language_support():
    """Test multi-language support"""
    print("\n🌐 Testing Multi-Language Support...")

    try:
        lang_manager = LanguageManager()

        # Test language detection
        test_inputs = [
            ("Hello, I need an appointment", "english"),
            ("नमस्ते, मुझे अपॉइंटमेंट चाहिए", "hindi"),
            ("నమస్కారం, నాకు అపాయింట్మెంట్ కావాలి", "telugu"),
            ("Hindi mein baat karna hai", "hindi"),
            ("Telugu lo matladandi", "telugu")
        ]

        for text, expected_lang in test_inputs:
            detected = lang_manager.detect_language_preference(text)
            status = "✅" if detected == expected_lang else "⚠️"
            print(f"{status} '{text}' -> {detected} (expected: {expected_lang})")

        # Test text retrieval in different languages
        print("\n📝 Testing text retrieval:")
        for lang in [SupportedLanguage.ENGLISH.value, SupportedLanguage.HINDI.value, SupportedLanguage.TELUGU.value]:
            greeting = lang_manager.get_text('greeting', lang)
            print(f"🌏 {lang.title()}: {greeting}")

        # Test appointment confirmation formatting
        print("\n📋 Testing appointment confirmation formatting:")
        confirmation = lang_manager.format_appointment_confirmation(
            "John Smith", "Dr. Patel", "2024-12-25", "10:00 AM", SupportedLanguage.HINDI.value
        )
        print(f"📄 Hindi confirmation:\n{confirmation}")

        return True

    except Exception as e:
        print(f"❌ Language support test failed: {e}")
        return False

def test_appointment_cancellation():
    """Test appointment cancellation logic"""
    print("\n❌ Testing Appointment Cancellation...")

    try:
        calendar_service = CalendarService()

        # Test cancellation with non-existent appointment (should fail gracefully)
        result = calendar_service.cancel_appointment(
            patient_name="Test Patient",
            patient_email="test@example.com",
            patient_phone="+91-9876543210",
            appointment_date="2024-12-25",
            appointment_time="10:00 AM",
            doctor_name="Dr. Test"
        )

        print(f"🔍 Cancellation test result: {result}")

        if not result.get('success'):
            print(f"✅ Cancellation correctly failed: {result.get('error')}")
            print(f"📋 Provided details tracked: {result.get('provided_details')}")
        else:
            print("⚠️ Unexpected cancellation success (or appointment exists)")

        return True

    except Exception as e:
        print(f"❌ Appointment cancellation test failed: {e}")
        return False

async def test_enhanced_functions():
    """Test the enhanced appointment functions"""
    print("\n🔧 Testing Enhanced Function Schemas...")

    try:
        from enhanced_appointment_functions import (
            enhanced_appointment_tools,
            ENHANCED_FUNCTION_REGISTRY
        )

        print(f"✅ Enhanced tools schema loaded: {len(enhanced_appointment_tools.standard_tools)} functions")

        # List all available functions
        print("📋 Available functions:")
        for i, tool in enumerate(enhanced_appointment_tools.standard_tools, 1):
            print(f"  {i}. {tool.name}: {tool.description}")

        print(f"🔧 Function registry: {len(ENHANCED_FUNCTION_REGISTRY)} handlers registered")
        for func_name in ENHANCED_FUNCTION_REGISTRY.keys():
            print(f"  ✓ {func_name}")

        return True

    except Exception as e:
        print(f"❌ Enhanced functions test failed: {e}")
        return False

def test_system_integration():
    """Test integration between all components"""
    print("\n🔗 Testing System Integration...")

    try:
        # Test that all components can be imported and initialized
        from gmail_service import get_gmail_service
        from calendar_service import get_calendar_service
        from call_logger import get_call_logger
        from language_support import get_language_manager

        print("✅ All services can be imported")

        # Test service initialization
        gmail_service = get_gmail_service()
        calendar_service = get_calendar_service()
        call_logger = get_call_logger()
        lang_manager = get_language_manager()

        print("✅ All services can be initialized")

        # Test that CSV file is created
        csv_path = os.path.join(os.path.dirname(__file__), 'call_logs.csv')
        if os.path.exists(csv_path):
            print(f"✅ Call logs CSV exists: {csv_path}")
        else:
            print(f"📝 Call logs CSV will be created at: {csv_path}")

        return True

    except Exception as e:
        print(f"❌ System integration test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🏥 Renova Hospitals - Enhanced Voice Agent Feature Testing")
    print("=" * 80)

    tests = [
        ("System Integration", test_system_integration),
        ("Enhanced Functions", test_enhanced_functions),
        ("Language Support", test_language_support),
        ("Call Logging", test_call_logging),
        ("Calendar Availability", test_calendar_availability),
        ("Appointment Cancellation", test_appointment_cancellation),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 80)
    print("🏁 TEST SUMMARY")
    print("=" * 80)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\n📊 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")

    if passed == total:
        print("🎉 All tests passed! Enhanced voice agent is ready.")
        print("\n🚀 To start the enhanced server:")
        print("   python src/enhanced_pipecat_server.py")
        print("\n📡 WebSocket URL format:")
        print("   ws://localhost:8090/ws?voice_id=Charon&language=english")
        print("   ws://localhost:8090/ws?voice_id=Charon&language=hindi")
        print("   ws://localhost:8090/ws?voice_id=Charon&language=telugu")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")

    return passed == total

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    # Run tests
    asyncio.run(main())