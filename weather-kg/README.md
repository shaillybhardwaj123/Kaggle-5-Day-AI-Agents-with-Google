# 🌦️ Weather Assistant Agent

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-v2.2-green.svg)](https://adk.dev/)
[![Gemini Flash](https://img.shields.io/badge/Model-Gemini%20Flash-orange.svg)](https://deepmind.google/technologies/gemini/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

A premium, lightweight ReAct (Reasoning and Acting) agent powered by the **Google Agent Development Kit (ADK)** and the **Gemini** generative models. It acts as an intelligent assistant capable of dynamically resolving weather information and time updates via tool integration.

---

## 🚀 Key Features

* **⚡ Smart ReAct Loop**: Seamless reasoning and tool-calling loop using `gemini-flash-latest`.
* **🛠️ Integrated Utility Tools**:
  * `get_weather`: Simulates real-time weather retrieval for cities (e.g., San Francisco, New York).
  * `get_current_time`: Fetches timezone-aware time mapping (supporting America/Los_Angeles timezone).
* **🔌 Dynamic Authentication**: Auto-detects environment credentials. Gracefully falls back from **Vertex AI** (GCP) to **Google AI Studio** (`GEMINI_API_KEY` or `GOOGLE_API_KEY`) for local prototyping.
* **💻 Interactive Dev UI**: Integrated local web playground to trace events, inspect tool calling, and preview agent behaviour.

---

## 📂 Project Structure

```bash
weather-assistant/
├── app/                      # Main package containing agent logic
│   ├── agent.py              # 🧠 Core Agent definition and Tool declarations
│   ├── fast_api_app.py       # 🌐 FastAPI wrapper exposing ASGI interface
│   └── app_utils/            # 🛠️ Telemetry & typing configurations
├── tests/                    # Unit, integration, and behavioral eval cases
├── agents-cli-manifest.yaml  # 📝 CLI manifest configuration
├── GEMINI.md                 # 🤖 AI-assisted development context
├── pyproject.toml            # 📦 Dependencies managed via uv
└── README.md                 # 📖 Project documentation
```

---

## 🛠️ Setup & Installation

### Prerequisites
Before you start, ensure you have installed:
* **[uv](https://docs.astral.sh/uv/getting-started/installation/)**: Fast Python package manager.
* **[agents-cli](https://github.com/google/agents-cli)**: Official Agent lifecycle CLI.

### Quick Start

1. **Install CLI Skills**:
   ```bash
   uvx google-agents-cli setup
   ```

2. **Install Project Dependencies**:
   ```bash
   agents-cli install
   ```

3. **Configure Environment Variables**:
   Export your Gemini API key (defaults to Google AI Studio):
   ```bash
   # Windows PowerShell
   $env:GEMINI_API_KEY="your-gemini-api-key"

   # Unix/macOS Bash
   export GEMINI_API_KEY="your-gemini-api-key"
   ```

4. **Launch the Web Playground**:
   Start the interactive dashboard:
   ```bash
   agents-cli playground
   ```
   Open **[http://127.0.0.1:8080/dev-ui/?app=app](http://127.0.0.1:8080/dev-ui/?app=app)** in your browser to chat with the agent!

---

## 💻 Command Reference

| Command | Action |
| :--- | :--- |
| **`agents-cli playground`** | Launch local web server and interactive UI dashboard. |
| **`agents-cli lint`** | Run code quality and type checks. |
| **`agents-cli eval run`** | Run behavioral evaluation suites. |
| **`uv run pytest tests/`** | Execute unit and integration tests. |

---

## 📈 Next Steps

* **Enhance Tools**: Expand custom logic inside `app/agent.py` to call real APIs like OpenWeatherMap or Open-Meteo.
* **Scale Infrastructure**: Easily add cloud deployment configurations (Cloud Run, GKE, or Agent Runtime) with:
  ```bash
  agents-cli scaffold enhance
  ```
