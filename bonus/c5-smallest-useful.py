#!/usr/bin/env python3
"""C5: compare the two lab quantizations on a small, reproducible task set."""
from __future__ import annotations

import json
import pathlib
import re
import sys
import time

import httpx

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
import labkit  # noqa: E402


CASES = [
    ("arithmetic", "Return only the integer result of 17 * 23.", [r"\b391\b"]),
    (
        "grounded fact",
        "Context: Atlas rotates credentials every 90 days. According to the context, "
        "how often are credentials rotated? Answer with the number and unit only.",
        [r"\b90\b", r"day"],
    ),
    ("translation", "Translate 'xin chào' to English. Return one word only.", [r"\bhello\b"]),
    (
        "sorting",
        "Sort these integers in ascending order and return CSV only: 11, 2, 7, 3",
        [r"2\s*,\s*3\s*,\s*7\s*,\s*11"],
    ),
    (
        "instruction",
        "Reply with exactly the word BLUE in uppercase and nothing else.",
        [r"^\s*BLUE\s*$"],
    ),
]


def evaluate(model: pathlib.Path, label: str, port: int) -> list[dict]:
    rows: list[dict] = []
    with labkit.serve_bg(str(model), port=port):
        for name, prompt, patterns in CASES:
            started = time.perf_counter()
            response = httpx.post(
                f"http://127.0.0.1:{port}/v1/chat/completions",
                json={
                    "model": "local",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                    "max_tokens": 64,
                },
                timeout=180,
            )
            response.raise_for_status()
            answer = response.json()["choices"][0]["message"]["content"].strip()
            passed = all(re.search(pattern, answer, re.I | re.S) for pattern in patterns)
            rows.append(
                {
                    "quant": label,
                    "case": name,
                    "pass": passed,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                    "answer": answer,
                }
            )
            print(f"{label:12s} {name:14s} {'PASS' if passed else 'FAIL'}  {answer[:70]!r}")
    return rows


def main() -> int:
    active = labkit.load_active()
    root = labkit.repo_root()
    primary = root / active["primary_model"]
    compare = root / active["compare_model"]
    rows = evaluate(primary, active["primary_quant"], 8092)
    rows.extend(evaluate(compare, active["compare_quant"], 8092))

    summary = []
    for label in (active["primary_quant"], active["compare_quant"]):
        selected = [row for row in rows if row["quant"] == label]
        summary.append(
            [
                label,
                f"{sum(row['pass'] for row in selected)}/{len(selected)}",
                f"{sum(row['latency_ms'] for row in selected) / len(selected):.1f}",
            ]
        )

    for row in rows:
        row["answer_md"] = row["answer"].replace("`", "'")[:240]
    details = "\n".join(
        f"- **{row['quant']} / {row['case']}** ({'pass' if row['pass'] else 'fail'}, "
        f"{row['latency_ms']:.1f} ms): `{row['answer_md']}`"
        for row in rows
    )
    md = f"""# Bonus C5 - Smallest useful quantization

Model `{active['model']}` · host `{labkit.host_tag()}` · temperature 0 · 5 constrained prompts

{labkit.md_table(['Quantization', 'Checks passed', 'Mean E2E (ms)'], summary)}

The checks are deliberately transparent substring/format checks, not an LLM judge. They
cover arithmetic, grounded extraction, translation, sorting, and strict instruction
following. This is a smoke-quality gate rather than a broad model-quality benchmark.

## Observed outputs

{details}

## Finding

Use the measured pass counts together with the base latency and size report. If both
quantizations pass this small gate, that does **not** prove equal quality; it only means
no next-lower-quant failure was observed in this narrow set. In that case the safer
deployment choice is the higher-quality quant unless the memory saving is operationally
necessary.
"""
    path = labkit.write_report("bonus-c5-smallest-useful.md", md, rows)
    print(f"==> Wrote {path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
