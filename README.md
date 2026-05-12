# Forum Review Scraper

A backend API that scrapes posts/threads from multiple forum platforms through a **single endpoint**. The platform is dynamically chosen based on input.

## Architecture

```
POST /api/v1/scrape  →  ScraperFactory  →  BaseScraper (interface)
                                              ├── RedditScraper
                                              ├── ProductHuntScraper
                                              ├── StackOverflowScraper
                                              ├── WebmasterSunScraper
                                              └── QuoraScraper
```

### SOLID Principles

| Principle | Implementation |
|-----------|---------------|
| **S** — Single Responsibility | Each file handles one concern (fetch, extract, route, etc.) |
| **O** — Open/Closed | Add new forums by adding a folder + registering in factory |
| **L** — Liskov Substitution | All scrapers implement `BaseScraper` — interchangeable |
| **I** — Interface Segregation | `BaseScraper` defines only universal methods |
| **D** — Dependency Inversion | Routes depend on interface, not concrete scrapers |

---

## Project Structure

```
├── main.py                          # FastAPI app entry point
├── api/v1/routes/scraper.py         # POST /api/v1/scrape endpoint
├── core/
│   ├── config.py                    # Environment variables, settings
│   ├── exceptions.py                # Custom exception hierarchy
│   └── response.py                  # Unified API response models
├── interfaces/
│   └── base_scraper.py              # Abstract base class for scrapers
├── factory/
│   └── scraper_factory.py           # Forum → Scraper routing
├── models/
│   ├── request.py                   # Request body validation
│   └── response.py                  # Unified Post model
├── scrapers/
│   ├── reddit/
│   │   ├── scraper.py               # Orchestrator (validate→fetch→extract→normalize)
│   │   ├── fetcher.py               # HTTP requests with retry + header rotation
│   │   ├── extractor.py             # Parse Reddit JSON
│   │   └── models.py                # Reddit URL validation
│   ├── producthunt/
│   │   ├── scraper.py               # Orchestrator (validate→fetch→extract→normalize)
│   │   ├── fetcher.py               # HTML page fetching with retry
│   │   ├── extractor.py             # Parse Apollo SSR embedded data
│   │   └── models.py                # Product Hunt URL validation
│   ├── stackoverflow/
│   │   ├── scraper.py               # Orchestrator (validate→fetch→extract→normalize)
│   │   ├── fetcher.py               # Stack Exchange API v2.3 client
│   │   ├── extractor.py             # Parse API JSON responses
│   │   └── models.py                # Stack Overflow URL validation
│   ├── webmastersun/
│   │   ├── scraper.py               # Orchestrator (validate→fetch→extract→normalize)
│   │   ├── fetcher.py               # XenForo HTML fetching with retry
│   │   ├── extractor.py             # Parse XenForo search result HTML
│   │   └── models.py                # WebmasterSun URL validation
│   └── quora/
│       ├── scraper.py               # Orchestrator (validate→fetch→extract→normalize)
│       ├── fetcher.py               # curl_cffi session + GraphQL API client
│       ├── extractor.py             # Parse GraphQL feed response
│       └── models.py                # Quora topic URL validation
├── ui/
│   └── index.html                   # Browser-based scraper UI
├── utils/
│   ├── http.py                      # Reusable HTTP utilities
│   └── validators.py                # URL and forum name validators
└── requirements.txt
```

---

## API Reference

### `POST /api/v1/scrape`

Scrapes **posts** from a subreddit, Product Hunt product page, Stack Overflow tag, WebmasterSun search, or Quora topic.

---

#### Scrape Reddit Posts

**Request:**
```json
{
  "forum": "reddit",
  "url": "https://www.reddit.com/r/Zoho/",
  "limit": 200,
  "options": {
    "sort": "hot"
  }
}
```

**Response (200):**
```json
{
  "success": true,
  "forum": "reddit",
  "subreddit": "Zoho",
  "total_fetched": 200,
  "posts": [
    {
      "id": "1t30kdp",
      "title": "Post title here",
      "author": "username",
      "score": 125,
      "upvote_ratio": 0.95,
      "num_comments": 42,
      "created_utc": 1714800000.0,
      "url": "https://www.reddit.com/r/Zoho/comments/1t30kdp/...",
      "permalink": "https://www.reddit.com/r/Zoho/comments/1t30kdp/...",
      "selftext": "Post body text...",
      "link_flair_text": "Question",
      "is_self": true,
      "thumbnail": ""
    }
  ]
}
```

---

#### Scrape Product Hunt Forum Posts

**Request:**
```json
{
  "forum": "producthunt",
  "url": "https://www.producthunt.com/p/zoho",
  "limit": 20
}
```

**Response (200):**
```json
{
  "success": true,
  "forum": "producthunt",
  "product_slug": "zoho",
  "total_fetched": 10,
  "posts": [
    {
      "id": "12345",
      "title": "Thread title here",
      "author": "John Doe",
      "score": 5,
      "upvote_ratio": 0.0,
      "num_comments": 3,
      "created_utc": 0.0,
      "url": "https://www.producthunt.com/p/zoho/thread-slug",
      "permalink": "/p/zoho/thread-slug",
      "selftext": "",
      "link_flair_text": "Product tagline here",
      "is_self": true,
      "thumbnail": ""
    }
  ]
}
```

