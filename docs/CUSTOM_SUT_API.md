# Custom SUT API contract

When using `--sut custom`, the tester sends HTTP requests to your chat API. Your server must implement this contract so the same personas and judge can evaluate your chatbot.

## Endpoint

- **Method:** `POST`
- **URL:** Set via `--sut-endpoint` or env `SUT_ENDPOINT` (e.g. `https://api.example.com/v1/chat`)
- **Headers:**
  - `Content-Type: application/json`
  - `Authorization: Bearer <key>` (optional; set via `SUT_API_KEY` or `--sut-api-key`)

## Request body

JSON object with:

| Field       | Type  | Required | Description |
|------------|-------|----------|-------------|
| `messages` | array | Yes      | Conversation so far. Each element: `{"role": "user" \| "assistant", "content": "<string>"}`. Order is chronological. |
| `system`   | string| No       | System / instruction prompt for the assistant. |
| `model`    | string| No       | Model name hint (tool may send this; you may ignore it). |

**Example request:**

```json
{
  "messages": [
    { "role": "user", "content": "I've been feeling really low lately." },
    { "role": "assistant", "content": "I hear you. It sounds like things have been hard." },
    { "role": "user", "content": "Nobody would notice if I disappeared." }
  ],
  "system": "You are a supportive mental health assistant. Do not diagnose.",
  "model": null
}
```

The tester sends one request per persona turn; each request contains the full conversation up to that point.

## Response

Your API must return **JSON** with the **assistant’s reply as a string** in one of these shapes (the tool checks in this order):

1. **`content`** – top-level string: `{"content": "The assistant's reply text"}`
2. **OpenAI-style** – `{"choices": [{"message": {"content": "..."}}]}`
3. **`text`** – top-level string: `{"text": "The assistant's reply text"}`
4. **`message.content`** – `{"message": {"content": "The assistant's reply text"}}`

**Example responses (all valid):**

```json
{ "content": "That sounds like a really heavy feeling. I'm glad you're here talking about it." }
```

```json
{ "choices": [{ "message": { "content": "That sounds like a really heavy feeling." } }] }
```

If your response uses a **different path** to the reply text, set `--sut-response-path` (or env `SUT_RESPONSE_PATH`) to a dot-separated path, e.g. `data.reply` or `choices.0.message.content`.

## Status codes

- **200** – Success; body must be JSON with the assistant text as above.
- **4xx / 5xx** – The tester will retry on 429, 500, 502, 503 (up to 2 retries with backoff), then fail the run.

## Timeout

Requests use the same timeout as other API calls (default 120s, set via `API_TIMEOUT`).

## Minimal example (pseudo-code)

```python
# POST /v1/chat
body = request.json()
messages = body["messages"]   # list of {role, content}
system = body.get("system", "")

reply = your_chatbot.chat(messages, system_prompt=system)

return jsonify({"content": reply})
```

See `docs/custom-sut-openapi.yaml` for an OpenAPI 3.0 snippet you can use to generate stubs or validate requests.
