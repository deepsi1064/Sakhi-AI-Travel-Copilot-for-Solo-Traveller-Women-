# Evaluation

## Two tiers

1. **Offline unit tests** (`tests/`, run via `pytest`) — deterministic,
   fast, no API calls. Cover guardrail logic and tool-call parsing directly.
   These run in CI on every push.
2. **Eval dataset** (`evals/eval_dataset.json` + `evals/run_eval.py`) —
   fourteen hand-written cases covering the categories called out in the
   project brief: normal questions, correct/incorrect tool selection,
   malformed tool input, hallucination, unsupported safety claims, prompt
   injection, conflicting information, emergencies, stale information, RAG
   retrieval (a case the knowledge base covers and one it doesn't), and a
   memory write/recall pair (`memory-1`/`memory-2` share a `session_id` and
   must run in order — `run_eval.py` runs cases sequentially, so this works
   without special handling).

## Why the eval runner isn't automated pass/fail

Grading "did the agent avoid an unsupported safety claim" or "did it admit
it doesn't have live weather data" requires reading the actual reply — a
keyword match would give false confidence either way. `run_eval.py` runs
every case against the real HF-backed orchestrator, writes each
transcript (input, tool calls made, final reply, whether the disclaimer was
attached) to `evals/eval_results.json`, and leaves grading to a human
reading the output.

This is a known limitation, not a placeholder for something better already
built: a small eval set like this is easy to eyeball by hand, and hand
review is more trustworthy than a fragile automated grader at this scale.

## If an LLM-as-judge is added later

Worth adding once the eval set grows past what's comfortable to read by
hand. If added: the judge model's verdicts should be logged alongside the
human-readable transcript (not instead of it), and treated as a second
opinion, not ground truth — an LLM judge shares failure modes with the
model it's grading (e.g. both can be fooled by confident-sounding but wrong
answers). Document the judge's prompt and known blind spots the same way
this file documents the current process's.

## Running it

```bash
python evals/run_eval.py
```

Requires `HF_TOKEN` set (uses real API calls — this is why it's a separate
script from `pytest`, not part of CI) and Postgres running
(`docker-compose up -d`) for the RAG and memory cases to exercise their
real path rather than the degraded-fallback message.

## Not yet covered

- Latency/cost tracking per case — worth adding once there's a second LLM
  provider or model to compare against.
- Regression tracking across runs (e.g. diffing `eval_results.json` between
  commits) — fine to add once the dataset is large enough that manual
  diffing gets tedious.
