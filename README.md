# COSMOS Proposal Automation

A Python-based web automation application built with **Playwright**, **Flask**, and **uv** to automate proposal processing in the COSMOS insurance application.

The application provides a web-based dashboard where users can enter their COSMOS credentials, start automation, monitor the progress, and process proposals automatically.

---

## 🚀 Features

- Automates COSMOS proposal processing using Playwright
- Web-based frontend for starting automation
- Username and password entered directly through the UI
- Automatically logs into COSMOS
- Navigates to the Inbox and ILRole sections
- Reads and processes proposals
- Opens IL Details for each proposal
- Detects predefined IL error conditions
- Automatically submits applicable proposals
- Supports proposal pagination
- Displays automation progress in real time
- Tracks processed, submitted, and failed proposals
- Uses Chromium for browser automation
- Uses `uv` for Python environment and dependency management
- Flask backend with JavaScript frontend

---

## 🏗️ Project Structure

```text
COSMOS-Automation/
│
├── backend/
│   ├── app.py
│   └── automation.py
│
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
│
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── pyproject.toml
```

---

## 🛠️ Tech Stack

- **Python**
- **Flask**
- **Playwright**
- **Chromium**
- **JavaScript**
- **HTML**
- **CSS**
- **uv**
- **Git/GitHub**

---

# 📋 Prerequisites

Before running the project, make sure you have the following installed:

- Python 3.14+
- Git
- uv

You can verify Python:

```bash
python --version
```

Verify `uv`:

```bash
uv --version
```

---

# 📥 Clone the Repository

Clone the repository from GitHub:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
```

Navigate into the project:

```bash
cd YOUR_REPOSITORY
```

---

# ⚡ Setup Using uv

This project uses **uv** for Python environment and dependency management.

## 1. Create the virtual environment

```bash
uv venv
```

This creates:

```text
.venv/
```

---

## 2. Activate the virtual environment

### Windows CMD

```cmd
.venv\Scripts\activate
```

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

You can also run commands directly using `uv` without manually activating the environment.

---

# 📦 Install Dependencies

Install the project dependencies from `requirements.txt`:

```bash
uv pip install -r requirements.txt
```

---

# 🌐 Install Playwright Chromium

The project uses Playwright with Chromium.

Install only the Chromium browser:

```bash
uv run playwright install chromium
```

This installs the browser required by the automation.

---

# 📄 requirements.txt

The project requires:

```text
Flask
playwright
python-dotenv
```

Install them with:

```bash
uv pip install -r requirements.txt
```

---

# 🔐 Environment Variables

If environment variables are used, create a `.env` file in the project root.

Example:

```env
COSMOS_URL=http://your-cosmos-url
```

> **Important:** Never commit credentials, passwords, API keys, tokens, or other sensitive information to GitHub.

Add `.env` to `.gitignore`.

---

# ▶️ Run the Application

Start the Flask backend from the project root:

```bash
uv run python backend/app.py
```

The application will start on:

```text
http://127.0.0.1:5000
```

Open the URL in your browser:

```text
http://127.0.0.1:5000
```

---