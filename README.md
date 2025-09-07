# AI-Powered Communication Assistant

An intelligent email management system that automatically fetches, analyzes, categorizes, and generates responses for support emails using Gmail API integration and AI-powered sentiment analysis.

## Features

- Real-time Gmail inbox integration with OAuth2 authentication
- Intelligent email categorization (Support, Urgent, Billing, Technical, etc.)
- Sentiment analysis and priority scoring
- Automated response generation
- Interactive dashboard with filtering and analytics
- Fresh email detection with customizable time windows

## Architecture

- **Backend**: FastAPI with RESTful API endpoints
- **Frontend**: Streamlit interactive dashboard
- **Email Integration**: Gmail API with OAuth2 authentication
- **AI Processing**: Sentiment analysis, urgency detection, and information extraction
- **Storage**: In-memory data store with persistence options

## Prerequisites

- Python 3.8 or higher
- Gmail account with API access enabled
- Google Cloud Console project with Gmail API enabled

## Installation and Setup

### 1. Clone Repository and Setup Virtual Environment

```bash
# Clone the repository
git clone <repository-url>
cd aunstop-urgent

# Create virtual environment
python -m venv unstop

# Activate virtual environment
# On Windows:
unstop\Scripts\activate
# On macOS/Linux:
source unstop/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Environment Configuration

```bash
# Copy the sample environment file
copy .env.example .env

# Edit .env file with your actual credentials
```

### 4. Gmail API Setup

#### Step 1: Create Google Cloud Project
1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

#### Step 2: Create OAuth2 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Select "Desktop application" as the application type
4. Provide a name for your OAuth2 client
5. Download the credentials JSON file

#### Step 3: Configure Credentials
1. Rename the downloaded file to `credentials.json`
2. Place it in the `backend/` directory
3. Update the `.env` file with your Gmail address

### 5. SMTP Configuration (Optional)

For sending email replies, configure SMTP settings:
1. Enable 2-factor authentication on your Gmail account
2. Generate an app-specific password
3. Update SMTP credentials in `.env` file

### 6. Gemini AI Configuration (Optional)

For enhanced AI responses:
1. Obtain Gemini API key from Google AI Studio
2. Add the API key to your `.env` file

## Running the Application

### Start the Backend Server

```bash
# Navigate to backend directory
cd backend

# Start FastAPI server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

### Start the Dashboard

```bash
# Navigate to dashboard directory
cd dashboard

# Start Streamlit application
streamlit run app.py --server.port 8501
```

The dashboard will be available at: http://localhost:8501

## API Endpoints

### Authentication and Health
- `GET /health` - Health check endpoint

### Email Management
- `GET /emails/filters` - Get available email category filters
- `POST /emails/load_inbox` - Fetch fresh emails from Gmail inbox
- `GET /emails/` - List all stored emails with filtering options
- `GET /emails/{email_id}` - Get specific email details
- `POST /emails/{email_id}/draft` - Generate response draft for email
- `POST /emails/{email_id}/send` - Send reply to email

### Data Management
- `POST /emails/clear` - Clear all stored email data

## Configuration Options

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `CSV_PATH` | Path to sample CSV data | No | `68b1acd44f393_Sample_Support_Emails_Dataset.csv` |
| `ALLOWED_ORIGINS` | CORS allowed origins | No | `*` |
| `GMAIL_USER` | Gmail account email | Yes | - |
| `GMAIL_CREDENTIALS_PATH` | Path to OAuth2 credentials | Yes | `credentials.json` |
| `GMAIL_TOKEN_PATH` | Path to store OAuth2 tokens | No | `token.json` |
| `SMTP_HOST` | SMTP server hostname | No | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | No | `587` |
| `SMTP_USER` | SMTP username | No | - |
| `SMTP_PASSWORD` | SMTP app-specific password | No | - |
| `GEMINI_API_KEY` | Google Gemini AI API key | No | - |

### Email Categories

The system automatically categorizes emails into:
- **Support**: General customer support queries
- **Query**: Questions and information requests  
- **Request**: Feature requests and service requests
- **Urgent**: Time-sensitive communications
- **Help**: Assistance requests
- **Billing**: Payment and billing inquiries
- **Technical**: Technical issues and bug reports
- **Account**: Account-related communications

## Usage

### Dashboard Features

1. **Email Filtering**: Select category filters to view specific types of emails
2. **Fresh Email Loading**: Fetch the latest emails from your Gmail inbox
3. **Email Analysis**: View sentiment analysis, priority scoring, and extracted information
4. **Response Generation**: Generate AI-powered response drafts
5. **Bulk Operations**: Manage multiple emails efficiently

