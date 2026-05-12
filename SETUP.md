# Setup & Installation Guide

## Prerequisites

- **Python 3.11+** installed
- **pip** package manager
- (Optional) **venv** or **conda** for virtual environments

---

## Quick Start

### 1. Clone / Navigate to Project

```bash
cd scraper-service-forum
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access the API

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/

---

## Test the Endpoint

### Using cURL

**Reddit Posts:**
```bash
curl -X POST http://localhost:8000/api/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "forum": "reddit",
    "url": "https://www.reddit.com/r/Zoho/",
    "limit": 50
  }'
```

**Product Hunt Forum Posts:**
```bash
curl -X POST http://localhost:8000/api/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "forum": "producthunt",
    "url": "https://www.producthunt.com/p/zoho",
    "limit": 10
  }'
```

**Stack Overflow Questions:**
```bash
curl -X POST http://localhost:8000/api/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "forum": "stackoverflow",
    "url": "https://stackoverflow.com/questions/tagged/zoho",
    "limit": 50
  }'
```

**WebmasterSun Search:**
```bash
curl -X POST http://localhost:8000/api/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "forum": "webmastersun",
    "url": "https://www.webmastersun.com/search/739149/?q=google&o=date",
    "limit": 20
  }'
```

**Quora Topic Questions:**
```bash
curl -X POST http://localhost:8000/api/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "forum": "quora",
    "url": "https://www.quora.com/topic/Zoho-CRM-1",
    "limit": 30
  }'
```

### Using Python

```python
import requests

# Reddit
response = requests.post(
    "http://localhost:8000/api/v1/scrape",
    json={
        "forum": "reddit",
        "url": "https://www.reddit.com/r/Zoho/",
        "limit": 50,
        "options": {"sort": "hot"}
    }
)
print(response.json())

# Product Hunt
response = requests.post(
    "http://localhost:8000/api/v1/scrape",
    json={
        "forum": "producthunt",
        "url": "https://www.producthunt.com/p/zoho",
        "limit": 10
    }
)
print(response.json())

# Stack Overflow
response = requests.post(
    "http://localhost:8000/api/v1/scrape",
    json={
        "forum": "stackoverflow",
        "url": "https://stackoverflow.com/questions/tagged/zoho",
        "limit": 50
    }
)
print(response.json())

# WebmasterSun
response = requests.post(
    "http://localhost:8000/api/v1/scrape",
    json={
        "forum": "webmastersun",
        "url": "https://www.webmastersun.com/search/739149/?q=google&o=date",
        "limit": 20
    }
)
print(response.json())

# Quora
response = requests.post(
    "http://localhost:8000/api/v1/scrape",
    json={
        "forum": "quora",
        "url": "https://www.quora.com/topic/Zoho-CRM-1",
        "limit": 30
    }
)
print(response.json())
```

---

## Environment Variables (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |

---

## Production Deployment

### Run with multiple workers

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Gunicorn (Linux)

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

Build and run:

```bash
docker build -t forum-scraper .
docker run -p 8000:8000 forum-scraper
```

---

## Project Verification

After starting the server, verify everything works:

1. **Health check:**
   ```bash
   curl http://localhost:8000/
   # {"status":"healthy","service":"Forum Review Scraper","version":"1.0.0"}
   ```

2. **Swagger docs:** Open http://localhost:8000/docs in your browser

3. **Test scrape (Reddit):**
   ```bash
   curl -X POST http://localhost:8000/api/v1/scrape \
     -H "Content-Type: application/json" \
     -d '{"forum": "reddit", "url": "https://www.reddit.com/r/Python/", "limit": 10}'
   ```

4. **Test scrape (Product Hunt):**
   ```bash
   curl -X POST http://localhost:8000/api/v1/scrape \
     -H "Content-Type: application/json" \
     -d '{"forum": "producthunt", "url": "https://www.producthunt.com/p/zoho", "limit": 5}'
   ```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` | Ensure you're in the project root and venv is activated |
| `Connection refused` | Check server is running on the correct port |
| Reddit returns 429 | Normal — the scraper retries automatically with backoff |
| Empty posts array | The subreddit/forum may have no posts, or the URL may be incorrect |
