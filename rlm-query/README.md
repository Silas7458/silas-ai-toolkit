# RLM Query

Query large documents using **Recursive Language Models (RLM)** with Anthropic Claude.

## What is RLM?

Recursive Language Models solve the "context rot" problem -- where LLMs degrade on long inputs as important details get buried in massive context windows. RLM breaks the problem into recursive reasoning steps, letting a small model systematically work through large documents.

**The result:** GPT-4o mini + RLM beat full GPT-4o by 34 points on long-document benchmarks. The technique works natively with Anthropic Claude models (Haiku, Sonnet, Opus).

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

The script reads your Anthropic API key from a JSON config file. Set the `RLM_CONFIG_PATH` environment variable to point to your config file:

```bash
export RLM_CONFIG_PATH="/path/to/your/config.json"
```

Your config file should have this structure:

```json
{
  "api_keys": {
    "anthropic": "sk-ant-..."
  }
}
```

Alternatively, set the `ANTHROPIC_API_KEY` environment variable directly.

## Usage

```bash
# Basic query
python rlm-query.py document.txt "What are the key findings?"

# Query a PDF
python rlm-query.py report.pdf "Summarize the methodology section"

# Verbose mode (shows reasoning steps)
python rlm-query.py big-file.txt "Extract all dates mentioned" --verbose

# Use a specific model
python rlm-query.py data.md "List all action items" --model claude-sonnet-4-20250514

# Control reasoning depth
python rlm-query.py huge-doc.pdf "Find contradictions" --max-iterations 20 --max-depth 2
```

## Supported File Types

- `.txt`, `.md`, `.json`, `.csv`, `.log`, `.xml`, `.html`, `.yaml`, `.yml` -- read as text
- `.pdf` -- extracted via PyMuPDF with page markers

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--model` | `claude-sonnet-4-20250514` | Anthropic model to use |
| `--verbose` | off | Show RLM reasoning steps and token usage |
| `--max-iterations` | 30 | Maximum reasoning iterations |
| `--max-depth` | 1 | Maximum recursion depth |
| `--timeout` | none | Maximum execution time in seconds |

## Why Use This?

- **Long documents:** RLM handles 100+ page PDFs without losing details in the middle
- **Cost efficient:** Use cheaper models (Haiku, Sonnet) and get better results than expensive models on raw context
- **Claude-native:** Built for Anthropic's API -- no OpenAI dependency required
- **Simple CLI:** One command, one file, one question -- get a thorough answer
