from dataclasses import dataclass, field
from typing import Optional

@dataclass
class AppConfig:
    name: str = "MQI Communicator"
    version: str = "2.0.0"
    environment: str = "production"

@dataclass
class PathsConfig:
    local_logdata: str
    remote_workspace: str

@dataclass
class SSHConfig:
    host: str
    port: int = 22
    username: str
    key_file: Optional[str] = None
    connection_pool_size: int = 5

@dataclass
class ResourcesConfig:
    max_concurrent_jobs: int = 10
    gpu_count: int = 8
    min_disk_space_gb: int = 100

@dataclass
class RetryPolicyConfig:
    max_attempts: int = 3
    base_delay: float = 1.0

@dataclass
class ProcessingConfig:
    scan_interval_seconds: int = 60
    retry_policy: RetryPolicyConfig = field(default_factory=RetryPolicyConfig)

@dataclass
class MonitoringConfig:
    metrics_port: int = 8000
    metrics_interval_seconds: int = 30
    health_check_interval_seconds: int = 60

@dataclass
class MainConfig:
    app: AppConfig = field(default_factory=AppConfig)
    paths: PathsConfig
    ssh: SSHConfig
    resources: ResourcesConfig = field(default_factory=ResourcesConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
