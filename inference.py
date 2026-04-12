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
import time
from typing import Dict, List, Optional
import httpx
from openai import OpenAI

# ── Required environment variables ────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN     = os.getenv("HF_TOKEN")

if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

# ── Runtime configuration ─────────────────────────────────────────────────────
ENV_URL                 = os.getenv("ENV_URL", "https://rohanrogers-contract-review-env.hf.space")
TEMPERATURE             = 0.7
MAX_TOKENS              = 2000
MAX_STEPS               = 20
SUCCESS_SCORE_THRESHOLD = 0.5
TASK_TIMEOUT_SECONDS    = 300   # 5 min per task; 3 tasks = 15 min max (under 20 min limit)
LLM_MAX_RETRIES         = 3     # Retry LLM calls with backoff (organizer Q17 advice)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ── Structured logging helpers ────────────────────────────────────────────────
# CRITICAL: The validator parses lines starting with literal [START], [STEP], [END].
# These MUST be plain text, NOT JSON. Rewards must be 2 decimal places.
# Booleans must be lowercase "true"/"false". No other stdout output allowed.

def clamp_reward(r: float) -> float:
    """Clamp reward to strict (0, 1) range — validator rejects 0.0 and 1.0."""
    return max(0.01, min(0.99, r))


def fmt_reward(r: float) -> str:
    """Format reward to exactly 2 decimal places."""
    return f"{r:.2f}"


