#!/usr/bin/env python3

import os
import json
import logging
from typing import Dict, Any, Optional
from enum import Enum

# Set up logging
logger = logging.getLogger(__name__)

class SupportedLanguage(Enum):
    """Supported languages for the voice agent"""
    ENGLISH = "english"
    HINDI = "hindi"
    TELUGU = "telugu"

# Language prompts and responses
LANGUAGE_TEMPLATES = {
    SupportedLanguage.ENGLISH.value: {
        "greeting": "Hello! Welcome to Renova Hospitals. How can I help you today?",
        "name_request": "May I have your full name please?",
        "phone_request": "Could you please provide your phone number?",
        "email_request": "What is your email address?",
        "appointment_request": "I can help you book an appointment. Which doctor or department would you like to see?",
        "date_request": "What date would you prefer for your appointment?",
        "time_request": "What time would work best for you?",
        "confirmation": "Let me confirm your appointment details...",
        "availability_check": "Let me check the availability for that time slot...",
        "slot_unavailable": "I'm sorry, that time slot is not available. Here are some alternative times:",
        "appointment_confirmed": "Your appointment has been successfully booked. You will receive a confirmation email shortly.",
        "appointment_cancelled": "Your appointment has been successfully cancelled.",
        "cancellation_request": "To cancel your appointment, I need to verify some details. Please provide your name, doctor name, and appointment date and time.",
        "details_mismatch": "The details you provided don't match our records. Please verify and try again.",
        "goodbye": "Thank you for calling Renova Hospitals. Have a great day!",
        "error": "I apologize, but there seems to be an issue. Let me help you with that.",
        "clarification": "I didn't quite understand. Could you please repeat that?",
        "department_list": "We have the following departments: Cardiology, Neurology, Orthopedics, Pediatrics, General Medicine, Emergency, and more.",
        "visiting_hours": "Our visiting hours are from 9 AM to 6 PM, Monday through Saturday."
    },

    SupportedLanguage.HINDI.value: {
        "greeting": "नमस्ते! रेनोवा हॉस्पिटल में आपका स्वागत है। आज मैं आपकी कैसे सहायता कर सकता हूं?",
        "name_request": "कृपया अपना पूरा नाम बताएं?",
        "phone_request": "कृपया अपना फोन नंबर दें?",
        "email_request": "आपका ईमेल पता क्या है?",
        "appointment_request": "मैं आपको अपॉइंटमेंट बुक करने में मदद कर सकता हूं। आप किस डॉक्टर या विभाग से मिलना चाहते हैं?",
        "date_request": "आप किस तारीख को अपॉइंटमेंट चाहते हैं?",
        "time_request": "आपके लिए कौन सा समय सबसे अच्छा होगा?",
        "confirmation": "मुझे आपके अपॉइंटमेंट की जानकारी की पुष्टि करने दें...",
        "availability_check": "मुझे उस समय स्लॉट की उपलब्धता चेक करने दें...",
        "slot_unavailable": "खुशी है, वह समय स्लॉट उपलब्ध नहीं है। यहां कुछ वैकल्पिक समय हैं:",
        "appointment_confirmed": "आपका अपॉइंटमेंट सफलतापूर्वक बुक हो गया है। आपको जल्द ही एक कन्फर्मेशन ईमेल मिलेगा।",
        "appointment_cancelled": "आपका अपॉइंटमेंट सफलतापूर्वक रद्द कर दिया गया है।",
        "cancellation_request": "अपॉइंटमेंट रद्द करने के लिए, मुझे कुछ विवरणों की पुष्टि करनी होगी। कृपया अपना नाम, डॉक्टर का नाम, और अपॉइंटमेंट की तारीख और समय बताएं।",
        "details_mismatch": "आपके द्वारा दिए गए विवरण हमारे रिकॉर्ड से मेल नहीं खाते। कृपया सत्यापित करें और पुनः प्रयास करें।",
        "goodbye": "रेनोवा हॉस्पिटल्स को कॉल करने के लिए धन्यवाद। आपका दिन शुभ हो!",
        "error": "मुझे खेद है, कुछ समस्या लग रही है। मैं आपकी इसमें सहायता करूंगा।",
        "clarification": "मैं पूरी तरह समझ नहीं पाया। कृपया इसे दोहराएं?",
        "department_list": "हमारे पास निम्नलिखित विभाग हैं: कार्डियोलॉजी, न्यूरोलॉजी, ऑर्थोपेडिक्स, पीडियाट्रिक्स, जनरल मेडिसिन, इमरजेंसी, और अन्य।",
        "visiting_hours": "हमारे दर्शन का समय सोमवार से शनिवार सुबह 9 बजे से शाम 6 बजे तक है।"
    },

    SupportedLanguage.TELUGU.value: {
        "greeting": "నమస్కారం! రేనోవా హాస్పిటల్స్‌కు స్వాగతం. నేను ఈరోజు మీకు ఎలా సహాయం చేయగలను?",
        "name_request": "దయచేసి మీ పూర్తి పేరు చెప్పండి?",
        "phone_request": "దయచేసి మీ ఫోన్ నంబర్ ఇవ్వండి?",
        "email_request": "మీ ఇమెయిల్ చిరునామా ఏమిటి?",
        "appointment_request": "నేను మీకు అపాయింట్‌మెంట్ బుక్ చేయడంలో సహాయం చేయగలను. మీరు ఏ డాక్టర్ లేదా విభాగాన్ని చూడాలనుకుంటున్నారు?",
        "date_request": "మీరు ఏ తేదీని అపాయింట్‌మెంట్ కోసం ఇష్టపడతారు?",
        "time_request": "మీకు ఏ సమయం బాగుంటుంది?",
        "confirmation": "మీ అపాయింట్‌మెంట్ వివరాలను నేను ధృవీకరించనివ్వండి...",
        "availability_check": "ఆ సమయ స్లాట్ లభ్యతను నేను తనిఖీ చేయనివ్వండి...",
        "slot_unavailable": "క్షమించండి, ఆ సమయ స్లాట్ అందుబాటులో లేదు. ఇక్కడ కొన్ని ప్రత్యామ్నాయ సమయాలు ఉన్నాయి:",
        "appointment_confirmed": "మీ అపాయింట్‌మెంట్ విజయవంతంగా బుక్ చేయబడింది. మీకు త్వరలో ధృవీకరణ ఇమెయిల్ వస్తుంది.",
        "appointment_cancelled": "మీ అపాయింట్‌మెంట్ విజయవంతంగా రద్దు చేయబడింది.",
        "cancellation_request": "అపాయింట్‌మెంట్ రద్దు చేయడానికి, నేను కొన్ని వివరాలను ధృవీకరించాలి. దయచేసి మీ పేరు, డాక్టర్ పేరు, మరియు అపాయింట్‌మెంట్ తేదీ మరియు సమయం ఇవ్వండి.",
        "details_mismatch": "మీరు అందించిన వివరాలు మా రికార్డులతో సరిపోలలేదు. దయచేసి ధృవీకరించి మళ్లీ ప్రయత్నించండి.",
        "goodbye": "రేనోవా హాస్పిటల్స్‌కు కాల్ చేసినందుకు ధన్యవాదాలు. మీ రోజు మంచిగా గడవాలని కోరుకుంటున్నాను!",
        "error": "క్షమించండి, ఏదో సమస్య ఉన్నట్లు అనిపిస్తుంది. దానిలో నేను మీకు సహాయం చేస్తాను.",
        "clarification": "నేను పూర్తిగా అర్థం చేసుకోలేకపోయాను. దయచేసి మళ్లీ చెప్పండి?",
        "department_list": "మా వద్ద ఈ విభాగాలు ఉన్నాయి: కార్డియాలజీ, న్యూరాలజీ, ఆర్థోపెడిక్స్, పీడియాట్రిక్స్, జనరల్ మెడిసిన్, ఎమర్జెన్సీ, మరియు ఇతరాలు.",
        "visiting_hours": "మా దర్శన సమయాలు సోమవారం నుంచి శనివారం వరకు ఉదయం 9 గంటల నుంచి సాయంత్రం 6 గంటల వరకు."
    }
}