---

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `forum` | string | Yes | Target forum (`reddit`, `producthunt`, `stackoverflow`, `webmastersun`, `quora`) |
| `url` | string | Yes | Forum-specific URL (see examples below) |
| `limit` | integer | No | Max items to fetch (default: 100, max: 10000) |
| `options` | object | No | Forum-specific parameters |

**Error Response:**
```json
{
  "success": false,
  "forum": "reddit",
  "error_code": "INVALID_URL",
  "message": "The provided URL is not a valid Reddit URL"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNSUPPORTED_FORUM` | 400 | Forum not supported |
| `INVALID_URL` | 400 | URL format invalid for forum |
| `PRIVATE_POST` | 403 | Post is private/restricted |
| `POST_NOT_FOUND` | 404 | Post/forum deleted or not found |
| `RATE_LIMITED` | 429 | Rate limited by platform |
| `FETCH_TIMEOUT` | 504 | Request timed out |
| `PARSE_ERROR` | 500 | Failed to parse response |
| `MAX_RETRIES_EXCEEDED` | 503 | All retry attempts failed |

---

## Reddit Scraper Details

- Uses Reddit's public JSON API (no credentials required)
- **No caching** — always fetches fresh data
- Rotates User-Agent randomly per request
- Retry on 429: waits `attempt × 10` seconds (max 3 retries)
- Random delay between page fetches: `1.5–3.5 seconds`
- Fetches all posts from a subreddit with pagination

### Reddit Options

| Option | Type | Default | Values |
|--------|------|---------|--------|
| `sort` | string | `"hot"` | `hot`, `new`, `top`, `rising`, `controversial` |

---

## Product Hunt Scraper Details

- Scrapes **forum posts** (threads) from a product community page
- Parses embedded Apollo SSR data from the HTML page
- Supports `/p/{product}` and `/products/{product}` URL patterns
- Query parameters (e.g. `?order=trending`) are automatically stripped
- Pagination via page parameter (10 threads per page)
- Random delay between page fetches: `1.5–3 seconds`

### Product Hunt URL Patterns

| URL Pattern | Example |
|-------------|---------|
| `/p/{product}` | `https://www.producthunt.com/p/zoho` |
| `/products/{product}` | `https://www.producthunt.com/products/zoho` |

---

## Stack Overflow Scraper Details

- Uses the **Stack Exchange API v2.3** (public, no key required)
- Scrapes questions tagged with a specific tag
- Supports multiple sort orders and date filtering
- Pagination with configurable page size (up to 100 per page)

**Request:**
```json
{
  "forum": "stackoverflow",
  "url": "https://stackoverflow.com/questions/tagged/zoho",
  "limit": 50,
  "options": {
    "sort": "votes"
  }
}
```

### Stack Overflow Sort Options

| Option | Description |
|--------|-------------|
| `activity` | Recently active (default) |
| `creation` | Newest first |
| `votes` | Highest score |
| `hot` | Hot questions |
| `week` | Top this week |
| `month` | Top this month |

### Stack Overflow URL Patterns

| URL Pattern | Example |
|-------------|---------|
| `/questions/tagged/{tag}` | `https://stackoverflow.com/questions/tagged/zoho` |

---

## WebmasterSun Scraper Details

- Scrapes search results from the **XenForo-based** WebmasterSun forum
- Fetches full post content by visiting each thread page
- HTML parsing with regex (no BeautifulSoup dependency)
- Retry logic with exponential backoff on rate limiting

**Request:**
```json
{
  "forum": "webmastersun",
  "url": "https://www.webmastersun.com/search/739149/?q=google&o=date",
  "limit": 20
}
```

### WebmasterSun URL Patterns

| URL Pattern | Example |
|-------------|---------|
| `/search/{id}/?q={query}` | `https://www.webmastersun.com/search/739149/?q=google&o=date` |

---

## Quora Scraper Details

- Scrapes **questions** from a Quora topic page
- Uses `curl_cffi` with Chrome TLS fingerprint to bypass Cloudflare
- Calls Quora's internal GraphQL API with persisted query hashes
- Extracts auth tokens (`formkey`, `revision`) and feed hash from page/JS bundles
- Cursor-based pagination with deduplication
- Returns question titles, URLs, and answer counts (not answer content)

**Request:**
```json
{
  "forum": "quora",
  "url": "https://www.quora.com/topic/Zoho-CRM-1",
  "limit": 30
}
```

### Quora URL Patterns

| URL Pattern | Example |
|-------------|---------|
| `/topic/{slug}` | `https://www.quora.com/topic/Zoho-CRM-1` |

---

## Adding a New Forum Scraper

1. Create `scrapers/your_forum/` directory with:
   - `scraper.py` — implements `BaseScraper`
   - `fetcher.py` — HTTP logic
   - `extractor.py` — response parsing
   - `models.py` — validation
2. Register in `factory/scraper_factory.py`:
   ```python
   from scrapers.your_forum.scraper import YourForumScraper
   REGISTRY["your_forum"] = YourForumScraper
   ```
3. Add forum name to `SUPPORTED_FORUMS` in `utils/validators.py`
4. Add any config constants to `core/config.py`
5. (Optional) Add UI option in `ui/index.html`

---

## Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Framework | FastAPI | Fast, async, auto docs |
| HTTP Client | httpx | Modern, sync/async support |
| HTTP Client | curl_cffi | Cloudflare bypass via TLS fingerprinting (Quora) |
| Validation | Pydantic v2 | Type-safe request/response |
| Language | Python 3.11+ | Latest features |
| Server | Uvicorn | ASGI server |
