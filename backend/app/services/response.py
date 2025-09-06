from ..config import get_settings
from .store import get_email, add_response
from datetime import datetime

PROMPT_TEMPLATE = (
    "You are a professional, empathetic customer support assistant.\n"
    "Draft a clear, concise, friendly reply to the customer email using the details and context.\n"
    "If the sentiment is negative, begin with an acknowledgement of their frustration.\n"
    "Do NOT hallucinate facts; if missing information, politely ask for it.\n\n"
    "Email Subject: {subject}\n"
    "Sentiment: {sentiment}\n"
    "Priority: {priority}\n"
    "Extracted Phones: {phones}\n"
    "Extracted Emails: {emails}\n"
    "Key Phrases: {phrases}\n\n"
    "Customer Email:\n"
    "----- BEGIN EMAIL -----\n{body}\n----- END EMAIL -----\n\n"
    "Relevant Knowledge Base Context:\n{context}\n\n"
    "Reply Draft (professional, empathetic):\n"
)

# In real implementation replace with Gemini API call

def generate_draft(email_id: str):
    email_doc = get_email(email_id)
    if not email_doc:
        return None
    extraction = email_doc.get('extraction') or {}
    context = "(RAG not yet implemented)"
    prompt = PROMPT_TEMPLATE.format(
        subject=email_doc.get('subject',''),
        sentiment=email_doc.get('sentiment','neutral'),
        priority=email_doc.get('priority','not_urgent'),
        phones=extraction.get('phones', []),
        emails=extraction.get('emails', []),
        phrases=extraction.get('key_phrases', []),
        body=email_doc.get('body','')[:4000],
        context=context
    )
    
    # Enhanced empathetic response generation
    sender = email_doc.get('sender', 'valued customer')
    subject = email_doc.get('subject', '')
    sentiment = email_doc.get('sentiment', 'neutral')
    priority = email_doc.get('priority', 'not_urgent')
    key_phrases = extraction.get('key_phrases', [])
    
    # Opening based on sentiment and urgency
    if sentiment == 'negative' or priority == 'urgent':
        if 'cannot' in subject.lower() or 'unable' in subject.lower() or 'down' in subject.lower():
            opening = f"Dear {sender.split('@')[0]},\n\nI sincerely apologize for the inconvenience you're experiencing. I understand how frustrating it must be when you're unable to access our services, and I want to assure you that resolving this issue is my top priority."
        elif 'billing' in subject.lower() or 'charged' in subject.lower():
            opening = f"Dear {sender.split('@')[0]},\n\nThank you for bringing this billing concern to our attention. I understand how concerning unexpected charges can be, and I want to personally ensure we resolve this matter quickly and to your satisfaction."
        else:
            opening = f"Dear {sender.split('@')[0]},\n\nI understand your concern and truly appreciate you taking the time to reach out to us. Your experience matters greatly to us, and I'm here to help resolve this issue promptly."
    else:
        opening = f"Dear {sender.split('@')[0]},\n\nThank you for contacting our support team. I'm delighted to assist you with your inquiry today."
    
    # Main content based on key phrases and subject
    main_content = ""
    if any(phrase in ['login', 'access', 'password', 'account'] for phrase in key_phrases):
        main_content = "I've reviewed your account access issue and will prioritize getting you back into your account immediately. Our technical team has identified several effective solutions for login-related concerns.\n\nTo expedite the resolution process, I'll be sending you a secure password reset link within the next few minutes. Please check both your inbox and spam folder. If you continue to experience difficulties, I'm also available for a brief phone call to walk you through the process step-by-step."
    elif any(phrase in ['billing', 'charged', 'payment', 'refund'] for phrase in key_phrases):
        main_content = "I've immediately escalated your billing inquiry to our specialized billing department for review. We take billing accuracy very seriously and will conduct a thorough investigation of your account charges.\n\nYou can expect a detailed breakdown of all charges along with any necessary corrections within 24 hours. If a refund is warranted, we'll process it immediately and provide you with a reference number for tracking."
    elif any(phrase in ['integration', 'api', 'third-party'] for phrase in key_phrases):
        main_content = "I'm excited to help you explore our integration capabilities! Our platform supports extensive third-party integrations, including comprehensive CRM connectivity.\n\nI'll be sending you our detailed integration guide along with API documentation within the next hour. Our technical team can also schedule a personalized demo to show you exactly how our integrations can streamline your workflow and enhance your business operations."
    elif any(phrase in ['pricing', 'subscription', 'plan'] for phrase in key_phrases):
        main_content = "I'd be happy to provide you with comprehensive pricing information tailored to your specific needs. Our flexible subscription plans are designed to grow with your business.\n\nI'll prepare a customized pricing breakdown that includes all available features and any current promotional offers. Additionally, I can arrange a consultation with our solutions specialist to ensure you select the perfect plan for your requirements."
    else:
        main_content = f"I've carefully reviewed your inquiry regarding {', '.join(key_phrases[:3]) if key_phrases else 'your request'} and want to provide you with the most comprehensive assistance possible.\n\nOur team is committed to delivering exceptional service, and I'll personally ensure your needs are met. I'll be following up with detailed information and next steps within the next few hours."
    
    # Closing based on urgency
    if priority == 'urgent':
        closing = "Given the urgent nature of your request, I'm treating this with the highest priority. You can expect an update from me within the next 2 hours, and I'll remain available throughout the resolution process.\n\nIf you need immediate assistance, please don't hesitate to call our priority support line, and mention ticket reference #SP-" + email_id[:8].upper() + ".\n\nWarm regards,\nCustomer Success Team\nAI Communication Assistant"
    else:
        closing = "I'm committed to ensuring your complete satisfaction with our resolution. You can expect a follow-up from me within 24 hours with either a complete solution or a detailed progress update.\n\nPlease don't hesitate to reach out if you have any additional questions or concerns in the meantime.\n\nBest regards,\nCustomer Success Team\nAI Communication Assistant\n\nP.S. Your feedback helps us improve our service. We'd love to hear about your experience once we've resolved your inquiry."
    
    draft = f"{opening}\n\n{main_content}\n\n{closing}"
    
    add_response(email_doc['id'], draft, model='empathetic-ai')
    return draft
