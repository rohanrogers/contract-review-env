---
title: Contract Review Environment
emoji: ⚖️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
base_path: /docs
license: mit
pinned: false
tags:
  - openenv
  - legal
  - contract-review
  - reinforcement-learning
  - decision-making
---

# Contract Review Environment v2.0 🔍⚖️

**Interactive legal contract review environment for AI agent training and evaluation.**  
Designed specifically for evaluating LLM agents in structured decision-making tasks.

---

## 🎯 Motivation

Real-world contract review is a **strategic, multi-step reasoning task** — not a simple classification problem. Legal professionals:

1. **Explore progressively** — read clauses sequentially, not all at once
2. **Flag risks accurately** — identify problematic terms (unlimited liability, auto-renewal, etc.)
3. **Make strategic decisions** — balance risk vs. business value (accept / negotiate / reject)
4. **Work under constraints** — time, budget, and cognitive load limitations

This environment transforms contract review from a static classification wrapper into an **interactive decision-making system** that challenges AI agents to reason strategically across multiple steps.

---

## 🚀 Key Features

### 1. Progressive Clause Revelation
Agents don't see the entire contract upfront. They must:
- Request clauses one at a time (`request_next_clause`)
- Decide when they've seen enough
- Balance exploration vs. exploitation

### 2. Multi-Action Decision System
Four action types:
- `request_next_clause` — Reveal next clause
- `flag_risk` — Identify a risky clause with a specific risk label
- `make_decision` — Accept / negotiate / reject a clause
- `finalize_review` — Complete review and receive final score

### 3. Cost / Penalty Mechanics
Every step costs exploration budget:
- Correct risk flags → **+0.4 reward**
- False positives → **−0.3 penalty**
- Strategic decisions → **+0.3 bonus**
- Each step → **−0.05 cost**

### 4. Three Difficulty Levels
- **Easy**: Obvious keywords (e.g., "unlimited liability")
- **Medium**: Indirect wording (e.g., "shall continue in successive terms…")
- **Hard**: Conflicting clauses, compound risks, legal jargon

### 5. Strategic Tradeoffs
Agents must balance risk severity vs. business value, precision vs. recall, and exploration efficiency.

---

## 📋 Environment Specification

### Observation Space

```json
{
  "visible_clauses": [
    {
      "id": "C1",
      "text": "The Contractor shall be liable...",
      "business_value": 0.5
    }
  ],
  "flagged_risks": [
    {"clause_id": "C1", "risk_type": "unlimited_liability"}
  ],
  "total_clauses": 8,
  "clauses_revealed": 3,
  "current_step": 5,
  "max_steps": 20,
  "exploration_budget": 0.65,
  "message": "Revealed clause C3"
}
```

### Action Space

```json
{
  "type": "request_next_clause | flag_risk | make_decision | finalize_review",
  "clause_id": "C1",
  "risk_label": "unlimited_liability",
  "decision": "accept | negotiate | reject",
  "justification": "High severity risk with low business value"
}
```

### Risk Labels

`unlimited_liability` · `auto_renewal` · `unilateral_termination` · `ip_transfer` · `exclusivity` · `penalty_clause` · `unfavorable_jurisdiction` · `broad_indemnification` · `overly_broad_confidentiality` · `restrictive_non_compete`

### Reward Structure

| Component | Value |
|---|---|
| Correct flag | +0.4 |
| False positive | −0.3 |
| False negative penalty | −0.5 |
| Good decision | +0.3 |
| Exploration | +0.1 |
| Step cost | −0.05 |

---

## 🎓 Tasks

### Task 1: Easy Detection (`easy_detection`)
- **Difficulty**: Easy
- **Contract**: Simple SaaS agreement
- **Objective**: Identify obvious risk clauses
- **Target Score**: 0.7
- **Grader**: Risk detection accuracy (F1 score)

### Task 2: Medium Analysis (`medium_analysis`)
- **Difficulty**: Medium
- **Contract**: Vendor agreement with indirect wording
- **Objective**: Flag hidden risks AND make strategic decisions
- **Target Score**: 0.65
- **Grader**: Decision quality (weighted by risk / value tradeoffs)

### Task 3: Hard Comprehensive (`hard_comprehensive`)
- **Difficulty**: Hard
- **Contract**: Complex partnership agreement
- **Objective**: Comprehensive review with efficiency constraints
- **Target Score**: 0.6
- **Grader**: Combined metric (40% detection + 40% decisions + 20% efficiency)

---

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.11+
- Docker (for containerized deployment)

### Environment Variables

```bash
export API_BASE_URL="https://api.openai.com/v1"   # LLM API endpoint
export MODEL_NAME="gpt-4o-mini"                    # Model identifier
export HF_TOKEN="your-huggingface-token"           # HF / API key
export ENV_URL="http://localhost:7860"             # Environment URL
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python -m uvicorn server.app:app --host 0.0.0.0 --port 7860

# Health check
curl http://localhost:7860/
```

### Docker Deployment

```bash
# Build image
docker build -t contract-review-env .

# Run container
docker run -p 7860:7860 \
  -e API_BASE_URL="https://api.openai.com/v1" \
  -e MODEL_NAME="gpt-4o-mini" \
  -e HF_TOKEN="your-token" \
  contract-review-env

# Health check
curl http://localhost:7860/
```

