# How Each Forum Scraper Works

Technical breakdown of how each scraper fetches and extracts data.

---

## 1. Reddit

**Data Source:** Reddit's public JSON API

**How it works:**
1. Sends a GET request to `https://www.reddit.com/r/{subreddit}/{sort}.json`
2. Parses the JSON response — posts are in `data.children[].data`
3. Paginates using the `after` cursor from each response

**Protection handling:**
- Rotates User-Agent headers across 6 browser strings
- Handles 429 rate limits with exponential backoff (`10s × attempt`)

**Pagination:** Cursor-based — each response includes a `data.after` token pointing to the next page. Stops when `after` is null. Delay: 1.5–3.5s between pages.

**Fields extracted:**

| Field | Source |
|-------|--------|
| Title | `data.title` |
| Author | `data.author` |
| Score | `data.score` |
| Upvote ratio | `data.upvote_ratio` |
| Comments count | `data.num_comments` |
| Post body | `data.selftext` |
| Flair | `data.link_flair_text` |
| Created time | `data.created_utc` |
| URL | `data.url` |
| Permalink | `data.permalink` |

---

## 2. Product Hunt

**Data Source:** Apollo SSR (server-side rendered GraphQL data embedded in HTML)

**How it works:**
1. Sends a GET request to `https://www.producthunt.com/p/{product}?page=N`
2. Searches the HTML for embedded JSON containing `"threads"` data
3. Manually parses the JSON by tracking brace boundaries
4. Extracts thread data from `discussionForum.threads.edges[].node`

**Protection handling:**
- Rotates User-Agent headers across 5 browser strings
- Query parameters (e.g. `?order=trending`) are stripped before validation
- Handles 429 with exponential backoff (`2^attempt + random`)

**Pagination:** Page-based — increments `page` parameter. Checks `pageInfo.hasNextPage` to know when to stop. Delay: 1.5–3.0s between pages.

**Fields extracted:**

| Field | Source |
|-------|--------|
| Title | `node.title` |
| Author | `node.user.name` |
| Description | `node.descriptionPreview` |
| Comments count | `node.commentsCount` |
| Score | `node.commentable.latestScore` |
| Created time | `node.createdAt` |
| Product tagline | `node.commentable.tagline` |
| URL | Constructed from `node.path` |

---

## 3. Stack Overflow

**Data Source:** Stack Exchange API v2.3 (official)

**How it works:**
1. Sends a GET request to `https://api.stackexchange.com/2.3/questions?tagged={tag}&site=stackoverflow`
2. Parses the official JSON response — questions are in `items[]`
3. Uses the `filter=withbody` parameter to include full question HTML body

**Protection handling:**
- Optional API key (`SO_API_KEY`) for higher quota (10,000 vs 300 requests/day)
- Checks the `backoff` field in responses and sleeps accordingly

**Pagination:** Page-based — increments `page` parameter. Checks `has_more` boolean to stop. Delay: 0.5s between pages.

**Fields extracted:**

| Field | Source |
|-------|--------|
| Title | `.title` |
| Author | `owner.display_name` |
| Author reputation | `owner.reputation` |
| Score | `.score` |
| Answer count | `.answer_count` |
| View count | `.view_count` |
| Is answered | `.is_answered` |
| Body (HTML) | `.body` |
| Tags | `.tags` (joined as comma-separated) |
| Created time | `.creation_date` |
| URL | `.link` |

---

## 4. WebmasterSun

**Data Source:** XenForo forum HTML pages

**How it works (two-phase fetch):**

**Phase 1 — Search results:**
1. Sends a GET request to `https://www.webmastersun.com/search/{id}/?q={query}&page=N`
2. Splits HTML by `class="block-row block-row--separated"` markers
3. Uses regex to extract title, author, snippet, timestamps from each block

**Phase 2 — Full content:**
4. For each search result, fetches the individual post page
5. Finds the post content inside `class="bbWrapper"` div
6. Converts HTML to plain text (strips tags, decodes entities)

**Protection handling:**
- Rotates User-Agent headers across 5 browser strings
- Handles 429/403 with retry (`5s × attempt`)

**Pagination:** Page-based — checks for `rel="next"` in HTML. Delay: 1.5–3.0s between search pages, plus 1.0–2.0s per individual post fetch.

**Fields extracted:**

| Field | Source |
|-------|--------|
| Title | `<h3 class="contentRow-title">` |
| Author | `data-author` attribute |
| Snippet | `<div class="contentRow-snippet">` |
| Full content | `class="bbWrapper"` (from post page) |
| Post number | `Post #N` text |
| Forum category | `Forum:` link text |
| Created time | `data-time` attribute |
| URL | Reconstructed from href path |

---

## 5. Quora

**Data Source:** Internal GraphQL API (behind Cloudflare)

**How it works:**

**Initialization:**
1. Fetches the topic page (`https://www.quora.com/topic/{slug}`) using `curl_cffi` with Chrome TLS fingerprint to bypass Cloudflare
2. Extracts auth tokens from page HTML: `formkey`, `revision`, and `tid` (topic ID)
3. Finds the TopicTab-ReadWrite JS bundle URL in the page
4. Fetches the JS bundle and extracts the 64-char GraphQL persisted query hash

**Data fetching:**
5. Sends a POST request to `https://www.quora.com/graphql/gql_para_POST` with:
   - Headers: `quora-formkey`, `quora-revision`
   - Body: `queryName`, `variables` (tid, cursor, page size), `extensions` (hash)
6. Parses the nested response: `data.multifeedObject.multifeedConnection.edges[].node.bundleConnection.edges[].node.answer.question`
7. Decodes Quora's JSON text format: `{"sections": [{"spans": [{"text": "..."}]}]}`

**Protection handling:**
- **curl_cffi** with `impersonate="chrome120"` — bypasses Cloudflare TLS fingerprinting
- Session-based — maintains cookies across requests
- Handles 429/403 with exponential backoff (`3s × attempt`)

**Pagination:** Cursor-based — uses `pageInfo.endCursor`. Also increments `multifeedNumBundlesOnClient` per page. Deduplicates questions by `qid` across pages. Delay: 1.0–2.0s between pages.

**Fields extracted:**

| Field | Source |
|-------|--------|
| Title | `question.title` (JSON-parsed) |
| Question ID | `question.qid` |
| Answer count | `question.answerCount` |
| URL | `https://www.quora.com{question.url}` |
| Slug | `question.slug` |

---

## Comparison

| | Reddit | Product Hunt | Stack Overflow | WebmasterSun | Quora |
|---|--------|-------------|----------------|--------------|-------|
| **Source** | Public JSON API | HTML (Apollo SSR) | Official API v2.3 | HTML (XenForo) | Private GraphQL |
| **Auth** | None | None | Optional API key | None | formkey + TLS fingerprint |
| **Cloudflare** | No | No | No | No | **Yes** (curl_cffi bypass) |
| **Pagination** | Cursor | Page number | Page number | Page number | Cursor + offset |
| **Two-phase fetch** | No | No | No | **Yes** | No |
| **HTTP library** | httpx | httpx | httpx | httpx | curl_cffi |
