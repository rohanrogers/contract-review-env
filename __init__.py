# Copyright (c) Rohan Rogers
# Contract Review Environment

"""
Contract Review Environment — Interactive legal contract review for AI agent evaluation.

This environment tests an agent's ability to perform strategic contract review,
balancing risk identification against business value preservation through
progressive clause revelation and multi-axis grading.

Tasks:
- easy_detection: Basic risk identification
- medium_analysis: Multi-clause risk analysis
- hard_comprehensive: Strategic trade-off evaluation (accept vs. negotiate vs. reject)

Example:
    >>> from contract_review import ContractReviewEnv
    >>>
    >>> async with ContractReviewEnv(base_url="http://localhost:7860") as env:
    ...     result = await env.reset(task_id="easy_detection")
    ...     result = await env.step({"type": "request_next_clause"})
    ...     print(result.observation)
"""

from .client import ContractReviewEnv

__all__ = ["ContractReviewEnv"]
