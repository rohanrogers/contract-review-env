"""
FastAPI server implementing OpenEnv specification
"""

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, List
import uvicorn

from server.environment import (
    ContractReviewEnvironment,
    Action,
    Observation,
    Reward,
    ActionType,
    Decision,
    RiskType
)
from contracts.datasets import get_contract_by_id, get_contracts_by_difficulty
from tasks.graders import get_task, get_all_tasks


app = FastAPI(
    title="Contract Review Environment",
    description="Interactive legal contract review environment for AI agents",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global environment instance
current_env: Optional[ContractReviewEnvironment] = None
current_task_id: Optional[str] = None


class ResetRequest(BaseModel):
    task_id: Optional[str] = "easy_detection"
    contract_id: Optional[str] = None


class ResetResponse(BaseModel):
    observation: Observation
    task_id: str
    contract_id: str


class StepRequest(BaseModel):
    action: Action


class StepResponse(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
    info: Dict


class StateResponse(BaseModel):
    state: Dict
    task_id: Optional[str]


class GradeResponse(BaseModel):
    task_id: str
    score: float
    max_score: float = 1.0


class TaskInfo(BaseModel):
    task_id: str
    difficulty: str
    description: str
    target_score: float


class HealthResponse(BaseModel):
    status: str
    environment: str
    tasks_available: int


@app.get("/", response_model=HealthResponse)
async def root():
    """Root health check endpoint"""
    return HealthResponse(
        status="healthy",
        environment="contract_review_v2",
        tasks_available=len(get_all_tasks())
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check — required by OpenEnv judge validation script"""
    return HealthResponse(
        status="healthy",
        environment="contract_review_v2",
        tasks_available=len(get_all_tasks())
    )


@app.get("/healthz", response_model=HealthResponse)
async def healthz():
    """Kubernetes-style liveness probe alias"""
    return HealthResponse(
        status="healthy",
        environment="contract_review_v2",
        tasks_available=len(get_all_tasks())
    )


@app.get("/tasks", response_model=List[TaskInfo])
async def list_tasks():
    """List all available tasks"""
    tasks = get_all_tasks()
    return [
        TaskInfo(
            task_id=t["task_id"],
            difficulty=t["difficulty"],
            description=t["description"],
            target_score=t["target_score"]
        )
        for t in tasks
    ]


@app.get("/tasks/{task_id}", response_model=TaskInfo)
async def get_task_info(task_id: str):
    """Get information about a specific task"""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return TaskInfo(
        task_id=task["task_id"],
        difficulty=task["difficulty"],
        description=task["description"],
        target_score=task["target_score"]
    )


@app.post("/reset", response_model=ResetResponse)
async def reset(request: Optional[ResetRequest] = Body(default=None)):
    """Reset environment to initial state"""
    global current_env, current_task_id
    
    if request is None:
        request = ResetRequest()
    
    # Get task
    task = get_task(request.task_id)
    if not task:
        raise HTTPException(status_code=400, detail=f"Task {request.task_id} not found")
    
    # Get contract
    contract_id = request.contract_id or task["contract_id"]
    contract_data = get_contract_by_id(contract_id)
    
    if not contract_data:
        raise HTTPException(status_code=400, detail=f"Contract {contract_id} not found")
    
    # Create environment
    current_env = ContractReviewEnvironment(contract_data)
    current_task_id = request.task_id
    
    # Reset
    observation = current_env.reset()
    
    return ResetResponse(
        observation=observation,
        task_id=current_task_id,
        contract_id=contract_id
    )


@app.post("/step", response_model=StepResponse)
async def step(request: StepRequest):
    """Execute an action in the environment"""
    global current_env
    
    if current_env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    try:
        observation, reward, done, info = current_env.step(request.action)
        
        return StepResponse(
            observation=observation,
            reward=reward,
            done=done,
            info=info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step execution failed: {str(e)}")


@app.get("/state", response_model=StateResponse)
async def get_state():
    """Get current environment state"""
    global current_env, current_task_id
    
    if current_env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    state = current_env.state()
    
    return StateResponse(
        state=state,
        task_id=current_task_id
    )


@app.post("/grade", response_model=GradeResponse)
async def grade():
    """Grade current episode"""
    global current_env, current_task_id
    
    if current_env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")
    
    if current_task_id is None:
        raise HTTPException(status_code=400, detail="No task selected.")
    
    task = get_task(current_task_id)
    if not task:
        raise HTTPException(status_code=400, detail=f"Task {current_task_id} not found")
    
    grader = task["grader"]
    score = grader.grade(current_env)
    
    return GradeResponse(
        task_id=current_task_id,
        score=score,
        max_score=1.0
    )

def main(host: str = "0.0.0.0", port: int = 7860):
    """Entry point for direct execution."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
