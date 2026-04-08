"""
Task definitions and grading logic
"""

from typing import Dict, List
from server.environment import ContractReviewEnvironment, RiskType


class TaskGrader:
    """Base grader for contract review tasks"""
    
    def __init__(self, task_id: str, difficulty: str):
        self.task_id = task_id
        self.difficulty = difficulty
    
    def grade(self, env: ContractReviewEnvironment) -> float:
        """
        Grade the agent's performance
        Returns score between 0.0 and 1.0
        """
        raise NotImplementedError


class RiskDetectionGrader(TaskGrader):
    """Grade based on risk detection accuracy"""
    
    def grade(self, env: ContractReviewEnvironment) -> float:
        # Get all ground truth risks
        all_risky_clause_ids = {
            cid for cid, risks in env.ground_truth_risks.items() if risks
        }
        
        # Get visible risky clauses
        visible_risky = all_risky_clause_ids & env.visible_clause_ids
        
        # Get flagged clauses
        flagged_clause_ids = set(env.flagged_risks.keys())
        
        # Calculate metrics
        tp = len(flagged_clause_ids & visible_risky)
        fp = len(flagged_clause_ids - visible_risky)
        fn = len(visible_risky - flagged_clause_ids)
        
        # Precision and Recall
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        
        # F1 Score
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Penalize if didn't explore enough
        exploration_ratio = len(env.visible_clause_ids) / len(env.all_clauses) if env.all_clauses else 0.0
        exploration_penalty = max(0, 0.7 - exploration_ratio) * 0.3
        
        score = f1 - exploration_penalty
        return max(0.01, min(0.99, score))


class DecisionQualityGrader(TaskGrader):
    """Grade based on decision-making quality"""
    
    def grade(self, env: ContractReviewEnvironment) -> float:
        if not env.decisions_made:
            return 0.01
        
        total_score = 0.0
        num_decisions = 0
        
        for clause_id, decision in env.decisions_made.items():
            clause = next((c for c in env.all_clauses if c.id == clause_id), None)
            if not clause:
                continue
            
            has_risks = len(clause.risks) > 0
            severity = clause.severity
            business_value = clause.business_value
            
            # Scoring logic
            if decision.value == "accept":
                if not has_risks:
                    score = 1.0  # Perfect
                else:
                    score = max(0, 1.0 - severity)  # Penalize by severity
            
            elif decision.value == "negotiate":
                if has_risks and business_value > 0.5:
                    score = 1.0  # Perfect negotiation
                elif has_risks:
                    score = 0.7  # Okay negotiation
                else:
                    score = 0.5  # Unnecessary negotiation
            
            elif decision.value == "reject":
                if has_risks and severity > 0.7:
                    score = 1.0  # Perfect rejection
                elif has_risks:
                    score = 0.6  # Okay rejection
                else:
                    score = max(0, 1.0 - business_value)  # Penalize if high value
            else:
                score = 0.0
            
            total_score += score
            num_decisions += 1
        
        avg_score = total_score / num_decisions if num_decisions > 0 else 0.0
        
        # Reward decision coverage
        decision_coverage = len(env.decisions_made) / len(env.visible_clause_ids) if env.visible_clause_ids else 0.0
        
        final_score = avg_score * 0.7 + decision_coverage * 0.3
        return max(0.01, min(0.99, final_score))


class EfficiencyGrader(TaskGrader):
    """Grade based on efficiency and budget management"""
    
    def grade(self, env: ContractReviewEnvironment) -> float:
        # Budget efficiency
        budget_remaining_ratio = env.exploration_budget / env.INITIAL_BUDGET
        
        # Step efficiency
        step_efficiency = 1.0 - (env.step_count / env.MAX_STEPS)
        
        # Detection efficiency (precision matters)
        flagged_clause_ids = set(env.flagged_risks.keys())
        risky_clause_ids = {cid for cid, risks in env.ground_truth_risks.items() if risks}
        visible_risky = risky_clause_ids & env.visible_clause_ids
        
        tp = len(flagged_clause_ids & visible_risky)
        fp = len(flagged_clause_ids - visible_risky)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        
        # Combined score
        efficiency_score = (
            budget_remaining_ratio * 0.3 +
            step_efficiency * 0.3 +
            precision * 0.4
        )
        
        return max(0.01, min(0.99, efficiency_score))


