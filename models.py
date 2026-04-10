# Contract Review Environment - Pydantic Models
# Following calendar_env reference pattern from meta-pytorch/OpenEnv

"""
Data models for the Contract Review Environment.

These models define the action and observation types used by the OpenEnv
integration for the contract review server.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import Field

# Support both in-repo and standalone imports (matches calendar_env pattern)
try:
    from openenv.core.env_server.types import Action, Observation
except ImportError:
    from pydantic import BaseModel as Action
    from pydantic import BaseModel as Observation


class ContractAction(Action):
    """
    Action space for the Contract Review Environment.

    action_type values:
    - "request_next_clause": Reveal the next contract clause
    - "flag_risk": Flag a risk on a specific clause
    - "make_decision": Accept, negotiate, or reject a clause
    - "finalize_review": Complete the contract review
    """

    type: Literal["request_next_clause", "flag_risk", "make_decision", "finalize_review"] = Field(
        ..., description="Type of review action to perform"
    )
    clause_id: Optional[str] = Field(
        None, description="ID of the clause (e.g., 'C1') — required for flag_risk and make_decision"
    )
    risk_label: Optional[str] = Field(
        None, description="Risk type label — required for flag_risk"
    )
    decision: Optional[Literal["accept", "negotiate", "reject"]] = Field(
        None, description="Strategic decision — required for make_decision"
    )
    justification: Optional[str] = Field(
        None, description="Brief reasoning for the decision"
    )


class ContractObservation(Observation):
    """
    Observation returned by the Contract Review Environment.

    Provides the agent with visible contract clauses, flagged risks,
    step progress, and system feedback.
    """

    visible_clauses: List[Dict[str, Any]] = Field(
        default_factory=list, description="Contract clauses currently visible to the agent"
    )
    flagged_risks: List[Dict[str, Any]] = Field(
        default_factory=list, description="Risks flagged by the agent so far"
    )
    total_clauses: int = Field(0, description="Total clauses in the contract")
    clauses_revealed: int = Field(0, description="Number of clauses revealed so far")
    current_step: int = Field(0, description="Current episode step")
    max_steps: int = Field(20, description="Maximum allowed steps per episode")
    exploration_budget: float = Field(1.0, description="Remaining exploration budget [0.0, 1.0]")
    message: str = Field("", description="System feedback message")

    # Standard RL fields
    reward: Optional[float] = Field(None, description="Normalized reward signal [0.0, 1.0]")
    done: bool = Field(False, description="Whether the episode has terminated")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the execution"
    )


__all__ = [
    "ContractAction",
    "ContractObservation",
]
