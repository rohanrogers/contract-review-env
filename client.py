# Copyright (c) Rohan Rogers
# Contract Review Environment Client

"""
Contract Review Environment Client.

This module provides the client for connecting to a Contract Review Environment server.
ContractReviewEnv extends HTTPEnvClient to provide typed interactions for
legal contract review with strategic trade-off evaluation.

Example:
    >>> from contract_review import ContractReviewEnv
    >>>
    >>> # Connect to a running server
    >>> async with ContractReviewEnv(base_url="http://localhost:7860") as env:
    ...     result = await env.reset(task_id="easy_detection")
    ...     result = await env.step({"type": "request_next_clause"})
    ...     print(result.observation)

    >>> # Sync usage
    >>> with ContractReviewEnv(base_url="http://localhost:7860").sync() as env:
    ...     result = env.reset(task_id="easy_detection")
    ...     result = env.step({"type": "request_next_clause"})

Example with HuggingFace Space:
    >>> env = ContractReviewEnv(base_url="https://rohanrogers-contract-review-env.hf.space")
    >>> async with env:
    ...     result = await env.reset(task_id="hard_comprehensive")
    ...     # Agent reviews clauses, flags risks, makes strategic decisions
    ...     result = await env.step({
    ...         "type": "make_decision",
    ...         "clause_id": "C1",
    ...         "decision": "negotiate",
    ...         "justification": "High risk but high business value"
    ...     })
"""

try:
    from openenv.core.http_env_client import HTTPEnvClient

    class ContractReviewEnv(HTTPEnvClient):
        """
        Client for the Contract Review Environment.

        This environment tests an agent's ability to perform strategic legal
        contract review, balancing risk management against business value
        preservation. The agent must:

        - Explore contracts progressively via clause revelation
        - Flag risks with appropriate risk labels
        - Make strategic decisions (accept/negotiate/reject) considering both
          risk severity AND business value
        - Finalize reviews efficiently within step budgets

        The client inherits all HTTPEnvClient functionality:
        - `reset(**kwargs)`: Start a new contract review episode
        - `step(action)`: Submit a review action
        - `state()`: Get current environment state

        Available task difficulties:
        - easy_detection: Basic risk identification
        - medium_analysis: Multi-clause risk analysis
        - hard_comprehensive: Strategic trade-off evaluation
        """

        pass  # HTTPEnvClient provides all needed functionality

except ImportError:
    # Fallback for environments where openenv-core isn't installed
    # (e.g., during local testing without the full framework)
    class ContractReviewEnv:
        """Stub client — install openenv-core for full functionality."""

        def __init__(self, base_url: str = "http://localhost:7860"):
            self.base_url = base_url
