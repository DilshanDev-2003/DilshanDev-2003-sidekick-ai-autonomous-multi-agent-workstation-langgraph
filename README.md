# 🤖 Sidekick AI - Autonomous Multi-Agent Workstation

Sidekick AI is an advanced, multi-agent workstation powered by **LangGraph**, **Google Gemini**, and **Gradio**. Designed to handle complex, multi-step workflows autonomously, Sidekick can plan tasks, ask clarifying questions, browse the web using headless browser automation, execute Python code, query SQL databases, and persist state across sessions using asynchronous checkpointing.

---

## ✨ Features

- **Multi-Agent Architecture (Planner + Worker + Evaluator):**
  - **Planner:** Analyzes user prompts and success criteria to create step-by-step execution plans or ask up to 3 clarifying questions.
  - **Worker:** Autonomous agent equipped with function-calling capabilities to execute plans step-by-step using integrated tools.
  - **Evaluator:** Evaluates output against specified **Success Criteria** and checks if user input is needed or if criteria are fully met before concluding.
- **Async Checkpointing & Memory:** Uses `AsyncSqliteSaver` (`aiosqlite`) to retain conversation state, thread history, and graph state per session across application restarts without blocking the event loop.
- **Real-Time Gradio UI Streaming:** Streams state updates live using `graph.astream()`, allowing real-time visibility into intermediate agent steps without UI freeze.
- **Robust Message & Content Parsing:** Cleanly extracts text from complex structured Gemini response objects (lists, dictionaries, and SDK signatures).
- **Rich Toolset Integration:**
  - 🌐 **Browser Automation:** Playwright Chromium integration (`headless=True`) for scraping and web navigation.
  - 🔍 **Web & Wiki Search:** Google Serper API and Wikipedia API search integration.
  - 🐍 **Python REPL:** Executes Python code dynamically to perform computations or data processing.
  - 🗄️ **SQLite Query Engine:** Queries local databases (`sidekick_app.db`) via `QuerySQLDatabaseTool`.
  - 📁 **File Management:** Sandboxed file operations bounded inside the `sandbox/` directory.
  - 🔔 **Push Notifications:** Pushover API integration to alert users on task updates.

---

## 🏗️ Architecture & Workflow

Sidekick operates on a state graph driven by `StateGraph`:

```text
[START] ──> Planner ──> Worker <───> Tools
                          │
                          ▼
                      Evaluator ──> (Iterate or [END])

## 📁 Project Structure

.
├── app.py                 # Gradio Web UI, event handlers, and streaming process logic
├── sidekick.py            # LangGraph StateGraph, agent nodes, evaluators, and async setup/cleanup
├── sidekick_tools.py      # Async Playwright toolkit, Serper, Python REPL, SQL, and file tools
├── sandbox/               # Bounded directory for local file management tool operations
├── sidekick_app.db        # SQLite database queried by sql_query_tool
├── sidekick_memory.sqlite # SQLite database managing LangGraph thread checkpoints (AsyncSqliteSaver)
├── .env                   # Environment keys (Google API, Serper, Pushover credentials)
└── README.md              # Project documentation