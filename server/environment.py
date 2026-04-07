"""
Interactive Contract Review Environment - UPGRADED VERSION
Transforms static classification into dynamic legal reasoning system
"""

from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from pydantic import BaseModel, Field
import random


class RiskType(str, Enum):
    UNLIMITED_LIABILITY = "unlimited_liability"
    AUTO_RENEWAL = "auto_renewal"
    UNILATERAL_TERMINATION = "unilateral_termination"
    IP_TRANSFER = "ip_transfer"
    EXCLUSIVITY = "exclusivity"
    PENALTY_CLAUSE = "penalty_clause"
    JURISDICTION = "unfavorable_jurisdiction"
    INDEMNIFICATION = "broad_indemnification"
    CONFIDENTIALITY = "overly_broad_confidentiality"
    NON_COMPETE = "restrictive_non_compete"


class ActionType(str, Enum):
    REQUEST_NEXT = "request_next_clause"
    FLAG_RISK = "flag_risk"
    DECIDE = "make_decision"
    FINALIZE = "finalize_review"


class Decision(str, Enum):
    ACCEPT = "accept"
    NEGOTIATE = "negotiate"
    REJECT = "reject"


class ContractClause(BaseModel):
    id: str
    text: str
    risks: List[RiskType] = Field(default_factory=list)
    severity: float = Field(ge=0.0, le=1.0)  # 0.0 = safe, 1.0 = critical
    business_value: float = Field(ge=0.0, le=1.0)  # relevance to deal


class Action(BaseModel):
    type: ActionType
    clause_id: Optional[str] = None
    risk_label: Optional[RiskType] = None
    decision: Optional[Decision] = None
    justification: Optional[str] = None


class Observation(BaseModel):
    visible_clauses: List[ContractClause]
    flagged_risks: List[Dict[str, str]]  # clause_id -> risk_type mappings
    total_clauses: int
    clauses_revealed: int
    current_step: int
    max_steps: int
    exploration_budget: float  # decreases with each step
    message: str = ""


class Reward(BaseModel):
    value: float
    breakdown: Dict[str, float] = Field(default_factory=dict)