def log_start(*, task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(*, step: int, action, reward: float, done: bool, error=None) -> None:
    # Compact JSON + strip newlines to guarantee single-line output
    if isinstance(action, dict):
        action_str = json.dumps(action, separators=(",", ":"))
    else:
        action_str = str(action).replace("\n", " ")
    done_str = "true" if done else "false"
    error_str = str(error).replace("\n", " ") if error is not None else "null"
    print(
        f"[STEP] step={step} action={action_str} "
        f"reward={fmt_reward(reward)} done={done_str} error={error_str}",
        flush=True,
    )


def log_end(*, task: str, score: float, steps: int,
            success: bool = False, rewards: list = None) -> None:
    """Emit [END] with all fields from both organizer format and sample script."""
    success_str = "true" if success else "false"
    rewards_str = ",".join(fmt_reward(r) for r in (rewards or []))
    print(
        f"[END] task={task} success={success_str} "
        f"steps={steps} score={fmt_reward(score)} "
        f"rewards={rewards_str}",
        flush=True,
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

SYSTEM_PROMPT = """You review contracts. Output ONLY a single JSON object. No explanation.

Actions:
{"type": "request_next_clause"}
{"type": "flag_risk", "clause_id": "C1", "risk_label": "unlimited_liability"}
{"type": "make_decision", "clause_id": "C1", "decision": "negotiate", "justification": "high value"}
{"type": "finalize_review"}

Risk labels: unlimited_liability, auto_renewal, unilateral_termination, ip_transfer, exclusivity, penalty_clause, unfavorable_jurisdiction, broad_indemnification, overly_broad_confidentiality, restrictive_non_compete

Decisions: accept (safe clauses), negotiate (risky + high business value), reject (risky + low value)

Strategy: Do NOT reject high-value clauses. Negotiate them instead. Finalize after reviewing all clauses."""


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


def fallback_action(data: Dict, step: int, decided_ids: set) -> Dict:
    """Rule-based fallback agent — ensures valid logs even if LLM is unavailable.
    
    Uses persistent decided_ids to track which clauses have already been decided on,
    preventing infinite loops of re-deciding the same clause.
    """
    obs = data.get("observation", data)
    clauses_revealed = obs.get("clauses_revealed", 0)
    total_clauses = obs.get("total_clauses", 0)
    visible_clauses = obs.get("visible_clauses", [])
    flagged_risks = obs.get("flagged_risks", [])
    flagged_ids = {f["clause_id"] for f in flagged_risks}
    max_steps = obs.get("max_steps", MAX_STEPS)

    # Force finalize if running low on steps
    if step >= max_steps - 1:
        return {"type": "finalize_review", "justification": "Finalizing before step limit"}

    # Strategy: explore first, then flag risky-looking clauses, then decide, then finalize
    if clauses_revealed < total_clauses and step <= total_clauses + 1:
        return {"type": "request_next_clause"}

    # Flag unflagged clauses that contain risk keywords
    risk_keywords = {
        "unlimited_liability": ["unlimited", "without limitation", "any and all damages", "any and all losses"],
        "auto_renewal": ["automatically renew", "successive terms", "auto-renew", "automatic renewal"],
        "unilateral_termination": ["terminate immediately", "sole discretion", "for convenience"],
        "ip_transfer": ["intellectual property", "work made for hire", "assigns all right", "irrevocably assigns"],
        "broad_indemnification": ["indemnify", "hold harmless", "defend and indemnify"],
        "penalty_clause": ["liquidated damages", "penalty", "withhold payment"],
        "exclusivity": ["exclusive", "shall not provide similar", "preferred-vendor"],
        "restrictive_non_compete": ["non-compete", "shall not compete", "not engage", "not directly compete"],
        "unfavorable_jurisdiction": ["cayman", "singapore", "offshore", "grand cayman"],
        "overly_broad_confidentiality": ["any information", "whatsoever", "any purpose", "defined broadly"],
    }
    for clause in visible_clauses:
        cid = clause.get("id", "")
        if cid in flagged_ids:
            continue
        text_lower = clause.get("text", "").lower()
        for risk_label, keywords in risk_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return {"type": "flag_risk", "clause_id": cid, "risk_label": risk_label,
                        "justification": f"Identified {risk_label} risk pattern"}

    # Make decisions on visible clauses — use negotiate for high-value risky clauses
    for clause in visible_clauses:
        cid = clause.get("id", "")
        if cid in decided_ids:
            continue
        decided_ids.add(cid)
        text_lower = clause.get("text", "").lower()
        is_flagged = cid in flagged_ids
        # Detect high-value signals in clause text
        high_value_signals = ["revenue", "$", "million", "exclusive", "partnership",
                              "preferred-vendor", "guaranteed", "commitment", "pipeline"]
        has_high_value = any(sig in text_lower for sig in high_value_signals)
        
        if is_flagged and has_high_value:
            # Risky BUT high value — negotiate, don't reject
            return {"type": "make_decision", "clause_id": cid, "decision": "negotiate",
                    "justification": "Risky clause with high business value — negotiating terms"}
        elif is_flagged:
            # Risky and low value — reject
            return {"type": "make_decision", "clause_id": cid, "decision": "reject",
                    "justification": "High risk with low business value"}
        else:
            # Safe clause — accept
            return {"type": "make_decision", "clause_id": cid, "decision": "accept",
                    "justification": "Clause has no identified risks"}

    return {"type": "finalize_review", "justification": "All clauses reviewed and decided"}


def extract_json(text: str) -> str:
    """Extract JSON from LLM output — handles fences, surrounding text, and messy formatting.
    
    Critical: The validator uses Llama-3.1-8B (not GPT-4), which often wraps JSON in
    explanatory text like 'Here is my action:\n{...}\nThis will...'
    """
    text = text.strip()
    
    # Step 1: Strip markdown fences (```json ... ```)
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1:]
        if text.endswith("```"):
            text = text[:-3].rstrip()
        # Try parsing the fenced content directly
        try:
            json.loads(text.strip())
            return text.strip()
        except (json.JSONDecodeError, ValueError):
            pass
    
    # Step 2: Try parsing the whole text as JSON
    try:
        json.loads(text)
        return text
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Step 3: Extract first JSON object using brace matching
    start = text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        json.loads(candidate)
                        return candidate
                    except (json.JSONDecodeError, ValueError):
                        break
    
    # Step 4: Last resort — return original text (will trigger fallback)
    return text


def get_model_action(llm: OpenAI, history: List[Dict], data: Dict, step: int = 1,
                     decided_ids: set = None) -> Dict:
    """Get action from LLM with retry. Separates proxy call failures from JSON parse failures.
    
    Critical: The validator checks that at least one LLM proxy call was made.
    A successful call that returns bad JSON STILL counts as a proxy call.
    Only genuine connection/auth failures should fall through to the fallback.
    """
    if decided_ids is None:
        decided_ids = set()
    history.append({"role": "user", "content": build_obs_text(data)})

    # ── Step 1: Call LLM with retry ──────────────────────────────────────────
    text = None
    for attempt in range(LLM_MAX_RETRIES):
        try:
            response = llm.chat.completions.create(
                model=MODEL_NAME, messages=history,
                temperature=TEMPERATURE, max_tokens=MAX_TOKENS,
            )
            text = response.choices[0].message.content
            break  # Success — proxy call went through
        except Exception as e:
            if attempt < LLM_MAX_RETRIES - 1:
                wait = 2 ** (attempt + 1)  # 2s, 4s
                debug(f"LLM retry {attempt+1}/{LLM_MAX_RETRIES} after {wait}s: {e}")
                time.sleep(wait)
            else:
                debug(f"LLM call failed after {LLM_MAX_RETRIES} retries: {e} — using fallback")
                return fallback_action(data, step, decided_ids)

    # ── Step 2: Parse JSON (proxy call already succeeded at this point) ──────
    try:
        clean_text = extract_json(text)
        action = json.loads(clean_text)
        history.append({"role": "assistant", "content": text})
        return action
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        debug(f"JSON parse failed (proxy call DID succeed): {e}")
        return fallback_action(data, step, decided_ids)


# ── Per-task episode ───────────────────────────────────────────────────────────

async def run_task(env: EnvClient, llm: OpenAI, task_id: str) -> Dict:
    history: List[Dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False
    decided_ids: set = set()  # Persistent across all steps — prevents re-deciding

    log_start(task=task_id, env="contract_review_v2", model=MODEL_NAME)

    try:
        data = await env.reset(task_id)
        done = False

        for step in range(1, MAX_STEPS + 1):
            if done:
                break

            # Force finalize if we're about to hit step limit
            if step >= MAX_STEPS - 1:
                action = {"type": "finalize_review", "justification": "Finalizing before step limit"}
            else:
                action = get_model_action(llm, history, data, step, decided_ids)
            error = None

            try:
                data = await env.step(action)
                reward_obj = data.get("reward", {})
                raw_reward = float(reward_obj.get("value", 0.0)) if isinstance(reward_obj, dict) else float(reward_obj)
                done = bool(data.get("done", False))
            except Exception as e:
                error = str(e)
                raw_reward = 0.0
                done = True
                debug(f"Step {step} error: {e}")

            # Clamp reward to strict (0, 1) — validator rejects 0.0 and 1.0
            reward = clamp_reward(raw_reward)
            rewards.append(reward)
            steps_taken = step
            log_step(step=step, action=action, reward=reward, done=done, error=error)

        try:
            grade_data = await env.grade()
            score = float(grade_data.get("score", 0.0))
        except Exception as e:
            debug(f"Grade failed: {e}")
            score = sum(rewards) / len(rewards) if rewards else 0.01

        score = min(max(score, 0.01), 0.99)
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        log_end(task=task_id, score=score, steps=steps_taken,
                success=success, rewards=rewards)

    return {"task_id": task_id, "score": score, "steps": steps_taken}


# ── Main ───────────────────────────────────────────────────────────────────────

async def main():
    debug(f"Model: {MODEL_NAME} | API: {API_BASE_URL} | Env: {ENV_URL}")

    llm = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)

    # Fallback task IDs in case /tasks endpoint is unavailable
    FALLBACK_TASKS = ["easy_detection", "medium_analysis", "hard_comprehensive"]

    async with EnvClient(ENV_URL) as env:
        try:
            task_list = await env.tasks()
            task_ids = [t if isinstance(t, str) else t["task_id"] for t in task_list]
        except Exception as e:
            debug(f"Could not fetch task list: {e} — using fallback task IDs")
            task_ids = FALLBACK_TASKS
        debug(f"Running {len(task_ids)} tasks")

        results = []
        for task_id in task_ids:
            try:
                result = await asyncio.wait_for(
                    run_task(env, llm, task_id),
                    timeout=TASK_TIMEOUT_SECONDS
                )
                results.append(result)
            except asyncio.TimeoutError:
                debug(f"Task {task_id} timed out after {TASK_TIMEOUT_SECONDS}s")
                # CRITICAL: Always emit [END] even on timeout
                log_end(task=task_id, score=0.01, steps=MAX_STEPS,
                        success=False, rewards=[])
                results.append({"task_id": task_id, "score": 0.01, "steps": MAX_STEPS})

    avg_score = sum(r["score"] for r in results) / len(results) if results else 0.0
    debug(f"Average score: {avg_score:.4f}")


if __name__ == "__main__":
    asyncio.run(main())