### API Usage Examples

```python
import requests

# Fetch fresh emails
response = requests.post("http://localhost:8000/emails/load_inbox?filter_category=urgent&limit=50")

# Get all emails
emails = requests.get("http://localhost:8000/emails/")

# Generate response draft
draft = requests.post("http://localhost:8000/emails/123/draft")
```

## Troubleshooting

### Common Issues

1. **Gmail API Authentication Errors**
   - Ensure credentials.json is properly configured
   - Verify Gmail API is enabled in Google Cloud Console
   - Check that OAuth2 consent screen is configured

2. **No Emails Found**
   - Verify Gmail account has recent emails matching filter criteria
   - Check that OAuth2 authentication completed successfully
   - Ensure proper IMAP access permissions

3. **SMTP Send Errors**
   - Verify app-specific password is correctly configured
   - Ensure 2-factor authentication is enabled on Gmail account
   - Check SMTP server settings

### Logs and Debugging

- Backend logs are displayed in the terminal running the FastAPI server
- Streamlit logs are shown in the dashboard terminal
- Check browser console for frontend errors

## Technical Implementation

### AI and Language Models

#### Language Models Used
1. **Google Gemini API** (Optional Enhancement)
   - Used for advanced response generation when API key is provided
   - Fallback to rule-based responses when not configured
   - Context-aware email reply generation

2. **Rule-Based NLP Processing** (Core Implementation)
   - **Sentiment Analysis**: Keyword-based sentiment detection (positive, negative, neutral)
   - **Urgency Detection**: Pattern matching for urgent keywords (urgent, asap, critical, emergency)
   - **Information Extraction**: Regex-based extraction of emails, phone numbers, key phrases
   - **Priority Scoring**: Mathematical scoring based on sentiment + urgency (urgent=5, negative=2 points)

### Email Fetching and Processing

#### Gmail API Integration
1. **OAuth2 Authentication Flow**
   - Desktop application credentials (not service account)
   - Local server callback for authorization
   - Token persistence for seamless re-authentication

2. **Email Fetching Logic**
   ```python
   # Natural inbox search without timestamp restrictions
   final_query = f'in:inbox ({search_query})'
   
   # Fetches 50 emails naturally ordered newest to oldest
   maxResults=50  # Configurable limit
   ```

3. **Smart Category Filtering**
   - Keyword-based categorization using subject line analysis
   - 8 predefined categories with multiple keywords each
   - Dynamic query building: `subject:"support" OR subject:"urgent" OR ...`

4. **Email Processing Pipeline**
   - Fetch message IDs from Gmail API
   - Retrieve full message details (headers, body, attachments)
   - Extract and decode base64 email body content
   - Parse email metadata (sender, subject, date, message-ID)
   - Apply NLP analysis (sentiment, urgency, information extraction)
   - Store in memory with category tagging

#### Sorting and Ordering
- **Gmail Natural Order**: API returns emails newest first by default
- **No Manual Sorting**: Preserves Gmail's chronological ordering
- **Timestamp Processing**: Converts email dates to UTC for consistent handling
- **Priority Scoring**: Mathematical ranking based on urgency + sentiment analysis

### User Interface Features

#### Dashboard Enhancements
1. **Visual Indicators and Emojis**
   ```python
   # Priority indicators
   "🔴" for urgent emails
   "🟡" for normal priority  
   "🟢" for low priority
   
   # Sentiment indicators
   "😊" for positive sentiment
   "😐" for neutral sentiment  
   "😞" for negative sentiment
   
   # Category badges
   "🚨 URGENT", "💬 SUPPORT", "❓ QUERY", "🔧 TECHNICAL"
   ```

2. **Interactive Filtering**
   - Dropdown category selection with real-time filtering
   - Multi-category support ("all" vs specific categories)
   - Live email count updates

3. **Real-Time Status Updates**
   - Loading spinners during email fetch operations
   - Success/error notifications with detailed feedback
   - Progress indicators for bulk operations

#### Advanced UI Components
1. **Email Cards with Rich Metadata**
   - Sender information with domain extraction
   - Timestamp with relative time display
   - Subject highlighting with truncation
   - Expandable body content with formatting preservation

2. **Response Generation Interface**
   - AI-powered draft generation with context awareness
   - Editable response templates
   - Send functionality with SMTP integration
   - Response history tracking

3. **Analytics Dashboard**
   - Email volume metrics by category
   - Sentiment distribution charts
   - Response time analytics
   - Priority queue visualization

### Data Processing Pipeline

#### Email Analysis Workflow
1. **Content Extraction**
   - HTML/Plain text body parsing
   - Attachment detection and listing
   - Header analysis for routing information