class ContractReviewEnvironment:
    """
    Interactive contract review environment with:
    - Progressive clause revelation
    - Multi-action decision system
    - Cost/penalty mechanics
    - Decision tradeoffs
    """
    
    # Cost parameters
    STEP_COST = 0.05
    FALSE_POSITIVE_PENALTY = 0.3
    FALSE_NEGATIVE_PENALTY = 0.5
    EXPLORATION_REWARD = 0.1
    CORRECT_FLAG_REWARD = 0.4
    DECISION_BONUS = 0.3
    
    MAX_STEPS = 20
    INITIAL_BUDGET = 1.0
    
    def __init__(self, contract_data: Dict):
        """
        contract_data: {
            "contract_id": str,
            "clauses": List[ContractClause],
            "difficulty": str
        }
        """
        self.contract_id = contract_data["contract_id"]
        self.all_clauses = contract_data["clauses"]
        self.difficulty = contract_data.get("difficulty", "easy")
        
        # Shuffle clauses for variability
        random.shuffle(self.all_clauses)
        
        # State tracking
        self.visible_clause_ids: Set[str] = set()
        self.flagged_risks: Dict[str, RiskType] = {}
        self.decisions_made: Dict[str, Decision] = {}
        self.step_count = 0
        self.exploration_budget = self.INITIAL_BUDGET
        self.is_finalized = False
        
        # Ground truth
        self.ground_truth_risks: Dict[str, List[RiskType]] = {
            clause.id: clause.risks for clause in self.all_clauses
        }
        
        # Reveal first clause automatically
        if self.all_clauses:
            self.visible_clause_ids.add(self.all_clauses[0].id)
    
    def reset(self) -> Observation:
        """Reset environment to initial state"""
        random.shuffle(self.all_clauses)
        
        self.visible_clause_ids = set()
        self.flagged_risks = {}
        self.decisions_made = {}
        self.step_count = 0
        self.exploration_budget = self.INITIAL_BUDGET
        self.is_finalized = False
        
        # Reveal first clause
        if self.all_clauses:
            self.visible_clause_ids.add(self.all_clauses[0].id)
        
        return self._get_observation("Contract review started. Review visible clauses.")
    
    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict]:
        """Execute action and return new state"""
        
        if self.is_finalized:
            return (
                self._get_observation("Review already finalized."),
                Reward(value=0.01),
                True,
                {"error": "already_finalized"}
            )
        
        self.step_count += 1
        self.exploration_budget -= self.STEP_COST
        
        reward_breakdown = {"step_cost": -self.STEP_COST}
        message = ""
        done = False
        
        # Handle different action types
        if action.type == ActionType.REQUEST_NEXT:
            obs, reward_delta, msg = self._handle_request_next()
            reward_breakdown["exploration"] = reward_delta
            message = msg
        
        elif action.type == ActionType.FLAG_RISK:
            obs, reward_delta, msg = self._handle_flag_risk(action)
            reward_breakdown["flagging"] = reward_delta
            message = msg
        
        elif action.type == ActionType.DECIDE:
            obs, reward_delta, msg = self._handle_decision(action)
            reward_breakdown["decision"] = reward_delta
            message = msg
        
        elif action.type == ActionType.FINALIZE:
            obs, reward_delta, msg = self._handle_finalize()
            reward_breakdown["finalization"] = reward_delta
            message = msg
            done = True
            self.is_finalized = True
        
        else:
            obs = self._get_observation("Unknown action type.")
            reward_breakdown["invalid_action"] = -0.1
        
        # Check if max steps reached
        if self.step_count >= self.MAX_STEPS:
            done = True
            message += " Max steps reached."
        
        # Check if budget exhausted
        if self.exploration_budget <= 0:
            done = True
            message += " Exploration budget exhausted."
        
        total_reward = sum(reward_breakdown.values())
        # Clamp reward to strict (0, 1) — validator rejects 0.0 and 1.0
        clamped_reward = max(0.01, min(0.99, total_reward))
        
        return (
            self._get_observation(message),
            Reward(value=clamped_reward, breakdown=reward_breakdown),
            done,
            {"step": self.step_count}
        )
    
    def _handle_request_next(self) -> Tuple[Observation, float, str]:
        """Reveal next clause"""
        hidden_clauses = [c for c in self.all_clauses if c.id not in self.visible_clause_ids]
        
        if not hidden_clauses:
            return self._get_observation(""), 0.0, "No more clauses to reveal."
        
        next_clause = hidden_clauses[0]
        self.visible_clause_ids.add(next_clause.id)
        
        reward = self.EXPLORATION_REWARD
        message = f"Revealed clause {next_clause.id}"
        
        return self._get_observation(message), reward, message
    
    def _handle_flag_risk(self, action: Action) -> Tuple[Observation, float, str]:
        """Flag a risk in a clause"""
        if not action.clause_id or not action.risk_label:
            return self._get_observation(""), -0.1, "Missing clause_id or risk_label"
        
        if action.clause_id not in self.visible_clause_ids:
            return self._get_observation(""), -0.2, "Cannot flag invisible clause"
        
        # Check if already flagged
        if action.clause_id in self.flagged_risks:
            return self._get_observation(""), -0.1, "Clause already flagged"
        
        # Record the flag
        self.flagged_risks[action.clause_id] = action.risk_label
        
        # Calculate reward
        ground_truth = self.ground_truth_risks.get(action.clause_id, [])
        
        if action.risk_label in ground_truth:
            # Correct flag
            reward = self.CORRECT_FLAG_REWARD
            message = f"Correctly flagged {action.risk_label} in {action.clause_id}"
        else:
            # False positive
            reward = -self.FALSE_POSITIVE_PENALTY
            message = f"Incorrect flag: {action.risk_label} not in {action.clause_id}"
        
        return self._get_observation(message), reward, message
    
    def _handle_decision(self, action: Action) -> Tuple[Observation, float, str]:
        """Make accept/negotiate/reject decision for a clause"""
        if not action.clause_id or not action.decision:
            return self._get_observation(""), -0.1, "Missing clause_id or decision"
        
        if action.clause_id not in self.visible_clause_ids:
            return self._get_observation(""), -0.2, "Cannot decide on invisible clause"
        
        # Record decision
        self.decisions_made[action.clause_id] = action.decision
        
        # Get clause info
        clause = next((c for c in self.all_clauses if c.id == action.clause_id), None)
        if not clause:
            return self._get_observation(""), -0.1, "Clause not found"
        
        # Evaluate decision quality
        has_risks = len(clause.risks) > 0
        severity = clause.severity
        business_value = clause.business_value
        
        reward = 0.0
        
        if action.decision == Decision.ACCEPT:
            if not has_risks:
                reward = self.DECISION_BONUS
                message = "Good: Accepted safe clause"
            else:
                # Penalize accepting risky clause
                reward = -severity * 0.4
                message = f"Warning: Accepted risky clause (severity {severity:.2f})"
        
        elif action.decision == Decision.NEGOTIATE:
            if has_risks and business_value > 0.5:
                # Good: negotiate high-value risky clause
                reward = self.DECISION_BONUS
                message = "Good: Negotiating high-value risky clause"
            else:
                # Suboptimal negotiation
                reward = 0.1
                message = "Negotiation initiated"
        
        elif action.decision == Decision.REJECT:
            if has_risks and severity > 0.7:
                # Good: reject high-severity risk
                reward = self.DECISION_BONUS
                message = "Good: Rejected high-risk clause"
            elif business_value > 0.7:
                # Bad: rejected high-value clause
                reward = -0.3
                message = "Warning: Rejected high-value clause"
            else:
                reward = 0.1
                message = "Clause rejected"
        
        return self._get_observation(message), reward, message
    
    def _handle_finalize(self) -> Tuple[Observation, float, str]:
        """Finalize review and calculate final score"""
        
        # Calculate metrics
        all_risks = set()
        for risks in self.ground_truth_risks.values():
            all_risks.update(risks)
        
        flagged_clause_ids = set(self.flagged_risks.keys())
        risky_clause_ids = {cid for cid, risks in self.ground_truth_risks.items() if risks}
        
        # True positives: correctly flagged risky clauses
        tp = len(flagged_clause_ids & risky_clause_ids)
        
        # False positives: flagged safe clauses
        fp = len(flagged_clause_ids - risky_clause_ids)
        
        # False negatives: missed risky clauses that were visible
        visible_risky = risky_clause_ids & self.visible_clause_ids
        fn = len(visible_risky - flagged_clause_ids)
        
        # Precision & Recall
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Decision coverage
        decision_coverage = len(self.decisions_made) / len(self.visible_clause_ids) if self.visible_clause_ids else 0.0
        
        # Final reward
        finalization_reward = f1 * 0.5 + decision_coverage * 0.3
        
        message = f"Review finalized. F1={f1:.2f}, Decisions={decision_coverage:.2f}"
        
        return self._get_observation(message), finalization_reward, message
    
    def _get_observation(self, message: str = "") -> Observation:
        """Build current observation"""
        visible_clauses = [c for c in self.all_clauses if c.id in self.visible_clause_ids]
        
        # Remove ground truth from visible clauses
        sanitized_clauses = []
        for clause in visible_clauses:
            sanitized = clause.model_copy()
            # Don't reveal risks and severity in observation
            sanitized.risks = []
            sanitized.severity = 0.0
            sanitized_clauses.append(sanitized)
        
        flagged_list = [
            {"clause_id": cid, "risk_type": risk.value}
            for cid, risk in self.flagged_risks.items()
        ]
        
        return Observation(
            visible_clauses=sanitized_clauses,
            flagged_risks=flagged_list,
            total_clauses=len(self.all_clauses),
            clauses_revealed=len(self.visible_clause_ids),
            current_step=self.step_count,
            max_steps=self.MAX_STEPS,
            exploration_budget=max(0.0, self.exploration_budget),
            message=message
        )
    
    def state(self) -> Dict:
        """Return complete state for checkpointing"""
        return {
            "contract_id": self.contract_id,
            "difficulty": self.difficulty,
            "visible_clause_ids": list(self.visible_clause_ids),
            "flagged_risks": {k: v.value for k, v in self.flagged_risks.items()},
            "decisions_made": {k: v.value for k, v in self.decisions_made.items()},
            "step_count": self.step_count,
            "exploration_budget": self.exploration_budget,
            "is_finalized": self.is_finalized
        }
