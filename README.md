---
title: Contract Review Environment
emoji: ⚖️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
tags:
  - openenv
  - legal
  - contract-review
  - reinforcement-learning
---

An OpenEnv environment for interactive legal contract review. Each episode presents a contract with progressively revealed clauses. The agent explores clauses, flags risks, and makes strategic decisions (accept, negotiate, reject) under step and budget constraints. The hard task presents 14 enterprise-grade clauses requiring 22-28 steps for optimal performance. The agent must balance exploration cost against decision quality, and negotiate risky clauses that carry high business value rather than rejecting them.

## Quick Start

```python
from contract_review import ContractReviewEnv

# Connect to the running Space
env = ContractReviewEnv(base_url="https://rohanrogers-contract-review-env.hf.space")

result = env.reset(task_id="easy_detection")
print(result.observation)  # First clause visible

# Explore
result = env.step({"type": "request_next_clause"})
# Reveals next clause, costs exploration budget

# Flag a risk
result = env.step({
    "type": "flag_risk",
    "clause_id": "C2",
    "risk_label": "unlimited_liability"
})

# Make a strategic decision
result = env.step({
    "type": "make_decision",
    "clause_id": "C2",
    "decision": "reject"
})

# Finalize
result = env.step({"type": "finalize_review"})
print(f"Done: {result.done}, Reward: {result.reward}")

env.close()
```

## Building and Running Locally

### Docker (Recommended)

```bash
docker build -t contract-review-env .
docker run -p 7860:7860 contract-review-env

curl http://localhost:7860/health
# {"status": "healthy", "environment": "contract_review_v2", "tasks_available": 3}
```

### Without Docker

```bash
git clone https://huggingface.co/spaces/rohanrogers/contract-review-env
cd contract-review-env
pip install -e .
uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload

curl http://localhost:7860/health
```

## Environment Design

### Episode Structure

Each episode is a multi-step contract review:

1. `reset(task_id)` loads a contract with the first clause visible
2. `step(action)` processes one of four action types
3. The agent explores, flags, decides, and finalizes within a step budget
4. `grade()` returns a normalized score in (0, 1)

### Action

`ContractAction`: The agent's review action.

| Field | Type | Description |
|-------|------|-------------|
| `type` | `str` | One of: `request_next_clause`, `flag_risk`, `make_decision`, `finalize_review` |
| `clause_id` | `str` (optional) | Target clause (required for `flag_risk` and `make_decision`) |
| `risk_label` | `str` (optional) | Risk type (required for `flag_risk`) |
| `decision` | `str` (optional) | One of: `accept`, `negotiate`, `reject` (required for `make_decision`) |

### Observation

`ContractObservation`: The current state of the review.

| Field | Type | Description |
|-------|------|-------------|
| `visible_clauses` | `list` | Clauses revealed so far (id, text, business_value) |
| `flagged_risks` | `list` | Risks flagged by the agent |
| `total_clauses` | `int` | Total clauses in the contract |
| `clauses_revealed` | `int` | Number revealed so far |
| `current_step` | `int` | Current step in the episode |
| `max_steps` | `int` | Step budget (default: 25) |
| `exploration_budget` | `float` | Remaining budget, decreases each step |
| `message` | `str` | Feedback from the last action |

### Risk Labels

The environment supports 10 risk types:

`unlimited_liability`, `auto_renewal`, `unilateral_termination`, `ip_transfer`, `exclusivity`, `penalty_clause`, `unfavorable_jurisdiction`, `broad_indemnification`, `overly_broad_confidentiality`, `restrictive_non_compete`

### Reward

Step rewards are computed from action quality:

- Correct risk flag: +0.4
- False positive: -0.3 (clamped to 0.01 minimum at output)
- Strategic decision on high-risk clause: +0.3
- Exploration: +0.1
- Step cost: -0.05 per step

All rewards are clamped to the (0.01, 0.99) range before output.

## Tasks

### Task 1: Easy Detection (`easy_detection`)

Simple SaaS agreement with obvious risk keywords (e.g., "unlimited liability"). The grader measures risk detection F1 score.

```python
result = env.reset(task_id="easy_detection")
```

### Task 2: Medium Analysis (`medium_analysis`)

Vendor agreement with indirect wording (e.g., "shall continue in successive terms"). The grader evaluates decision quality weighted by risk-value tradeoffs.

```python
result = env.reset(task_id="medium_analysis")
```

### Task 3: Hard Comprehensive (`hard_comprehensive`)

14-clause enterprise partnership agreement where multiple high-risk clauses also carry high business value. The agent cannot fully explore, flag, and decide everything within the budget. It must prioritize. The grader combines four axes:

- Risk detection (20%) - F1 score on flagged risks
- Decision quality (30%) - appropriateness of accept/negotiate/reject
- Business awareness (30%) - penalty for destroying high-value clauses
- Efficiency (20%) - exploration and step budget usage

