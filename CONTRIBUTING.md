# NLP CLI - Contributor Guide

Thank you for your interest in contributing! This project aims to bridge the gap between human language and shell commands.

## 📂 Project Structure

*   `nlp_cli/`: Main package source code.
    *   `main.py`: CLI entry point (Typer).
    *   `local_translator.py`: Orchestrates translation logic.
    *   `intent_classifier.py`: The ML brain (SVM model).
    *   `command_templates.py`: Dictionary mapping intents to OS commands.
    *   `training_data.py`: The dataset (can be extended).
*   `tests/`: Unit tests using `pytest`.

## 🧪 Running Tests

We use `pytest` to ensure reliability.

```bash
pip install pytest
pytest
```

## 🧠 Adding New Commands

1.  Open `nlp_cli/training_data.py` and add example phrases for your new intent.
2.  Open `nlp_cli/command_templates.py` and define the command syntax for Windows/Linux.
3.  Run `nlp retrain` to update the model.

## 🚀 Pull Requests

1.  Fork the repo.
2.  Create a feature branch.
3.  Add your changes + tests.
4.  Submit a PR!

Happy Coding! 🤖

