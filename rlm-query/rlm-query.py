#!/usr/bin/env python3
"""
rlm-query.py — Query files using Recursive Language Models (RLM) with Anthropic.

Loads a file (txt, md, or pdf), prepends it as context, and sends a query
through the RLM library for multi-step reasoning.

Usage:
    python rlm-query.py <file_path> "<question>"
    python rlm-query.py <file_path> "<question>" --verbose
    python rlm-query.py <file_path> "<question>" --model claude-sonnet-4-20250514

Examples:
    python rlm-query.py big-document.txt "What are all the Medicare rate changes mentioned?"
    python rlm-query.py report.pdf "Summarize the key findings" --verbose
    python rlm-query.py notes.md "List all action items" --model claude-sonnet-4-20250514

API Key:
    Set ANTHROPIC_API_KEY environment variable, or point RLM_CONFIG_PATH to a JSON
    file with {"api_keys": {"anthropic": "sk-ant-..."}}
"""

import argparse
import json
import os
import sys

DEFAULT_MODEL = "claude-sonnet-4-20250514"


def load_api_key() -> str:
    """Read the Anthropic API key from environment or config file."""
    # 1. Check environment variable first
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key

    # 2. Check config file
    config_path = os.environ.get("RLM_CONFIG_PATH")
    if not config_path:
        print(
            "Error: No API key found. Set ANTHROPIC_API_KEY environment variable,\n"
            "or set RLM_CONFIG_PATH to a JSON config file containing the key.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found at {config_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse config JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # Try api_keys.anthropic first (canonical), fall back to top-level alias
    key = None
    if "api_keys" in config and "anthropic" in config["api_keys"]:
        key = config["api_keys"]["anthropic"]
    elif "anthropic_api_key" in config:
        key = config["anthropic_api_key"]

    if not key:
        print(
            "Error: No Anthropic API key found in config (expected api_keys.anthropic)",
            file=sys.stderr,
        )
        sys.exit(1)

    return key


def load_file(file_path: str) -> str:
    """Load file contents. Supports .txt, .md, and .pdf."""
    if not os.path.isfile(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        try:
            import pymupdf  # PyMuPDF
        except ImportError:
            try:
                import fitz as pymupdf  # older PyMuPDF import name
            except ImportError:
                print(
                    "Error: pymupdf (PyMuPDF) is required for PDF files. "
                    "Install with: pip install pymupdf",
                    file=sys.stderr,
                )
                sys.exit(1)

        try:
            doc = pymupdf.open(file_path)
            text_parts = []
            for page_num, page in enumerate(doc, 1):
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(f"--- Page {page_num} ---\n{page_text}")
            doc.close()
            if not text_parts:
                print(
                    f"Warning: PDF appears to contain no extractable text: {file_path}",
                    file=sys.stderr,
                )
                return "(empty PDF)"
            return "\n\n".join(text_parts)
        except Exception as e:
            print(f"Error: Failed to read PDF: {e}", file=sys.stderr)
            sys.exit(1)

    elif ext in (".txt", ".md", ".json", ".csv", ".log", ".xml", ".html", ".yaml", ".yml"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                return f.read()
        except Exception as e:
            print(f"Error: Failed to read file: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        # Try reading as text anyway
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error: Cannot read file with extension '{ext}': {e}", file=sys.stderr)
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Query files using Recursive Language Models (RLM) with Anthropic.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python rlm-query.py document.txt "What are the key points?"
  python rlm-query.py report.pdf "Summarize the findings" --verbose
  python rlm-query.py data.md "List all action items" --model claude-sonnet-4-20250514
  python rlm-query.py big-file.txt "Extract all dates mentioned" --max-iterations 20
        """,
    )
    parser.add_argument("file_path", help="Path to the file to analyze (.txt, .md, .pdf, etc.)")
    parser.add_argument("question", help="The question to ask about the file contents")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Anthropic model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show RLM's reasoning steps and iteration details",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=30,
        help="Maximum reasoning iterations (default: 30)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=1,
        help="Maximum recursion depth (default: 1)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Maximum execution time in seconds (default: no limit)",
    )

    args = parser.parse_args()

    # Load API key
    api_key = load_api_key()

    # Set env var as well (some libraries check it)
    os.environ["ANTHROPIC_API_KEY"] = api_key

    # Load file
    file_content = load_file(args.file_path)
    file_name = os.path.basename(args.file_path)

    # Build the prompt: file content as context + question
    prompt = (
        f"=== DOCUMENT: {file_name} ===\n"
        f"{file_content}\n"
        f"=== END DOCUMENT ===\n\n"
        f"Question: {args.question}"
    )

    # Initialize and run RLM
    try:
        from rlm import RLM

        model = RLM(
            backend="anthropic",
            backend_kwargs={
                "api_key": api_key,
                "model_name": args.model,
            },
            max_iterations=args.max_iterations,
            max_depth=args.max_depth,
            max_timeout=args.timeout,
            verbose=args.verbose,
        )

        result = model.completion(prompt, root_prompt=args.question)

        # Print the final answer
        print(result.response)

        # Print usage stats if verbose
        if args.verbose and result.usage_summary:
            usage = result.usage_summary
            print("\n--- Usage ---", file=sys.stderr)
            print(f"  Input tokens:  {usage.total_input_tokens:,}", file=sys.stderr)
            print(f"  Output tokens: {usage.total_output_tokens:,}", file=sys.stderr)
            if usage.total_cost is not None:
                print(f"  Cost:          ${usage.total_cost:.6f}", file=sys.stderr)
            print(f"  Time:          {result.execution_time:.1f}s", file=sys.stderr)

    except ImportError:
        print("Error: rlm library not installed. Install with: pip install rlms", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
