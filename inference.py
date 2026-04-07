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
MODEL_NAME   = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN     = os.getenv("HF_TOKEN")

if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

# ── Runtime configuration ─────────────────────────────────────────────────────
ENV_URL                 = os.getenv("ENV_URL", "http://localhost:7860")
TEMPERATURE             = 0.7
MAX_TOKENS              = 2000
MAX_STEPS               = 20
SUCCESS_SCORE_THRESHOLD = 0.5
TASK_TIMEOUT_SECONDS    = 300   # 5 min per task; 3 tasks = 15 min max (under 20 min limit)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ── Structured logging helpers ────────────────────────────────────────────────
# CRITICAL: The validator parses lines starting with literal [START], [STEP], [END].
# These MUST be plain text, NOT JSON. Rewards must be 2 decimal places.
# Booleans must be lowercase "true"/"false". No other stdout output allowed.

def fmt_reward(r: float) -> str:
    """Format reward to exactly 2 decimal places."""
    return f"{r:.2f}"


def log_start(*, task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(*, step: int, action, reward: float, done: bool, error=None) -> None:
    action_str = json.dumps(action) if isinstance(action, dict) else str(action)
    done_str = "true" if done else "false"
    error_str = str(error) if error is not None else "null"
    print(
        f"[STEP] step={step} action={action_str} "
        f"reward={fmt_reward(reward)} done={done_str} error={error_str}",
        flush=True
    )


def log_end(*, success: bool, steps: int, rewards: list) -> None:
    success_str = "true" if success else "false"
    rewards_str = ",".join(fmt_reward(r) for r in rewards)
    print(
        f"[END] success={success_str} steps={steps} rewards={rewards_str}",
        flush=True
    )


def debug(msg: str) -> None:
    """Debug output goes to stderr only — never pollute stdout."""
    print(f"[DEBUG] {msg}", file=sys.stderr, flush=True)


# ── Thin async OpenEnv client ─────────────────────────────────────────────────

class EnvClient:
    def __init__(self, base_url: str):
        self._base = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=30.0)
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


def fallback_action(data: Dict, step: int) -> Dict:
    """Rule-based fallback agent — ensures valid logs even if LLM is unavailable."""
    obs = data.get("observation", data)
    clauses_revealed = obs.get("clauses_revealed", 0)
    total_clauses = obs.get("total_clauses", 0)
    visible_clauses = obs.get("visible_clauses", [])
    flagged_risks = obs.get("flagged_risks", [])
    flagged_ids = {f["clause_id"] for f in flagged_risks}

    # Strategy: explore first, then flag risky-looking clauses, then finalize
    if clauses_revealed < total_clauses and step <= total_clauses + 1:
        return {"type": "request_next_clause"}

    # Flag unflagged clauses that contain risk keywords
    risk_keywords = {
        "unlimited_liability": ["unlimited", "without limitation", "any and all damages"],
        "auto_renewal": ["automatically renew", "successive terms", "auto-renew"],
        "unilateral_termination": ["terminate immediately", "sole discretion", "for convenience"],
        "ip_transfer": ["intellectual property", "work made for hire", "assigns all right"],
        "broad_indemnification": ["indemnify", "hold harmless", "defend and indemnify"],
        "penalty_clause": ["liquidated damages", "penalty", "withhold payment"],
        "exclusivity": ["exclusive", "shall not provide similar"],
        "restrictive_non_compete": ["non-compete", "shall not compete", "not engage"],
        "unfavorable_jurisdiction": ["cayman", "singapore", "offshore"],
        "overly_broad_confidentiality": ["any information", "whatsoever", "any purpose"],
    }
    for clause in visible_clauses:
        cid = clause.get("id", "")
        if cid in flagged_ids:
            continue
        text_lower = clause.get("text", "").lower()
        for risk_label, keywords in risk_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return {"type": "flag_risk", "clause_id": cid, "risk_label": risk_label,
                        "justification": f"Keyword match for {risk_label}"}

    # Make decisions on visible clauses
    decided_ids = set()
    for clause in visible_clauses:
        cid = clause.get("id", "")
        if cid not in decided_ids:
            if cid in flagged_ids:
                return {"type": "make_decision", "clause_id": cid, "decision": "reject",
                        "justification": "Rejecting flagged risky clause"}
            else:
                return {"type": "make_decision", "clause_id": cid, "decision": "accept",
                        "justification": "Accepting clause with no identified risks"}

    return {"type": "finalize_review", "justification": "Review complete"}


def get_model_action(llm: OpenAI, history: List[Dict], data: Dict, step: int = 1) -> Dict:
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
        debug(f"JSON parse error: {e} — using fallback agent")
        return fallback_action(data, step)
    except Exception as e:
        debug(f"LLM call failed: {e} — using fallback agent")
        return fallback_action(data, step)


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

            action = get_model_action(llm, history, data, step)
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
            score = sum(rewards) / len(rewards) if rewards else 0.0

        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        log_end(success=success, steps=steps_taken, rewards=rewards)

    return {"task_id": task_id, "score": score, "steps": steps_taken}


# ── Main ───────────────────────────────────────────────────────────────────────

async def main():
    debug(f"Model: {MODEL_NAME} | API: {API_BASE_URL} | Env: {ENV_URL}")

    llm = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)

    async with EnvClient(ENV_URL) as env:
        task_list = await env.tasks()
        debug(f"Found {len(task_list)} tasks")

        results = []
        for task_info in task_list:
            task_id = task_info if isinstance(task_info, str) else task_info["task_id"]
            try:
                result = await asyncio.wait_for(
                    run_task(env, llm, task_id),
                    timeout=TASK_TIMEOUT_SECONDS
                )
                results.append(result)
            except asyncio.TimeoutError:
                debug(f"Task {task_id} timed out after {TASK_TIMEOUT_SECONDS}s")
                results.append({"task_id": task_id, "score": 0.0, "steps": MAX_STEPS})

    avg_score = sum(r["score"] for r in results) / len(results) if results else 0.0
    debug(f"Average score: {avg_score:.4f}")


if __name__ == "__main__":
    asyncio.run(main())
