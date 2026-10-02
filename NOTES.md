# 📝 Sidekick Technical Notes & Troubleshooting Log

## ⚠️ Key Bug Fixes & Technical Decisions

### 1. LangGraph Async Checkpointing (`AsyncSqliteSaver`)
- **Issue:** Using standard `SqliteSaver` with `await graph.ainvoke()` or `astream()` throws `NotImplementedError: The SqliteSaver does not support async methods`.
- **Solution:** Switched to `AsyncSqliteSaver` from `langgraph.checkpoint.sqlite.aio` backed by `aiosqlite`.
- **Path Syntax Note:** `AsyncSqliteSaver.from_conn_string("sidekick_memory.sqlite")` expects a plain filename path string, **not** a SQLAlchemy URI prefix like `sqlite:///...`.
- **Context Manager Lifecycle:** `from_conn_string()` returns an async context manager. Initialize context in `setup()` with `await self._saver_cm.__aenter__()` and clean up in `cleanup()` with `await self._saver_cm.__aexit__(None, None, None)`.

### 2. Gemini Structured Content Parsing
- **Issue:** Gemini returns structured message objects or lists of dicts containing metadata (`extras`, `signature`) when tools or structured outputs are active, causing raw JSON-like blobs in the UI or throwing `AttributeError: 'list' object has no attribute 'content'`.
- **Solution:** Implemented `extract_text()` helper function to recursively parse string blocks from nested lists, dictionaries, and `AIMessage` objects before sending to Gradio.

### 3. Model Identifier Naming
- **Issue:** Calling unprefixed model names caused `404 NOT_FOUND` errors on newer versions of `langchain-google-genai`.
- **Fix:** Prefix models with `models/` (e.g., `models/gemini-1.5-flash`) or use updated aliases (`gemini-1.5-flash-latest`, `gemini-2.0-flash`).

### 4. Router Logic Object Access
- **Issue:** In `worker_router`, accessing `.tool_calls` on `state["messages"][-1].content` failed because `.content` is a string/list rather than the message instance itself.
- **Fix:** Inspected `state["messages"][-1]` directly: `if hasattr(last_message, "tool_calls") and last_message.tool_calls:`.

### 5. Playwright & Execution Latency
- Running Playwright with `headless=False` creates high CPU overhead and long cycle times (~167s+ per superstep). Set `headless=True` for performance.
- Streaming graph execution via `astream()` ensures intermediate steps are rendered in Gradio immediately rather than waiting for full graph completion.

---

## 📌 Future Enhancements

- [ ] Add a short-circuit route in `planner` to bypass execution plans for simple one-shot queries.
- [ ] Implement browser context reuse to avoid reopening Chromium sessions across user messages.
- [ ] Add human-in-the-loop interruption nodes prior to database or notification actions.