---

## 🏃 Running Inference

```bash
# Run baseline agent on all tasks
python inference.py
```

### Expected Output (structured JSON logs)

```json
{"event": "START", "task": "easy_detection", "env": "contract_review_v2", "model": "gpt-4o-mini"}
{"event": "STEP", "step": 1, "action": {"type": "request_next_clause"}, "reward": 0.05, "done": false, "error": null}
{"event": "STEP", "step": 2, "action": {"type": "flag_risk", "clause_id": "C2", "risk_label": "unlimited_liability"}, "reward": 0.35, "done": false, "error": null}
{"event": "STEP", "step": 3, "action": {"type": "make_decision", "clause_id": "C2", "decision": "reject"}, "reward": 0.3, "done": false, "error": null}
{"event": "STEP", "step": 4, "action": {"type": "finalize_review"}, "reward": 0.0, "done": true, "error": null}
{"event": "END", "success": true, "steps": 4, "score": 0.75, "rewards": [0.05, 0.35, 0.3, 0.0]}
```

### Baseline Results

| Task | Difficulty | Baseline Score |
|---|---|---|
| easy_detection | Easy | ~0.75 |
| medium_analysis | Medium | ~0.68 |
| hard_comprehensive | Hard | ~0.62 |

---

## 📊 Grading Logic

### Risk Detection Grader (Easy)

```python
F1 = 2 * precision * recall / (precision + recall)
exploration_penalty = max(0, 0.7 - exploration_ratio) * 0.3
score = F1 - exploration_penalty
```

### Decision Quality Grader (Medium)

```python
if accept and no_risks:        score = 1.0
if accept and has_risks:       score = 1.0 - severity
if negotiate and high_value:   score = 1.0
if reject and high_severity:   score = 1.0

final = avg_decision_score * 0.7 + decision_coverage * 0.3
```

### Comprehensive Grader (Hard)

```python
final_score = (
    risk_detection_score * 0.4 +
    decision_quality_score * 0.4 +
    efficiency_score * 0.2
)
```

---

## 🧪 API Endpoints

### `GET /`
Health check — returns `200 OK`

### `GET /tasks`
List all available tasks

### `POST /reset`
```json
{ "task_id": "easy_detection", "contract_id": "EASY_001" }
```

### `POST /step`
```json
{
  "action": {
    "type": "flag_risk",
    "clause_id": "C2",
    "risk_label": "unlimited_liability"
  }
}
```

### `GET /state`
Get current environment state

### `POST /grade`
Grade the current episode — returns `{ "score": 0.75 }`

---

## 🔍 Example Episode

```python
# 1. Reset environment for a task
obs = await env.reset("easy_detection")
# → visible_clauses: [C1], exploration_budget: 1.0

# 2. Request next clause
obs, reward, done, _ = await env.step({"type": "request_next_clause"})
# → reward: +0.05 (exploration), visible_clauses: [C1, C2]

# 3. Flag risk in C2
obs, reward, done, _ = await env.step({
    "type": "flag_risk",
    "clause_id": "C2",
    "risk_label": "unlimited_liability"
})
# → reward: +0.4 (correct) − 0.05 (step cost) = +0.35

# 4. Reject C2
obs, reward, done, _ = await env.step({
    "type": "make_decision",
    "clause_id": "C2",
    "decision": "reject"
})
# → reward: +0.3 (good decision on high-risk clause)

# 5. Finalize
obs, reward, done, _ = await env.step({"type": "finalize_review"})
# → done: True, final grade calculated via POST /grade
```

---

## 🎯 Evaluation Alignment

| Criterion | How This Environment Addresses It |
|---|---|
| **Real-world utility (30%)** | Models actual legal review workflow; immediately useful for legal AI evaluation |
| **Task & grader quality (25%)** | 3 tasks with clear difficulty progression; deterministic graders; multi-dimensional scoring |
| **Environment design (20%)** | True state transitions; multi-action system; cost/penalty mechanics; clear episode boundaries |
| **Code quality & compliance (15%)** | Full OpenEnv spec; typed Pydantic models; clean FastAPI structure; working Dockerfile |
| **Creativity & novelty (10%)** | First interactive contract review environment; decision layer adds strategic depth |

---

## 📁 Project Structure

```
contract-review-env/
├── server/
│   ├── app.py              # FastAPI server (reset / step / state / grade)
│   └── environment.py      # Core environment logic
├── contracts/
│   └── datasets.py         # Contract data (easy / medium / hard)
├── tasks/
│   └── graders.py          # Task definitions + grading logic
├── inference.py            # Baseline agent script (root directory)
├── openenv.yaml            # OpenEnv specification
├── Dockerfile              # Container configuration
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 📧 Contact

**Author**: Rohan Mathew Rogers  
**Email**: rohanrogers10@gmail.com  
**Hackathon**: Meta OpenEnv Round 1 — Scaler School of Technology × Hugging Face × PyTorch

---

## 📜 License

MIT License — Built for Meta OpenEnv Hackathon 2026