```python
result = env.reset(task_id="hard_comprehensive")
# 14 clauses, budget allows ~25 steps
# Typical optimal trajectory: 22-28 steps
```

Naive strategies perform poorly:

| Strategy | Score | Why |
|----------|-------|-----|
| Reject all risky clauses | 0.39 | Destroys high-value partnerships |
| Accept everything | 0.33 | Ignores critical liability exposure |
| Strategic trade-offs | 0.72 | Negotiates high-value risks, rejects low-value ones |

Sample trajectory (optimal agent on hard task):

```
Steps 1-13:  Explore all 14 clauses (progressive revelation)
Step  14:    Flag H1_C3 = broad_indemnification (severity 0.9, value 0.8)
Step  15:    Flag H1_C6 = penalty_clause (severity 0.95, value 0.2)
Step  16:    Flag H1_C5 = ip_transfer (severity 0.8, value 0.7)
Step  17:    Make decision: H1_C3 -> negotiate (risky but high value)
Step  18:    Make decision: H1_C6 -> reject (risky and low value)
Step  19:    Make decision: H1_C5 -> negotiate (risky but high value)
Step  20:    Make decision: H1_C1 -> accept (safe clause)
Steps 21-22: Decide remaining clauses
Step  23:    Finalize review -> score: 0.72
```

## Running Inference

The `inference.py` script runs a baseline LLM agent across all tasks:

```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
export HF_TOKEN="your-token"
export ENV_URL="https://rohanrogers-contract-review-env.hf.space"

python inference.py
```

Output follows structured logging format:

```
[START] task=easy_detection env=contract_review_v2 model=meta-llama/Llama-3.1-8B-Instruct
[STEP] step=1 action={"type": "request_next_clause"} reward=0.05 done=false error=null
[STEP] step=2 action={"type": "flag_risk", "clause_id": "C2", "risk_label": "unlimited_liability"} reward=0.35 done=false error=null
[STEP] step=3 action={"type": "make_decision", "clause_id": "C2", "decision": "reject"} reward=0.30 done=false error=null
[STEP] step=4 action={"type": "finalize_review"} reward=0.01 done=true error=null
[END] task=easy_detection score=0.75 steps=4
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/tasks` | GET | List available tasks |
| `/reset` | POST | Start a new episode (`{"task_id": "easy_detection"}`) |
| `/step` | POST | Execute an action |
| `/state` | GET | Get current environment state |
| `/grade` | POST | Grade the current episode |

## Project Structure

```
contract-review-env/
├── .dockerignore         # Docker build exclusions
├── __init__.py           # Module exports
├── client.py             # ContractReviewEnv client
├── models.py             # Action and Observation models
├── inference.py          # Baseline LLM agent
├── openenv.yaml          # OpenEnv manifest
├── pyproject.toml        # Project metadata and dependencies
├── requirements.txt      # Server dependencies
├── Dockerfile            # Container image definition
├── README.md             # This file
├── server/
│   ├── app.py            # FastAPI application
│   └── environment.py    # Core environment logic
├── contracts/
│   └── datasets.py       # Contract data (easy / medium / hard)
└── tasks/
    └── graders.py        # Task definitions and grading logic
```

## Design Philosophy

Contract review suits reinforcement learning because it combines three properties rarely found together:

1. Progressive information revelation - clauses are hidden until explored, so the agent operates under genuine uncertainty. The agent must decide when to stop exploring and when to commit to decisions.

2. Irreversible decisions under uncertainty - once the agent flags a risk or makes a decision on a clause, it cannot undo it. This creates a planning horizon that extends across the entire episode, penalizing greedy strategies.

3. Multi-objective trade-offs - real contracts contain clauses that are simultaneously risky and valuable. A competent reviewer does not reject all risk. They negotiate where the business value justifies it. The 4-axis grading system (risk detection, decision quality, business awareness, efficiency) ensures no single-axis strategy dominates.

The hard task (14 clauses, 25-step budget) is designed so that a random agent scores around 0.33, a risk-averse agent scores around 0.45, and optimal strategic reasoning yields around 0.72. This score distribution provides a clear gradient signal for RL training.

## Use Cases

- LLM Evaluation: Benchmark strategic reasoning on high-stakes trade-offs
- Agent Training: Train RL agents with multi-axis reward signals
- Legal AI Research: Test whether models can balance risk vs. business value
- Curriculum Learning: Three difficulty levels for progressive training

## Learn More

- [OpenEnv Documentation](https://github.com/meta-pytorch/OpenEnv)
- [OpenEnv Tutorials](https://github.com/meta-pytorch/OpenEnv/tree/main/tutorial)
- [Hugging Face Space](https://huggingface.co/spaces/rohanrogers/contract-review-env)
