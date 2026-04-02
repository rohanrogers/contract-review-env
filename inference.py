#!/usr/bin/env python3
"""
Baseline inference script for Contract Review Environment
Uses OpenAI-compatible API with structured [START]/[STEP]/[END] logging
as required by the OpenEnv evaluation spec.
"""

import asyncio
import os
import json
import sys
from typing import Dict, List, Optional
import httpx
from openai import OpenAI

# ── Required environment variables ────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "gpt-4")
HF_TOKEN     = os.getenv("HF_TOKEN")

# ── Runtime configuration ─────────────────────────────────────────────────────
ENV_URL                 = os.getenv("ENV_URL", "http://localhost:7860")
TEMPERATURE             = 0.7
MAX_TOKENS              = 2000
MAX_STEPS               = 20
SUCCESS_SCORE_THRESHOLD = 0.5
TASK_TIMEOUT_SECONDS    = 900   # 15 min per task; 3 tasks = 45 min max → judges allow 20 min total
DEBUG                   = os.getenv("DEBUG", "false").lower() == "true"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ── Structured logging helpers (must match spec exactly) ──────────────────────

def log_start(*, task: str, env: str, model: str) -> None:
    print(json.dumps({"event": "START", "task": task, "env": env, "model": model}), flush=True)


def log_step(*, step: int, action, reward: float, done: bool, error=None) -> None:
    # 'error' field is always emitted (null when no error) to match spec field ordering exactly
    payload = {
        "event": "STEP",
        "step": step,
        "action": action,
        "reward": round(reward, 4),
        "done": done,
        "error": str(error) if error is not None else None,
    }
    print(json.dumps(payload), flush=True)


def log_end(*, success: bool, steps: int, score: float, rewards: list) -> None:
    print(json.dumps({
        "event": "END",
        "success": success,
        "steps": steps,
        "score": round(score, 4),
        "rewards": [round(r, 4) for r in rewards],
    }), flush=True)


def debug(msg: str) -> None:
    if DEBUG:
        print(f"[DEBUG] {msg}", flush=True)


# ── Thin async OpenEnv client ─────────────────────────────────────────────────

class EnvClient:
    def __init__(self, base_url: str):
        self._base = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=60.0)
        return self

    async def __aexit__(self, *_):
        await self.close()

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def reset(self, task_id: str) -> Dict:
        r = await self._client.post(f"{self._base}/reset", json={"task_id": task_id})
        r.raise_for_status()
        return r.json()

    async def step(self, action: Dict) -> Dict:
        r = await self._client.post(f"{self._base}/step", json={"action": action})
        r.raise_for_status()
        return r.json()

    async def state(self) -> Dict:
        r = await self._client.get(f"{self._base}/state")
        r.raise_for_status()
        return r.json()

    async def grade(self) -> Dict:
        r = await self._client.post(f"{self._base}/grade")
        r.raise_for_status()
        return r.json()

    async def tasks(self) -> List[Dict]:
        r = await self._client.get(f"{self._base}/tasks")
        r.raise_for_status()
        return r.json()


# ── LLM agent ─────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert contract review agent. Your task is to:

1. REQUEST_NEXT clauses to explore the contract progressively
2. FLAG_RISK when you identify risky clauses (unlimited liability, auto-renewal, etc.)
3. DECIDE on each clause (accept/negotiate/reject) based on risk vs business value
4. FINALIZE when review is complete

Available risk types:
- unlimited_liability, auto_renewal, unilateral_termination, ip_transfer, exclusivity
- penalty_clause, unfavorable_jurisdiction, broad_indemnification
- overly_broad_confidentiality, restrictive_non_compete

Action format:
{
  "type": "request_next_clause" | "flag_risk" | "make_decision" | "finalize_review",
  "clause_id": "C1",
  "risk_label": "unlimited_liability",
  "decision": "accept" | "negotiate" | "reject",
  "justification": "reason for action"
}

