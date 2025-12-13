# 🧠 NLP CLI (Natural Language Shell)

> **"Talk to your terminal like a human."**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![ML](https://img.shields.io/badge/ML-scikit--learn-orange.svg)](https://scikit-learn.org)

**NLP CLI** is an intelligent command-line tool that translates natural language into shell commands. It uses a **Local Machine Learning Model (TF-IDF + SVM)** to understand your intent, making it fast, privacy-focused, and offline-capable.

---

## ✨ Features

*   **🗣️ Natural Language**: Say *"scan ports on google"* instead of remembering complex `nmap` flags.
*   **🔒 100% Offline**: No API keys, no cloud, no latency. Runs locally on your machine.
*   **💻 Cross-Platform**: Automatically generates **PowerShell** commands on Windows and **Bash** on Linux/macOS.
*   **🛡️ Safety First**: Detects dangerous commands (`rm -rf`) and asks for ambiguity resolution if unsure.
*   **🧠 Self-Learning**: Supports an RLHF-style loop where you can teach it new phrases.

---

## 🚀 Installation

### Option 1: For Developers (Recommended)
Clone the repo and install in editable mode:

```bash
git clone https://github.com/tejuskapoor/nlp-cli.git
cd nlp-cli
pip install -e .
```

### Option 2: Requirements
```bash
pip install -r requirements.txt
```

---

## 📖 Usage

Run `nlp` followed by your request in quotes.

### 1. Basic Commands
```bash
nlp "create a folder named Project"
nlp "delete all txt files"
```

### 2. Multi-Step Logic (New!)
Chain commands naturally:
```bash
nlp "create secrets.txt and write 'password123' in it"
```
*(The tool understands context: "in it" refers to `secrets.txt`)*

### 3. Cybersecurity & Admin
Advanced context-aware commands:
```bash
# Windows
nlp "get wifi password for HomeNetwork"
# -> netsh wlan show profile name="HomeNetwork" key=clear

# Network
nlp "scan ports on google.com"
# -> nmap google.com (Linux) OR Test-NetConnection (Windows)
```

---

## 🧠 How It Works (Architecture)

1.  **Intent Classification**: A local SVM model classifies your text into 50+ intents (e.g., `git_status`, `port_scan`).
2.  **Entity Extraction**: Regex and rule-based logic extract filenames, IPs, and paths.
3.  **Context Resolution**: Maintains session state to resolve pronouns like "it".
4.  **Command Generation**: Fills OS-specific templates (PowerShell/Bash).

---

## 🛠️ Development

To retrain the model with your own data:

```bash
# 1. Add new examples interactively
nlp learn

# 2. Retrain the model
nlp retrain
```

---

## 📄 License

MIT License - feel free to modify and use it!

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/tejuskapoor">Tejus Kapoor</a>
</p>