class LanguageManager:
    """Manages multi-language support for the voice agent"""

    def __init__(self):
        """Initialize the language manager"""
        self.current_language = SupportedLanguage.ENGLISH.value
        self.templates = LANGUAGE_TEMPLATES

    def set_language(self, language: str) -> bool:
        """Set the current language"""
        if language.lower() in [lang.value for lang in SupportedLanguage]:
            self.current_language = language.lower()
            logger.info(f"Language set to: {self.current_language}")
            return True
        else:
            logger.warning(f"Unsupported language: {language}")
            return False

    def get_text(self, key: str, language: str = None) -> str:
        """Get text in the specified language"""
        lang = language or self.current_language

        if lang in self.templates and key in self.templates[lang]:
            return self.templates[lang][key]

        # Fallback to English if key not found
        if key in self.templates[SupportedLanguage.ENGLISH.value]:
            logger.warning(f"Key '{key}' not found in {lang}, using English fallback")
            return self.templates[SupportedLanguage.ENGLISH.value][key]

        logger.error(f"Key '{key}' not found in any language")
        return f"[Missing text: {key}]"

    def detect_language_preference(self, user_input: str) -> str:
        """Simple language detection based on keywords"""
        user_input_lower = user_input.lower()

        # Hindi keywords
        hindi_keywords = [
            'नमस्ते', 'धन्यवाद', 'कृपया', 'हां', 'नहीं', 'डॉक्टर', 'अपॉइंटमेंट',
            'hindi', 'हिंदी', 'मुझे हिंदी', 'हिंदी में'
        ]

        # Telugu keywords
        telugu_keywords = [
            'నమస్కారం', 'ధన్యవాదాలు', 'దయచేసి', 'అవును', 'లేదు', 'డాక్టర్', 'అపాయింట్మెంట్',
            'telugu', 'తెలుగు', 'తెలుగులో', 'నాకు తెలుగు'
        ]

        # Check for language indicators
        for keyword in hindi_keywords:
            if keyword in user_input_lower:
                return SupportedLanguage.HINDI.value

        for keyword in telugu_keywords:
            if keyword in user_input_lower:
                return SupportedLanguage.TELUGU.value

        # Default to English
        return SupportedLanguage.ENGLISH.value

    def get_system_instruction_for_language(self, language: str) -> str:
        """Get system instructions for specific language"""
        base_instruction = f"""
You are a helpful voice assistant for Renova Hospitals. You are currently communicating in {language.title()}.

CRITICAL LANGUAGE RULES:
1. Respond ONLY in {language.title()} language
2. Names, email addresses, phone numbers, and medical terms MUST remain in English
3. Doctor names MUST be in English (e.g., "Dr. Sharma", not translated)
4. Department names should be in English for clarity
5. Dates and times can be spoken in {language.title()} but written in English format (YYYY-MM-DD, HH:MM)

WHAT TO KEEP IN ENGLISH:
- Patient names (e.g., "John Smith")
- Doctor names (e.g., "Dr. Patel")
- Email addresses (e.g., "john@example.com")
- Phone numbers
- Department names (e.g., "Cardiology", "Neurology")
- Medical terms when appropriate

WHAT TO TRANSLATE:
- Greetings and conversation
- Instructions and questions
- Confirmations and responses
- General hospital information
"""

        if language == SupportedLanguage.HINDI.value:
            return base_instruction + """
HINDI SPECIFIC:
- Use respectful forms (आप, जी, कृपया)
- Keep sentences clear and simple
- Use common Hindi medical vocabulary where appropriate
"""
        elif language == SupportedLanguage.TELUGU.value:
            return base_instruction + """
TELUGU SPECIFIC:
- Use respectful forms (మీరు, దయచేసి)
- Keep sentences clear and simple
- Use common Telugu medical vocabulary where appropriate
"""
        else:
            return base_instruction

    def format_appointment_confirmation(self, patient_name: str, doctor_name: str,
                                      date: str, time: str, language: str = None) -> str:
        """Format appointment confirmation in the specified language"""
        lang = language or self.current_language

        if lang == SupportedLanguage.HINDI.value:
            return f"आपका अपॉइंटमेंट बुक हो गया है:\nमरीज़: {patient_name}\nडॉक्टर: {doctor_name}\nतारीख: {date}\nसमय: {time}\nआपको ईमेल कन्फर्मेशन मिलेगा।"
        elif lang == SupportedLanguage.TELUGU.value:
            return f"మీ అపాయింట్‌మెంట్ బుక్ చేయబడింది:\nపేషెంట్: {patient_name}\nడాక్టర్: {doctor_name}\nతేదీ: {date}\nసమయం: {time}\nమీకు ఇమెయిల్ కన్ఫర్మేషన్ వస్తుంది।"
        else:
            return f"Your appointment is confirmed:\nPatient: {patient_name}\nDoctor: {doctor_name}\nDate: {date}\nTime: {time}\nYou will receive an email confirmation."

    def format_alternative_slots(self, alternatives: list, language: str = None) -> str:
        """Format alternative time slots in the specified language"""
        lang = language or self.current_language

        if not alternatives:
            return self.get_text("error", lang)

        formatted_alternatives = []
        for alt in alternatives:
            formatted_alternatives.append(alt.get('formatted', f"{alt['date']} at {alt['time']}"))

        if lang == SupportedLanguage.HINDI.value:
            intro = "यहां कुछ वैकल्पिक समय हैं:"
            alternatives_text = "\n".join([f"• {alt}" for alt in formatted_alternatives])
            return f"{intro}\n{alternatives_text}"
        elif lang == SupportedLanguage.TELUGU.value:
            intro = "ఇక్కడ కొన్ని ప్రత్యామ్నాయ సమయాలు ఉన్నాయి:"
            alternatives_text = "\n".join([f"• {alt}" for alt in formatted_alternatives])
            return f"{intro}\n{alternatives_text}"
        else:
            intro = "Here are some alternative times:"
            alternatives_text = "\n".join([f"• {alt}" for alt in formatted_alternatives])
            return f"{intro}\n{alternatives_text}"