2. **NLP Processing Chain**
   ```python
   # Sentiment analysis
   sentiment = simple_sentiment(email_body)
   
   # Urgency detection  
   urgency, reason = urgency(email_body + subject)
   
   # Information extraction
   phones, emails, phrases = extract_info(email_body)
   
   # Priority calculation
   priority_score = (5 if urgent else 0) + (2 if negative else 0)
   ```

3. **Category Assignment**
   - Multi-keyword matching per category
   - Best-match algorithm for overlapping categories
   - Fallback to "general" category for unmatched emails

#### Response Generation
1. **Context-Aware Generation**
   - Email content analysis for response relevance
   - Sender information integration
   - Category-specific response templates

2. **Multi-Paragraph Structure**
   - Acknowledgment paragraph
   - Solution/Information paragraph  
   - Next steps/Follow-up paragraph
   - Professional closing

### Performance Optimizations

#### Caching and Storage
- **In-Memory Storage**: Fast access with optional persistence
- **Duplicate Detection**: Message-ID based deduplication
- **Batch Processing**: Efficient bulk email operations

#### API Rate Limiting
- **Gmail API Quotas**: Respectful API usage within limits
- **Retry Logic**: Exponential backoff for failed requests
- **Error Handling**: Graceful degradation on API failures

### Security Implementation

#### Authentication Security
- **OAuth2 Flow**: Secure token-based authentication
- **Token Encryption**: Secure storage of refresh tokens
- **Scope Limitation**: Read-only Gmail access by default

#### Data Protection
- **No Persistent Storage**: Emails stored in memory only
- **Environment Variables**: Sensitive credentials via .env files
- **Input Sanitization**: Protection against injection attacks



## Development

### Project Structure

```
aunstop-urgent/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Configuration management
│   │   ├── models.py            # Data models
│   │   ├── routes/
│   │   │   └── emails.py        # Email-related API endpoints
│   │   └── services/
│   │       ├── email_fetch.py   # Gmail API integration
│   │       ├── email_send.py    # SMTP email sending
│   │       ├── response.py      # AI response generation
│   │       ├── store.py         # Data storage management
│   │       └── nlp.py           # Natural language processing
│   ├── requirements.txt         # Python dependencies
│   └── credentials.json         # Gmail OAuth2 credentials
├── dashboard/
│   └── app.py                   # Streamlit dashboard application
├── .env                         # Environment configuration
├── .env.example                 # Sample environment file
└── README.md                    # This file
```

### Adding New Features

1. **New Email Filters**: Modify `FILTER_KEYWORDS` in `email_fetch.py`
2. **Custom AI Models**: Extend `nlp.py` with additional analysis functions
3. **New API Endpoints**: Add routes in `backend/app/routes/`
4. **Dashboard Enhancements**: Modify `dashboard/app.py`

### Algorithm Details

#### Email Categorization Algorithm
```python
FILTER_KEYWORDS = {
    "support": ["support", "customer support", "tech support", "help desk"],
    "urgent": ["urgent", "asap", "immediately", "critical", "emergency"],
    "billing": ["billing", "payment", "invoice", "refund", "charge"],
    # ... more categories
}

# Multi-keyword matching with OR logic
query_parts = [f'subject:"{keyword}"' for keyword in category_keywords]
search_query = ' OR '.join(query_parts)
```

#### Priority Scoring Formula
```python
priority_score = (5 if urgency == 'urgent' else 0) + (2 if sentiment == 'negative' else 0)
# Results in scores: 0 (normal), 2 (negative), 5 (urgent), 7 (urgent + negative)
```

## License

This project is developed for educational and hackathon purposes.

## Data Models

### Email Object Structure
```python
{
    "message_id": "unique_identifier",
    "subject": "email_subject_line", 
    "sender": "sender@domain.com",
    "body": "email_content_text",
    "received_at": "2025-09-07T12:00:00Z",
    "sentiment": "positive|negative|neutral",
    "priority": "urgent|normal|low", 
    "priority_score": 0-7,
    "matched_category": "support|urgent|billing|etc",
    "extraction": {
        "phones": ["phone_numbers_found"],
        "emails": ["email_addresses_found"], 
        "key_phrases": ["important_phrases"],
        "sentiment": "analysis_result",
        "urgency_reason": "why_marked_urgent"
    },
    "status": "pending|processed|replied"
}
```

### Response Object Structure  
```python
{
    "email_id": "reference_to_email",
    "draft": "generated_response_text",
    "model": "gemini|rule_based", 
    "created_at": "2025-09-07T12:00:00Z",
    "final": "final_sent_response"
}
```
