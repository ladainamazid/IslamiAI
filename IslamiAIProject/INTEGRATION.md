# Phase 2 Integration: chatbot.py → Flask /chat Endpoint

## Overview
This document specifies how to integrate `chatbot.py` (orchestration layer) into the existing Flask application (app.py) from Phase 1.

---

## Architecture: Request Flow

```
HTTP POST /chat
    ↓
Flask request handler (rate-limited by flask-limiter)
    ↓
Extract user_input, language, session_id from JSON body
    ↓
chatbot.generate_response(user_input, language, session_id, request_id)
    ↓
Chatbot pipeline: parse → retrieve → validate → format
    ↓
Return ChatbotResponse.to_dict() or ChatbotError.to_dict()
    ↓
HTTP 200 + JSON response
    (or HTTP 400/500 if validation fails)
```

---

## Implementation: Update app.py

### Step 1: Import chatbot.py

```python
# app.py (top of file)

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Phase 1 imports (already exist)
from config import Config
from query_parser import QueryParser
from retrieval import RetrievalEngine
from reasoning_validator import ReasoningValidator
from formatter import ResponseFormatter

# Phase 2 import (NEW)
from chatbot import create_chatbot, IslamicKnowledgeChatbot
```

### Step 2: Initialize chatbot in Flask app

```python
# app.py (in create_app() or __init__)

def create_app(config=None):
    """Flask application factory."""
    
    if config is None:
        config = Config()
    
    app = Flask(__name__)
    
    # Rate limiting (Phase 1)
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri="redis://localhost:6379"
    )
    
    # Initialize chatbot (Phase 2)
    chatbot = create_chatbot(config, logger=app.logger)
    
    # Store in app context for routes
    app.chatbot = chatbot
    
    return app, limiter
```

### Step 3: Add /chat endpoint

```python
# app.py (new route)

@app.route('/chat', methods=['POST'])
@limiter.limit("10 per minute")  # Rate limit: 10 requests per minute
def chat():
    """
    Single-turn conversation endpoint.
    
    REQUEST:
        POST /chat
        Content-Type: application/json
        {
            "message": "What does Islam say about honesty?",
            "language": "en",  # optional, default "en"
            "session_id": "sess-12345"  # optional for future multi-turn
        }
    
    RESPONSE (Success):
        HTTP 200
        {
            "answer": "Islam emphasizes truthfulness...",
            "confidence": 0.92,
            "sources": ["Quran 3:186", "Hadith: Sahih al-Bukhari 2605"],
            "justification": "Multiple Quranic sources...",
            "language": "en",
            "session_id": "sess-12345",
            "timestamp": "2025-05-30T12:34:56.789Z",
            "request_id": "req-abc123"
        }
    
    RESPONSE (Error):
        HTTP 400/500
        {
            "error_code": "PARSE_ERROR" | "NO_RESULTS" | "LOW_CONFIDENCE" | "INTERNAL_ERROR",
            "error_message": "Human-readable error message",
            "user_suggestion": "What user should do",
            "language": "en",
            "timestamp": "2025-05-30T12:34:56.789Z",
            "request_id": "req-abc123"
        }
    """
    
    try:
        # Validate request format
        if not request.is_json:
            return jsonify({
                "error_code": "INVALID_REQUEST",
                "error_message": "Request body must be JSON",
                "user_suggestion": "Send Content-Type: application/json"
            }), 400
        
        data = request.get_json()
        
        # Extract parameters
        message = data.get('message', '').strip()
        language = data.get('language', 'en')
        session_id = data.get('session_id')
        
        # Validate message
        if not message:
            return jsonify({
                "error_code": "MISSING_MESSAGE",
                "error_message": "Field 'message' is required",
                "user_suggestion": "Provide a non-empty 'message' field"
            }), 400
        
        if len(message) > 5000:
            return jsonify({
                "error_code": "MESSAGE_TOO_LONG",
                "error_message": "Message exceeds 5000 characters",
                "user_suggestion": "Shorten your question"
            }), 400
        
        # Validate language
        if language not in ['en', 'ar', 'id']:
            return jsonify({
                "error_code": "UNSUPPORTED_LANGUAGE",
                "error_message": f"Language '{language}' not supported",
                "user_suggestion": "Use 'en', 'ar', or 'id'"
            }), 400
        
        # Generate response via chatbot
        request_id = request.headers.get('X-Request-ID', f'req-{id(request)}')
        
        app.logger.info(
            f"Processing chat request",
            extra={
                "message": message[:100],
                "language": language,
                "request_id": request_id
            }
        )
        
        response = app.chatbot.generate_response(
            user_input=message,
            language=language,
            session_id=session_id,
            request_id=request_id
        )
        
        # Determine HTTP status based on response type
        status_code = 200 if 'answer' in response else 400
        
        return jsonify(response), status_code
    
    except Exception as e:
        # Unexpected error
        app.logger.exception("Unexpected error in /chat endpoint")
        return jsonify({
            "error_code": "INTERNAL_ERROR",
            "error_message": "An unexpected error occurred",
            "user_suggestion": "Please try again later or contact support"
        }), 500
```