Respond ONLY with valid JSON action."""


def build_obs_text(data: Dict) -> str:
    obs = data.get("observation", data)
    lines = [
        "Current State:",
        f"- Clauses revealed: {obs['clauses_revealed']}/{obs['total_clauses']}",
        f"- Current step: {obs['current_step']}/{obs['max_steps']}",
        f"- Exploration budget: {obs['exploration_budget']:.2f}",
        f"- Message: {obs.get('message', '')}",
        "", "Visible Clauses:",
    ]
    for clause in obs.get("visible_clauses", []):
        lines.append(f"\n[{clause['id']}] {clause['text']}")
    if obs.get("flagged_risks"):
        lines.append("\nFlagged Risks:")
        for flag in obs["flagged_risks"]:
            lines.append(f"- {flag['clause_id']}: {flag['risk_type']}")
    lines.append("\nWhat is your next action? (JSON only)")
    return "\n".join(lines)


def get_model_action(llm: OpenAI, history: List[Dict], data: Dict) -> Dict:
    history.append({"role": "user", "content": build_obs_text(data)})
    try:
        response = llm.chat.completions.create(
            model=MODEL_NAME, messages=history,
            temperature=TEMPERATURE, max_tokens=MAX_TOKENS,
        )
        text = response.choices[0].message.content
        action = json.loads(text)
        history.append({"role": "assistant", "content": text})
        return action
    except json.JSONDecodeError as e:
        debug(f"JSON parse error: {e}")
        return {"type": "request_next_clause"}
    except Exception as e:
        debug(f"LLM call failed: {e}")
        return {"type": "request_next_clause"}


# ── Per-task episode ───────────────────────────────────────────────────────────

async def run_task(env: EnvClient, llm: OpenAI, task_id: str) -> Dict:
    history: List[Dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_id, env="contract_review_v2", model=MODEL_NAME)

    try:
        data = await env.reset(task_id)
        done = False

        for step in range(1, MAX_STEPS + 1):
            if done:
                break

            action = get_model_action(llm, history, data)
            error = None

            try:
                data = await env.step(action)
                reward_obj = data.get("reward", {})
                reward = float(reward_obj.get("value", 0.0)) if isinstance(reward_obj, dict) else float(reward_obj)
                done = bool(data.get("done", False))
            except Exception as e:
                error = str(e)
                reward = 0.0
                done = True
                debug(f"Step {step} error: {e}")

            rewards.append(reward)
            steps_taken = step
            log_step(step=step, action=action, reward=reward, done=done, error=error)

        try:
            grade_data = await env.grade()
            score = float(grade_data.get("score", 0.0))
        except Exception as e:
            debug(f"Grade failed: {e}")
            score = sum(rewards) / MAX_STEPS if MAX_STEPS > 0 else 0.0

        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return {"task_id": task_id, "score": score, "steps": steps_taken}


# ── Main ───────────────────────────────────────────────────────────────────────

async def main():
    if not HF_TOKEN:
        print(json.dumps({"event": "WARN", "message": "HF_TOKEN not set — using ENV_URL directly without LLM auth"}), flush=True)

    debug(f"Model: {MODEL_NAME} | API: {API_BASE_URL} | Env: {ENV_URL}")

    llm = OpenAI(api_key=HF_TOKEN or "sk-placeholder", base_url=API_BASE_URL)

    async with EnvClient(ENV_URL) as env:
        task_list = await env.tasks()
        debug(f"Found {len(task_list)} tasks")

        results = []
        for task_info in task_list:
            try:
                result = await asyncio.wait_for(
                    run_task(env, llm, task_info["task_id"]),
                    timeout=TASK_TIMEOUT_SECONDS
                )
                results.append(result)
            except asyncio.TimeoutError:
                debug(f"Task {task_info['task_id']} timed out after {TASK_TIMEOUT_SECONDS}s")
                results.append({"task_id": task_info["task_id"], "score": 0.0, "steps": MAX_STEPS})

    avg_score = sum(r["score"] for r in results) / len(results) if results else 0.0
    with open("baseline_results.json", "w") as f:
        json.dump({"model": MODEL_NAME, "results": results, "average_score": avg_score}, f, indent=2)
    debug(f"Average score: {avg_score:.4f} — saved to baseline_results.json")


if __name__ == "__main__":
    asyncio.run(main())