class BusinessAwarenessGrader(TaskGrader):
    """Grade based on preserving high-value clauses while managing risk."""
    
    def grade(self, env: ContractReviewEnvironment) -> float:
        if not env.visible_clause_ids:
            return 0.01
        
        total_value_score = 0.0
        num_evaluated = 0
        
        for clause in env.all_clauses:
            if clause.id not in env.visible_clause_ids:
                continue
            
            decision = env.decisions_made.get(clause.id)
            has_risks = len(clause.risks) > 0
            bv = clause.business_value
            severity = clause.severity
            
            if decision is None:
                # No decision made on this clause — minor penalty for high-value clauses
                if bv > 0.6:
                    total_value_score += 0.3
                else:
                    total_value_score += 0.5
            elif decision.value == "reject":
                if bv > 0.6 and has_risks:
                    # Rejected high-value risky clause — should have negotiated
                    total_value_score += 0.2
                elif bv > 0.6 and not has_risks:
                    # Rejected high-value safe clause — very bad
                    total_value_score += 0.0
                else:
                    # Rejected low-value clause — fine
                    total_value_score += 0.7
            elif decision.value == "negotiate":
                if has_risks and bv > 0.5:
                    # Negotiated risky high-value clause — optimal
                    total_value_score += 1.0
                elif has_risks:
                    # Negotiated risky low-value clause — acceptable
                    total_value_score += 0.6
                else:
                    # Negotiated safe clause — unnecessary
                    total_value_score += 0.5
            elif decision.value == "accept":
                if not has_risks and bv > 0.5:
                    # Accepted safe high-value clause — optimal
                    total_value_score += 1.0
                elif not has_risks:
                    # Accepted safe low-value clause — fine
                    total_value_score += 0.8
                elif severity < 0.5:
                    # Accepted low-risk clause — acceptable
                    total_value_score += 0.6
                else:
                    # Accepted high-risk clause — bad
                    total_value_score += max(0.0, 1.0 - severity)
            
            num_evaluated += 1
        
        avg_score = total_value_score / num_evaluated if num_evaluated > 0 else 0.0
        return max(0.01, min(0.99, avg_score))


class ComprehensiveGrader(TaskGrader):
    """Comprehensive grading combining all aspects — emphasizes strategic trade-offs."""
    
    def grade(self, env: ContractReviewEnvironment) -> float:
        risk_grader = RiskDetectionGrader(self.task_id, self.difficulty)
        decision_grader = DecisionQualityGrader(self.task_id, self.difficulty)
        business_grader = BusinessAwarenessGrader(self.task_id, self.difficulty)
        efficiency_grader = EfficiencyGrader(self.task_id, self.difficulty)
        
        risk_score = risk_grader.grade(env)
        decision_score = decision_grader.grade(env)
        business_score = business_grader.grade(env)
        efficiency_score = efficiency_grader.grade(env)
        
        # Weighted combination — decision quality and business awareness are key
        final_score = (
            risk_score * 0.25 +
            decision_score * 0.35 +
            business_score * 0.25 +
            efficiency_score * 0.15
        )
        
        return max(0.01, min(0.99, final_score))


# Task definitions
TASKS = {
    "easy_detection": {
        "task_id": "easy_detection",
        "difficulty": "easy",
        "contract_id": "EASY_001",
        "description": "Review a simple SaaS contract and identify obvious risk clauses (auto-renewal, unlimited liability).",
        "grader": RiskDetectionGrader("easy_detection", "easy"),
        "target_score": 0.7
    },
    "medium_analysis": {
        "task_id": "medium_analysis",
        "difficulty": "medium",
        "contract_id": "MEDIUM_001",
        "description": "Analyze a vendor agreement with indirect wording. Identify hidden risks (unilateral termination, broad indemnification) and make accept/negotiate/reject decisions.",
        "grader": DecisionQualityGrader("medium_analysis", "medium"),
        "target_score": 0.65
    },
    "hard_comprehensive": {
        "task_id": "hard_comprehensive",
        "difficulty": "hard",
        "contract_id": "HARD_001",
        "description": "Conduct strategic review of a complex partnership agreement where some risky clauses have high business value. Agent must balance risk management against deal preservation — blindly rejecting all risks will kill the deal.",
        "grader": ComprehensiveGrader("hard_comprehensive", "hard"),
        "target_score": 0.55
    }
}


def get_task(task_id: str) -> Dict:
    """Get task definition by ID"""
    return TASKS.get(task_id)


def get_all_tasks() -> List[Dict]:
    """Get all task definitions"""
    return list(TASKS.values())
