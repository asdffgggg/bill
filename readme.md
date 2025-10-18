# BillAI

A browser for congressional bills and laws with AI analysis.

# Setup

- Install requirements with:
  ```
  pip install -r requirements.txt
  ```
- Set Congress API key in `CONGRESSAPIKEY` environment variable
- Set OpenAI API key in `OPENAI_API_KEY` environment variable
- Install [Ollama](https://ollama.com/download)
- Install gemma3 model:
  ```
  ollama pull gemma3
  ```
- Run with:
  ```
  python main.py
  ```
