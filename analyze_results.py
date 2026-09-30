"""Сводка результатов по режиму и пяти категориям ЛР2 (stdlib only)."""
import argparse
import csv
from collections import defaultdict
from pathlib import Path
import statistics


def pct(values, p):
    values = sorted(values)
    if not values:
        return None
    i = (len(values) - 1) * p
    lo = int(i)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (i - lo)


def fnum(row, key):
    value = row.get(key, "")
    return None if value in ("", "None", None) else float(value)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results_csv")
    ap.add_argument("--out", default="category_summary.csv")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.results_csv, encoding="utf-8")))
    groups = defaultdict(list)
    for r in rows:
        groups[(r["mode"], r["category"])].append(r)

    out_rows = []
    for (mode, category), group in sorted(groups.items()):
        elapsed = [float(r["elapsed_ms"]) for r in group]
        model_calls = [fnum(r, "model_calls") for r in group]
        prompt_tokens = [fnum(r, "prompt_tokens") for r in group]
        completion_tokens = [fnum(r, "completion_tokens") for r in group]
        usable_calls = [v for v in model_calls if v is not None]
        usable_prompt = [v for v in prompt_tokens if v is not None]
        usable_completion = [v for v in completion_tokens if v is not None]
        out_rows.append({
            "mode": mode,
            "category": category,
            "episodes": len(group),
            "successes": sum(int(r["success"]) for r in group),
            "success_rate": round(sum(int(r["success"]) for r in group) / len(group), 4),
            "mean_steps": round(statistics.mean(float(r["steps"]) for r in group), 3),
            "mean_tool_calls": round(statistics.mean(float(r["tool_calls"]) for r in group), 3),
            "mean_model_calls": round(statistics.mean(usable_calls), 3) if usable_calls else "",
            "mean_prompt_tokens": round(statistics.mean(usable_prompt), 3) if usable_prompt else "",
            "mean_completion_tokens": round(statistics.mean(usable_completion), 3) if usable_completion else "",
            "p50_ms": round(pct(elapsed, .5), 3),
            "p95_ms": round(pct(elapsed, .95), 3),
        })

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        writer.writeheader()
        writer.writerows(out_rows)

    print(Path(args.out).resolve())


if __name__ == "__main__":
    main()
