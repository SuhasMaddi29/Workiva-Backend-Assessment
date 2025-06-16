# AI API Integration Backend

A FastAPI-based backend application that integrates with OpenAI's GPT-3.5-turbo model, providing a RESTful API for AI interactions with conversation logging capabilities.

## Features

- **REST API Design**: Clean API endpoints with proper validation and error handling
- **OpenAI Integration**: Secure integration with OpenAI's GPT-3.5-turbo model
- **Conversation Logging**: Automatic logging of all conversations to SQLite database
- **Input Validation**: Comprehensive validation with detailed error messages
- **Error Handling**: Specific error codes for different failure scenarios

## Project Structure

```
ai-api-integration-backend/
├── config/
│   └── settings.py          # Application configuration
├── controllers/
│   ├── ai_controller.py     # AI request handling logic
│   └── conversation_controller.py  # Conversation management logic
├── models/
│   └── schemas.py           # Pydantic models for request/response validation
├── routes/
│   ├── ai_routes.py         # AI-related API endpoints
│   └── conversation_routes.py      # Conversation-related API endpoints
├── services/
│   ├── database_service.py  # Database operations
│   └── openai_service.py    # OpenAI API integration
├── utils/
│   └── logging_config.py    # Logging configuration
├── main.py                  # FastAPI application entry point
├── requirements.txt         # Python dependencies
├── env.example             # Environment variables template
└── README.md               # This file
```

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (sign up at https://platform.openai.com/)

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd ai-api-integration-backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the root directory:

```bash
cp env.example .env
```

Edit the `.env` file and add your OpenAI API key:

```env
# OpenAI API Configuration (Required)
OPENAI_API_KEY=sk-your_openai_api_key_here

# Optional Configuration
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7
PORT=8000
DB_PATH=./conversations.db
```

**Important**: Replace `sk-your_openai_api_key_here` with your actual OpenAI API key.

### 5. Run the Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`

## API Endpoints

### Core Endpoints

- **POST** `/api/ask-ai` - Send a prompt to the AI and receive a response
- **GET** `/api/conversations` - Retrieve all past conversations
- **DELETE** `/api/conversations` - Clear all conversation history
- **GET** `/api/health` - Check API health status

## Testing the API

### Using cURL

#### 1. Ask AI a Question
```bash
curl -X POST "http://localhost:8000/api/ask-ai" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is artificial intelligence?"}'
```

#### 2. Get All Conversations
```bash
curl -X GET "http://localhost:8000/api/conversations"
```

#### 3. Clear Conversation History
```bash
curl -X DELETE "http://localhost:8000/api/conversations"
```

#### 4. Health Check
```bash
curl -X GET "http://localhost:8000/api/health"
```

### Using the Test Script

```bash
# Make sure your server is running first
./test_api.sh
```

## Request/Response Examples

### POST /api/ask-ai

**Valid Request:**
```json
{
  "prompt": "Explain quantum computing in simple terms"
}
```

**Success Response (200):**
```json
{
  "prompt": "Explain quantum computing in simple terms",
  "response": "Quantum computing is a revolutionary technology that uses the principles of quantum mechanics to process information...",
  "timestamp": "2024-01-15T10:30:45.123456",
  "model": "gpt-3.5-turbo"
}
```

### GET /api/conversations

**Success Response (200):**
```json
{
  "conversations": [
    {
      "id": 1,
      "prompt": "Explain quantum computing in simple terms",
      "response": "Quantum computing is a revolutionary technology...",
      "timestamp": "2024-01-15T10:30:45.123456",
      "model": "gpt-3.5-turbo"
    }
  ],
  "total_count": 1
}
```

### DELETE /api/conversations

**Success Response (200):**
```json
{
  "message": "Successfully deleted 5 conversations",
  "deleted_count": 5
}
```

## Error Handling & Validation

### Input Validation Rules

- **Required**: Prompt field must be present
- **Non-empty**: Cannot be empty or contain only whitespace
- **Length**: Must be between 1-4000 characters
- **Meaningful content**: Must contain at least 2 meaningful characters
- **Security**: Cannot contain potentially harmful content (script tags, etc.)
- **Quality**: Cannot have excessive character repetition (>50 same characters)

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": "Error Category",
  "error_code": "SPECIFIC_ERROR_CODE",
  "message": "Detailed error description",
  "suggestions": [
    "Helpful suggestion 1",
    "Helpful suggestion 2"
  ],
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### Error Codes & Examples

#### Empty Prompt (400)
**Request:**
```bash
curl -X POST "http://localhost:8000/api/ask-ai" \
  -H "Content-Type: application/json" \
  -d '{"prompt": ""}'
```

**Response:**
```json
{
  "error": "Invalid Input",
  "error_code": "EMPTY_PROMPT",
  "message": "Prompt cannot be empty or contain only whitespace",
  "suggestions": [
    "Please provide a non-empty prompt",
    "Ensure your prompt contains actual text, not just spaces"
  ],
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

#### Insufficient Content (400)
**Request:**
```bash
curl -X POST "http://localhost:8000/api/ask-ai" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a"}'
```

**Response:**
```json
{
  "error": "Invalid Input",
  "error_code": "INSUFFICIENT_CONTENT",
  "message": "Prompt must contain at least 2 meaningful characters",
  "suggestions": [
    "Please provide a prompt with at least 2 meaningful characters",
    "Try asking a complete question or making a clear statement"
  ],
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

#### Harmful Content (400)
**Request:**
```bash
curl -X POST "http://localhost:8000/api/ask-ai" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello <script>alert(\"test\")</script>"}'
```

**Response:**
```json
{
  "error": "Invalid Input",
  "error_code": "HARMFUL_CONTENT",
  "message": "Prompt contains potentially harmful content",
  "suggestions": [
    "Please remove any script tags or potentially harmful content",
    "Ensure your prompt contains only safe, plain text"
  ],
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

#### Missing Field (422)
**Request:**
```bash
curl -X POST "http://localhost:8000/api/ask-ai" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**
```json
{
  "error": "Validation Error",
  "message": "Request validation failed. Please check your input.",
  "details": [
    {
      "field": "body.prompt",
      "message": "Field 'prompt' is required",
      "type": "value_error.missing"
    }
  ],
  "suggestions": [
    "Ensure all required fields are provided",
    "Check that field values meet the specified requirements"
  ],
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

#### Rate Limit Exceeded (429)
```json
{
  "error": "AI Service Error",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded. Please wait a moment before trying again.",
  "suggestions": [
    "Wait a few minutes before trying again",
    "Consider upgrading your OpenAI plan"
  ],
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

#### Invalid API Key (401)
```json
{
  "error": "AI Service Error",
  "error_code": "INVALID_API_KEY",
  "message": "Invalid API key or authentication failed. Please check your OpenAI API key.",
  "suggestions": [
    "Check your OpenAI API key",
    "Ensure the API key has proper permissions"
  ],
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### Complete Error Code Reference

| Error Code | HTTP Status | Description | Common Causes |
|------------|-------------|-------------|---------------|
| `EMPTY_PROMPT` | 400 | Prompt is empty or whitespace-only | Empty string, spaces, tabs, newlines only |
| `INSUFFICIENT_CONTENT` | 400 | Prompt too short | Single character prompts |
| `HARMFUL_CONTENT` | 400 | Potentially dangerous content detected | Script tags, JavaScript protocols |
| `EXCESSIVE_REPETITION` | 400 | Too much character repetition | Same character repeated >50 times |
| `RATE_LIMIT_EXCEEDED` | 429 | OpenAI API rate limit hit | Too many requests in short time |
| `QUOTA_EXCEEDED` | 429 | OpenAI API quota exhausted | Billing/usage limits reached |
| `INVALID_API_KEY` | 401 | OpenAI API key invalid | Wrong or expired API key |
| `REQUEST_TIMEOUT` | 504 | Request timeout | Network issues, large prompts |
| `AI_SERVICE_ERROR` | 503 | OpenAI service unavailable | OpenAI API downtime |

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Troubleshooting

### Common Issues

1. **"OpenAI API key not found"**
   - Ensure `.env` file exists and contains valid `OPENAI_API_KEY`

2. **"Module not found" errors**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`

3. **Port already in use**
   - Change the port in `.env` file or kill the process using the port

## Assessment Requirements Fulfilled

✅ **Project Setup (10 points)**
- FastAPI backend with clear folder structure
- Git repository ready for version control
- Organized into `/routes`, `/controllers`, `/services`, and `/utils`

✅ **REST API Design & Prompt Handling (20 points)**
- `POST /api/ask-ai` endpoint with JSON validation
- Input validation ensuring non-empty strings
- Meaningful error messages for invalid inputs

✅ **AI API Integration (40 points)**
- OpenAI GPT-3.5-turbo integration using official SDK
- Secure API key storage via environment variables
- Comprehensive error handling for API failures, rate limits, and malformed responses

✅ **Bonus: Conversation Logging & Storage (+10 points)**
- SQLite database for logging conversations
- `GET /api/conversations` endpoint to retrieve history
- `DELETE /api/conversations` endpoint to clear history 