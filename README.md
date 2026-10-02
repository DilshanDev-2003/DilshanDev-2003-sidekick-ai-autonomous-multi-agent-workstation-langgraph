# 🤖 Sidekick AI - Autonomous Multi-Agent Workstation

Sidekick AI is an advanced, multi-agent AI assistant powered by **LangGraph**, **Google Gemini 3.5 Flash**, and **Gradio**. Designed to handle complex, multi-step workflows autonomously, Sidekick can plan tasks, ask clarifying questions, browse the web using headless browser automation, run Python code, execute database queries, and persist conversation states across sessions.

---

## ✨ Features

- **Multi-Agent Architecture (Planner + Worker + Evaluator):**
  - **Planner:** Breaks down user requests into structured execution plans and identifies missing information.
  - **Worker:** Autonomous agent equipped with tool-calling capabilities to execute plans step-by-step.
  - **Evaluator:** Evaluates output against specified **Success Criteria** to ensure quality and completion before delivering the final answer.
- **Clarifying Questions Support:** Automatically identifies ambiguous prompts and prompts the user for clarification before running long tasks.
- **Persistent SQL Memory:** Uses SQLite database checkpointing (`SqliteSaver`) to retain conversation history and context per session/username across application restarts.
- **Rich Toolset Integration:**
  - 🌐 **Browser Automation:** Playwright Chromium integration for deep web scraping and site navigation.
  - 🔍 **Web & Wiki Search:** Google Serper API and Wikipedia API search integration.
  - 🐍 **Python REPL:** Executes Python code dynamically to solve logic or math problems.
  - 🗄️ **SQLite Query Tool:** Interacts with local databases using SQL queries.
  - 📁 **File System Management:** Sandboxed file creation and reading in the `sandboxx/` directory.
  - 🔔 **Push Notifications:** Pushover API integration to alert users on task updates.

---

## 📁 Project Structure

```text
├── app.py                # Gradio Web UI and session lifecycle manager
├── sidekick.py           # LangGraph state graph, agent definitions, and evaluator logic
├── sidekick_tools.py     # Tool bindings (Playwright, Python REPL, Serper, SQLite, etc.)
├── sandboxx/             # Sandboxed workspace directory for file outputs
├── sidekick_app.db       # Local SQLite database for SQL Query tool tasks
├── sidekick_memory.sqlite# Persistent database for LangGraph conversation checkpoints
├── .env                  # Environment variables (API keys)
└── README.md             # Project documentation