# Global language manager instance
_language_manager = None

def get_language_manager() -> LanguageManager:
    """Get a singleton LanguageManager instance"""
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager

def get_localized_text(key: str, language: str = None) -> str:
    """Quick function to get localized text"""
    manager = get_language_manager()
    return manager.get_text(key, language)

def detect_user_language(user_input: str) -> str:
    """Quick function to detect user language"""
    manager = get_language_manager()
    return manager.detect_language_preference(user_input)

# Test function
if __name__ == "__main__":
    # Test the language manager
    manager = LanguageManager()

    # Test language detection
    print("Testing language detection:")
    print(f"'Hello' -> {manager.detect_language_preference('Hello')}")
    print(f"'नमस्ते' -> {manager.detect_language_preference('नमस्ते')}")
    print(f"'నమస్కారం' -> {manager.detect_language_preference('నమస్కారం')}")

    # Test text retrieval
    print("\nTesting text retrieval:")
    for lang in [SupportedLanguage.ENGLISH.value, SupportedLanguage.HINDI.value, SupportedLanguage.TELUGU.value]:
        print(f"{lang.title()}: {manager.get_text('greeting', lang)}")

    # Test appointment confirmation
    print("\nTesting appointment confirmation:")
    confirmation = manager.format_appointment_confirmation(
        "John Smith", "Dr. Patel", "2024-12-25", "10:00 AM", SupportedLanguage.HINDI.value
    )
    print(confirmation)