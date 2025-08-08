from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Value Objects

class CaseStatus(str, Enum):
    NEW = "new"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskType(str, Enum):
    UPLOAD = "upload"
    INTERPRET = "interpret"
    BEAM_CALC = "beam_calc"
    CONVERT = "convert"
    DOWNLOAD = "download"

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# Domain Models

@dataclass
class Case:
    case_id: str
    status: CaseStatus
    beam_count: int
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Job:
    job_id: str
    case_id: str
    status: JobStatus
    gpu_allocation: List[int]
    priority: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class Task:
    task_id: str
    job_id: str
    type: TaskType
    status: TaskStatus
    parameters: Dict[str, Any] = field(default_factory=dict)
