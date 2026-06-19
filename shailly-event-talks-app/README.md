<div align="center">
  <h1>⚡ BigQuery Release Notes Hub</h1>
  <p>An elegant, high-fidelity developer dashboard to aggregate, split, filter, and share Google Cloud BigQuery Release Notes.</p>

  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/Flask-3.0.3-black?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
    <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5" />
    <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3" />
    <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript" />
    <img src="https://img.shields.io/badge/X%20%2F%20Twitter-000000?style=for-the-badge&logo=x&logoColor=white" alt="Twitter Sharing" />
    <img src="https://komarev.com/ghpvc/?username=shaillybhardwaj123&label=VIEWS&style=for-the-badge&color=38bdf8" alt="Views"/>
  </p>

  <!-- Animated Underline -->
  <div style="width: 150px; height: 3px; background: linear-gradient(90deg, #38bdf8, #8b5cf6, #38bdf8); background-size: 200% auto; border-radius: 4px; margin: 15px auto;"></div>
  
  <p style="font-size: 1.15rem; color: #94a3b8; margin-top: 12px;">
    ⚡ <strong>Live Parser Proxy</strong> • <strong>10m Cache</strong> • <strong>Interactive X Composer</strong>
  </p>
</div>



## 📖 Executive Summary & Data Context

> ⚡ **Proxy Caching & Parsing:** The official BigQuery release notes Atom feed is structured on a per-day basis, combining various categories (Features, Issues, Changes) in a single block. This app automatically fetches the feed, proxies it to avoid CORS constraints, parses daily blocks into separate, structured items, and caches them to avoid feed query spam.

This repository implements a **Developer Dashboard and Proxy** that parses the official XML feeds from Google Cloud, restructuring raw CDATA HTML into distinct, searchable entries. By cleaning the raw links and adding real-time sharing/export capabilities, the dashboard provides developers and DevOps engineers with immediate visibility into Google Cloud platform updates.

---

## 🛠️ Tech Stack & Architecture

<div align="center">
  
| 🧠 **Flask Backend Proxy** | 🎨 **Vanilla CSS Variables** | ⚡ **Vanilla JS State** | 📥 **Dynamic Export** |
|:---:|:---:|:---:|:---:|
| Python 3, requests | Custom Theme Variables | DOM State Tracker | UTF-8 BOM CSV |
| **🔋 Server-Side Cache** | 🌓 **Theme Persist** | 📋 **Micro-Feedback** | 🐦 **X Intent Linker** |
| 10-Minute memory cache | `localStorage` Sync | Clipboard Copy Animation | 23-Character Shortener |

</div>

---

## 📐 Systems Architecture & Pipeline

```mermaid
graph TD
    A[Google Cloud RSS Feed] -->|Atom XML| B(app.py Flask Backend)
    B -->|BS4 HTML Parsing & Link Cleaning| C{In-Memory Cache}
    C -->|JSON API Payload| D[script.js Frontend]
    D -->|1. Filter Categories| E[Interactive DOM Cards]
    D -->|2. Esc-key Handlers| E
    D -->|3. Search Term Highlight| E
    E -->|Copy Button| F[Clipboard Checkmark Animation]
    E -->|Tweet Button| G[280-char X Intent Composer]
    E -->|Export Button| H[UTF-8 BOM CSV Download]
    
    style A fill:#0ea5e9,stroke:#0284c7,stroke-width:2px,color:#fff
    style B fill:#334155,stroke:#1e293b,stroke-width:2px,color:#fff
    style C fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff
    style D fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#fff
    style E fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#fff
    style F fill:#e76f51,stroke:#b53d20,stroke-width:2px,color:#fff
    style G fill:#1da1f2,stroke:#0d8bf0,stroke-width:2px,color:#fff
    style H fill:#f4a261,stroke:#e76f51,stroke-width:2px,color:#fff
```

---

## 🎨 User Interface Showcase

The application has been styled with a custom dark-themed console theme (and a clean, high-contrast light mode toggle) with responsive grids and glassmorphism.

<p align="center">
  <img src="./static/mockup.jpg" width="850" alt="BigQuery Release Notes Hub Interface Mockup" style="border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 10px 30px rgba(0,0,0,0.55);" />
</p>

---

## 📁 Repository Directory Structure

```directory
shailly-event-talks-app/
│
├── 📂 templates/
│   └── 📄 index.html          # Semantic HTML5 layout, custom dialog markup
│
├── 📂 static/
│   ├── 🎨 style.css           # Token variables, CSS highlights, orbit transitions
│   ├── ⚡ script.js           # AJAX operations, highlights parser, clipboard transitions
│   └── 🖼️ mockup.jpg          # Application GUI mockup interface
│
├── 🐍 app.py                  # Core backend routing, proxies, BeautifulSoup parsing
├── 📄 run.ps1                 # Powershell startup automation runner
├── 📄 requirements.txt        # Python library declarations
├── 📄 README.md               # Visual documentation manual
└── ⚙️ .gitignore              # Exclusion file definitions
```

---

## ⚡ Quick Setup & Running Guide

### 📂 Step 1: Clone & Navigate
Open your CLI terminal and enter the project folder:
```bash
cd "shailly-event-talks-app"
```

### 🐍 Step 2: Set up Virtual Environment
Create and activate an isolated environment to prevent library collision:
```bash
# Create venv
python -m venv venv

# Activate venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Windows Command Prompt (CMD):
venv\Scripts\activate.bat
# On Linux/macOS:
source venv/bin/activate
```

### 📦 Step 3: Install Packages
Install dependencies from `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 🚀 Step 4: Spin up the Web Server
Launch the Flask development server:
```bash
python app.py
```
> [!TIP]
> **Windows Users**: You can run `.\run.ps1` in PowerShell. This automatically checks dependency status, installs missing packages, and spins up the server.

### 🌐 Step 5: Open in Browser
Open your browser and navigate to:
```text
http://127.0.0.1:5000/
```

---

## 🤝 Contributing & License
Distributed under the **MIT License**. Contributions, pull requests, and forks are welcome! Please open an issue to propose features or enhancements.