### Step 4: Add system status endpoint (debugging)

```python
# app.py (new route, optional)

@app.route('/status', methods=['GET'])
def status():
    """
    System health check.
    
    RESPONSE:
        HTTP 200
        {
            "chatbot_status": "healthy",
            "query_parser": "ready",
            "retrieval_engine": "ready",
            "reasoning_validator": "ready",
            "response_formatter": "ready",
            "timestamp": "2025-05-30T12:34:56.789Z"
        }
    """
    return jsonify(app.chatbot.get_system_status()), 200
```

### Step 5: Add explain endpoint (debugging, dev-only)

```python
# app.py (new route, DEVELOPMENT ONLY)

@app.route('/debug/explain', methods=['POST'])
@app.route('/debug/explain', methods=['POST'])
def explain():
    """
    (DEVELOPMENT ONLY) Detailed breakdown of chatbot decision.
    
    REQUEST:
        POST /debug/explain
        {
            "message": "Query to analyze",
            "language": "en"
        }
    
    RESPONSE:
        HTTP 200
        {
            "parsed_query": {...},
            "retrieval": {...},
            "validation": {...},
            "formatted": {...}
        }
    """
    
    if not app.config.get('DEBUG', False):
        return jsonify({"error": "Debug endpoint not available"}), 403
    
    data = request.get_json()
    message = data.get('message', '')
    language = data.get('language', 'en')
    
    explanation = app.chatbot.explain_decision(message, language=language)
    return jsonify(explanation), 200
```

---

## Testing the Integration

### 1. Unit Tests (pytest)

```bash
# Run chatbot tests
pytest test_chatbot.py -v

# Run all tests including Phase 1
pytest test_*.py -v
```

### 2. Integration Test (curl)

```bash
# Successful request
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does Islam say about honesty?",
    "language": "en"
  }'

# Expected output:
# {
#   "answer": "Islam emphasizes truthfulness...",
#   "confidence": 0.92,
#   "sources": ["Quran 3:186", "..."],
#   "language": "en",
#   "timestamp": "..."
# }
```

### 3. Error Cases (curl)

```bash
# Missing message
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"language": "en"}'

# Invalid language
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Query",
    "language": "xx"
  }'

# Rate limit exceeded (after 10 requests/min)
# Returns 429 Too Many Requests
```

---

## Configuration: app.config

Add these to your `config.py` or `.env`:

```python
# config.py (Phase 2 specific)

class Config:
    # ... existing config ...
    
    # Chatbot configuration
    CHAT_MAX_MESSAGE_LENGTH = 5000
    CHAT_RATE_LIMIT = "10/minute"
    
    # Response configuration
    MIN_CONFIDENCE_THRESHOLD = 0.7
    RETRIEVAL_TOP_K = 5
    RETRIEVAL_MIN_SCORE = 0.5
```

---

## Error Codes & HTTP Status

| Error Code | HTTP Status | Meaning |
|---|---|---|
| INVALID_REQUEST | 400 | Request format invalid (not JSON) |
| MISSING_MESSAGE | 400 | 'message' field required |
| MESSAGE_TOO_LONG | 400 | Message exceeds limit |
| UNSUPPORTED_LANGUAGE | 400 | Language not supported |
| PARSE_ERROR | 400 | Query parsing failed |
| NO_RESULTS | 400 | No documents retrieved |
| LOW_CONFIDENCE | 400 | Confidence below threshold |
| INTERNAL_ERROR | 500 | Unexpected server error |

---

## Backwards Compatibility

✅ **Phase 1 routes unchanged**
- `/` (landing page)
- `/api/query` (if it existed)
- All existing endpoints remain untouched

✅ **New routes added**
- `/chat` (POST) — main chatbot endpoint
- `/status` (GET) — health check
- `/debug/explain` (POST) — debugging endpoint (dev-only)

---

## Deployment Checklist

- [ ] Copy `chatbot.py` to project root
- [ ] Copy `test_chatbot.py` to project root
- [ ] Update `requirements.txt` with Flask>=3.0, requests, aiohttp
- [ ] Update `app.py` with `/chat` route
- [ ] Run `pytest test_chatbot.py -v` (≥85% pass rate)
- [ ] Run integration test with curl
- [ ] Test rate limiting: `curl` 10+ times rapidly
- [ ] Deploy to production (Flask 3.0+, Redis running)

---

## Future Phases

**Phase 3** will add:
- Multi-turn conversation memory (`chatbot_memory.py`)
- External API integration (`reference_fetcher.py`)
- Async processing (`async_integration.py`)
- Database persistence

**Phase 2** (this) deliberately stays focused:
- Single-turn Q&A only
- No external APIs yet
- No persistent storage yet
