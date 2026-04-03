"""Generate repeated LLM responses for SCORE-style expert grading.

This script standardises the response generation stage across providers so the
repository clearly shows how responses were collected before human grading.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd
from openai import OpenAI
import anthropic

from config import GenerationConfig, get_api_key
from utils import read_tabular_file, write_tabular_file



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate repeated LLM responses.")
    parser.add_argument("--provider", required=True, choices=["openai", "anthropic", "deepseek"])
    parser.add_argument("--model", required=True, help="Model name to query.")
    parser.add_argument("--input", required=True, help="Path to the question file.")
    parser.add_argument("--question-column", required=True, help="Column containing the questions.")
    parser.add_argument("--system-role", required=True, help="System instruction or role prompt.")
    parser.add_argument("--output", required=True, help="Output spreadsheet path.")
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--top-p", type=float, default=0.6)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--num-attempts", type=int, default=3)
    parser.add_argument("--max-questions", type=int, default=20)
    return parser.parse_args()



def load_questions(input_path: str, question_column: str, max_questions: int) -> List[str]:
    df = read_tabular_file(input_path)
    if question_column not in df.columns:
        raise ValueError(f"Column '{question_column}' not found in {input_path}")

    questions = (
        df[question_column]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )
    return questions[:max_questions]



def generate_openai_response(client: OpenAI, model: str, system_role: str, question: str,
                             temperature: float, top_p: float, max_tokens: int) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_role},
            {"role": "user", "content": question},
        ],
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""



def generate_anthropic_response(client: anthropic.Anthropic, model: str, system_role: str, question: str,
                                temperature: float, top_p: float, max_tokens: int) -> str:
    response = client.messages.create(
        model=model,
        system=system_role,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        messages=[
            {"role": "user", "content": question},
        ],
    )
    return response.content[0].text if response.content else ""



def build_client(provider: str):
    api_key = get_api_key(provider)
    if not api_key:
        raise ValueError(f"Missing API key for provider '{provider}'. Fill it in your .env file.")

    if provider == "openai":
        return OpenAI(api_key=api_key)
    if provider == "deepseek":
        return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    if provider == "anthropic":
        return anthropic.Anthropic(api_key=api_key)

    raise ValueError(f"Unsupported provider: {provider}")



def main() -> None:
    args = parse_args()
    config = GenerationConfig(
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_tokens,
        num_attempts=args.num_attempts,
        max_questions=args.max_questions,
    )

    questions = load_questions(args.input, args.question_column, config.max_questions)
    client = build_client(args.provider)

    response_table = pd.DataFrame({args.question_column: questions})

    for attempt in range(1, config.num_attempts + 1):
        attempt_responses = []
        for idx, question in enumerate(questions, start=1):
            print(f"[{attempt}/{config.num_attempts}] Generating response for question {idx}/{len(questions)}")
            try:
                if args.provider in {"openai", "deepseek"}:
                    text = generate_openai_response(
                        client=client,
                        model=args.model,
                        system_role=args.system_role,
                        question=question,
                        temperature=config.temperature,
                        top_p=config.top_p,
                        max_tokens=config.max_tokens,
                    )
                else:
                    text = generate_anthropic_response(
                        client=client,
                        model=args.model,
                        system_role=args.system_role,
                        question=question,
                        temperature=config.temperature,
                        top_p=config.top_p,
                        max_tokens=config.max_tokens,
                    )
                attempt_responses.append(text)
            except Exception as exc:  # noqa: BLE001
                attempt_responses.append(f"ERROR: {exc}")

        response_table[f"Response_Attempt_{attempt}"] = attempt_responses

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_tabular_file(response_table, output_path)
    print(f"Saved generated responses to: {output_path}")


if __name__ == "__main__":
    main()
