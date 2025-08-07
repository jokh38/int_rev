# MQI Communicator 구현 가이드라인

## 1. 코드 구조 템플릿

### 1.1 인터페이스 정의 템플릿
```python
# src/interfaces/service_interfaces.py
from typing import Protocol, List, Optional
from abc import abstractmethod

class ICaseService(Protocol):
    """Case 서비스 인터페이스"""
    
    @abstractmethod
    def scan_for_new_cases(self) -> List[str]:
        """새로운 케이스 스캔
        
        Returns:
            List[str]: 새로 발견된 case_id 목록
            
        Raises:
            FileSystemError: 파일시스템 접근 실패
        """
        ...
    
    @abstractmethod
    def get_case(self, case_id: str) -> Optional['Case']:
        """케이스 조회
        
        Args:
            case_id: 조회할 케이스 ID
            
        Returns:
            Case 객체 또는 None
            
        Raises:
            RepositoryError: 저장소 접근 실패
        """
        ...
```

### 1.2 구현체 템플릿
```python
# src/services/case_service.py
from typing import List, Optional
import logging
from dataclasses import dataclass

from ..interfaces import ICaseService, ICaseRepository
from ..models import Case, CaseStatus
from ..exceptions import ServiceError, ValidationError

logger = logging.getLogger(__name__)

@dataclass
class CaseService(ICaseService):
    """Case 서비스 구현체"""
    
    case_repository: ICaseRepository
    file_system: IFileSystem
    
    def __post_init__(self):
        """초기화 후 검증"""
        if not self.case_repository:
            raise ValidationError("case_repository is required")
        if not self.file_system:
            raise ValidationError("file_system is required")
    
    def scan_for_new_cases(self) -> List[str]:
        """새로운 케이스 스캔"""
        try:
            # 1. 파일시스템에서 디렉토리 목록 조회
            directories = self.file_system.list_directories()
            logger.debug(f"Found {len(directories)} directories")
            
            # 2. 기존 케이스 목록 조회
            existing_cases = self.case_repository.get_all_case_ids()
            
            # 3. 새로운 케이스 필터링
            new_cases = [d for d in directories if d not in existing_cases]
            
            # 4. 새로운 케이스 등록
            for case_id in new_cases:
                self._register_new_case(case_id)
            
            logger.info(f"Found {len(new_cases)} new cases")
            return new_cases
            
        except Exception as e:
            logger.error(f"Failed to scan for new cases: {e}")
            raise ServiceError(f"Case scanning failed: {e}") from e
    
    def _register_new_case(self, case_id: str) -> None:
        """새 케이스 등록 (내부 메서드)"""
        case = Case(
            case_id=case_id,
            status=CaseStatus.NEW,
            beam_count=0,
            metadata={}
        )
        self.case_repository.save(case)
```

### 1.3 테스트 템플릿
```python
# tests/unit/services/test_case_service.py
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.services import CaseService
from src.models import Case, CaseStatus
from src.exceptions import ServiceError

class TestCaseService:
    """CaseService 단위 테스트"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock repository fixture"""
        repo = Mock()
        repo.get_all_case_ids.return_value = ["case_001", "case_002"]
        return repo
    
    @pytest.fixture
    def mock_file_system(self):
        """Mock file system fixture"""
        fs = Mock()
        fs.list_directories.return_value = ["case_001", "case_002", "case_003"]
        return fs
    
    @pytest.fixture
    def service(self, mock_repository, mock_file_system):
        """Service fixture"""
        return CaseService(
            case_repository=mock_repository,
            file_system=mock_file_system
        )
    
    def test_scan_for_new_cases_success(self, service, mock_repository):
        """새 케이스 스캔 성공 테스트"""
        # When
        result = service.scan_for_new_cases()
        
        # Then
        assert len(result) == 1
        assert "case_003" in result
        mock_repository.save.assert_called_once()
    
    def test_scan_for_new_cases_no_new_cases(self, service, mock_file_system):
        """새 케이스 없음 테스트"""
        # Given
        mock_file_system.list_directories.return_value = ["case_001", "case_002"]
        
        # When
        result = service.scan_for_new_cases()
        
        # Then
        assert len(result) == 0
    
    def test_scan_for_new_cases_error_handling(self, service, mock_file_system):
        """에러 처리 테스트"""
        # Given
        mock_file_system.list_directories.side_effect = Exception("Access denied")
        
        # When/Then
        with pytest.raises(ServiceError) as exc_info:
            service.scan_for_new_cases()
        
        assert "Case scanning failed" in str(exc_info.value)
```

## 2. 에러 처리 패턴

### 2.1 Custom Exception Hierarchy
```python
# src/exceptions.py
class MQIError(Exception):
    """Base exception for MQI Communicator"""
    pass

class ConfigurationError(MQIError):
    """설정 관련 에러"""
    pass

class ServiceError(MQIError):
    """서비스 레이어 에러"""
    pass

class RepositoryError(MQIError):
    """저장소 레이어 에러"""
    pass

class ConnectionError(MQIError):
    """연결 관련 에러"""
    pass

class ValidationError(MQIError):
    """검증 실패 에러"""
    pass

class ResourceError(MQIError):
    """리소스 관련 에러"""
    pass
```

### 2.2 Error Context Manager
```python
# src/utils/error_handling.py
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

@contextmanager
def error_handler(operation: str, raise_on_error: bool = True):
    """에러 처리 컨텍스트 매니저
    
    Usage:
        with error_handler("database operation"):
            perform_database_operation()
    """
    try:
        logger.debug(f"Starting {operation}")
        yield
        logger.debug(f"Completed {operation}")
    except Exception as e:
        logger.error(f"Failed {operation}: {e}", exc_info=True)
        if raise_on_error:
            raise
        return None
```

## 3. 동시성 처리 패턴

### 3.1 Thread-Safe State Management
```python
# src/infrastructure/state/thread_safe_state.py
import threading
from typing import Any, Dict
import json
from pathlib import Path

class ThreadSafeStateManager:
    """스레드 안전 상태 관리자"""
    
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self._lock = threading.RLock()
        self._state: Dict[str, Any] = {}
        self._load_state()
    
    def get(self, key: str, default: Any = None) -> Any:
        """스레드 안전 읽기"""
        with self._lock:
            return self._state.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """스레드 안전 쓰기"""
        with self._lock:
            self._state[key] = value
            self._persist()
    
    def update_atomic(self, key: str, updater: callable) -> Any:
        """원자적 업데이트"""
        with self._lock:
            current = self._state.get(key)
            new_value = updater(current)
            self._state[key] = new_value
            self._persist()
            return new_value
    
    def _persist(self) -> None:
        """상태를 파일에 저장"""
        temp_file = self.state_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(self._state, f, indent=2)
        temp_file.replace(self.state_file)  # Atomic rename
```

### 3.2 Resource Pool Pattern
```python
# src/infrastructure/connection/connection_pool.py
import queue
import threading
from contextlib import contextmanager
from typing import Optional
import paramiko

class SSHConnectionPool:
    """SSH 연결 풀"""
    
    def __init__(self, config: dict, pool_size: int = 5):
        self.config = config
        self.pool_size = pool_size
        self._pool = queue.Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._initialize_pool()
    
    def _initialize_pool(self):
        """연결 풀 초기화"""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            self._pool.put(conn)
    
    def _create_connection(self) -> paramiko.SSHClient:
        """새 SSH 연결 생성"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=self.config['host'],
            port=self.config['port'],
            username=self.config['username'],
            key_filename=self.config['key_file']
        )
        return client
    
    @contextmanager
    def get_connection(self, timeout: float = 30.0):
        """연결 획득 컨텍스트 매니저"""
        connection = None
        try:
            connection = self._pool.get(timeout=timeout)
            yield connection
        finally:
            if connection:
                if connection.get_transport().is_active():
                    self._pool.put(connection)
                else:
                    # 죽은 연결은 새로 생성
                    new_conn = self._create_connection()
                    self._pool.put(new_conn)
```

## 4. 의존성 주입 패턴

### 4.1 Factory Pattern
```python
# src/factories/service_factory.py
from typing import Dict, Any
from ..interfaces import *
from ..services import *
from ..infrastructure import *

class ServiceFactory:
    """서비스 팩토리"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._instances = {}
    
    def get_case_service(self) -> ICaseService:
        """CaseService 인스턴스 반환"""
        if 'case_service' not in self._instances:
            self._instances['case_service'] = CaseService(
                case_repository=self.get_case_repository(),
                file_system=self.get_file_system()
            )
        return self._instances['case_service']
    
    def get_case_repository(self) -> ICaseRepository:
        """CaseRepository 인스턴스 반환"""
        if 'case_repository' not in self._instances:
            self._instances['case_repository'] = CaseRepository(
                state_manager=self.get_state_manager()
            )
        return self._instances['case_repository']
    
    def get_state_manager(self) -> IStateManager:
        """StateManager 인스턴스 반환"""
        if 'state_manager' not in self._instances:
            self._instances['state_manager'] = ThreadSafeStateManager(
                state_file=Path(self.config['state_file'])
            )
        return self._instances['state_manager']
```

### 4.2 Dependency Injection Container
```python
# src/container.py
from dependency_injector import containers, providers
from .services import *
from .infrastructure import *

class Container(containers.DeclarativeContainer):
    """DI Container"""
    
    # Configuration
    config = providers.Configuration()
    
    # Infrastructure
    state_manager = providers.Singleton(
        ThreadSafeStateManager,
        state_file=config.state.file_path
    )
    
    connection_pool = providers.Singleton(
        SSHConnectionPool,
        config=config.ssh,
        pool_size=config.ssh.pool_size
    )
    
    # Repositories
    case_repository = providers.Singleton(
        CaseRepository,
        state_manager=state_manager
    )
    
    job_repository = providers.Singleton(
        JobRepository,
        state_manager=state_manager
    )
    
    # Services
    case_service = providers.Singleton(
        CaseService,
        case_repository=case_repository,
        file_system=providers.Singleton(FileSystem)
    )
    
    job_service = providers.Singleton(
        JobService,
        job_repository=job_repository,
        resource_service=providers.Singleton(ResourceService)
    )
```

## 5. 로깅 및 모니터링

### 5.1 Structured Logging
```python
# src/utils/logging.py
import logging
import json
from datetime import datetime
from typing import Any, Dict

class StructuredLogger:
    """구조화된 로거"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context = {}
    
    def with_context(self, **kwargs) -> 'StructuredLogger':
        """컨텍스트 추가"""
        new_logger = StructuredLogger(self.logger.name)
        new_logger.context = {**self.context, **kwargs}
        return new_logger
    
    def _format_message(self, level: str, message: str, **kwargs) -> str:
        """메시지 포맷팅"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "context": {**self.context, **kwargs}
        }
        return json.dumps(log_entry)
    
    def info(self, message: str, **kwargs):
        """Info 로그"""
        self.logger.info(self._format_message("INFO", message, **kwargs))
    
    def error(self, message: str, **kwargs):
        """Error 로그"""
        self.logger.error(self._format_message("ERROR", message, **kwargs))
```

### 5.2 Metrics Collection
```python
# src/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# 메트릭 정의
case_processed = Counter('mqi_cases_processed_total', 'Total processed cases')
case_failed = Counter('mqi_cases_failed_total', 'Total failed cases')
processing_time = Histogram('mqi_processing_duration_seconds', 'Processing time')
active_jobs = Gauge('mqi_active_jobs', 'Number of active jobs')
gpu_usage = Gauge('mqi_gpu_usage', 'GPU usage', ['gpu_id'])

def track_processing_time(operation: str):
    """처리 시간 추적 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                processing_time.labels(operation=operation).observe(time.time() - start)
                return result
            except Exception as e:
                case_failed.inc()
                raise
        return wrapper
    return decorator

class MetricsCollector:
    """메트릭 수집기"""
    
    @track_processing_time("case_processing")
    def process_case(self, case_id: str):
        """케이스 처리 with 메트릭"""
        active_jobs.inc()
        try:
            # 처리 로직
            case_processed.inc()
        finally:
            active_jobs.dec()
```

## 6. 테스트 전략 상세

### 6.1 Test Fixtures
```python
# tests/fixtures/domain_fixtures.py
import pytest
from datetime import datetime
from src.models import Case, Job, CaseStatus, JobStatus

@pytest.fixture
def sample_case():
    """샘플 케이스 fixture"""
    return Case(
        case_id="test_case_001",
        status=CaseStatus.NEW,
        beam_count=4,
        created_at=datetime.now(),
        metadata={"patient_id": "P001"}
    )

@pytest.fixture
def sample_job(sample_case):
    """샘플 잡 fixture"""
    return Job(
        job_id="job_001",
        case_id=sample_case.case_id,
        status=JobStatus.PENDING,
        gpu_allocation=[],
        priority=1
    )
```

### 6.2 Integration Test Setup
```python
# tests/integration/conftest.py
import pytest
import docker
from pathlib import Path
import tempfile

@pytest.fixture(scope="session")
def ssh_server():
    """Docker SSH 서버 fixture"""
    client = docker.from_env()
    container = client.containers.run(
        "linuxserver/openssh-server",
        environment={
            "PASSWORD_ACCESS": "true",
            "USER_NAME": "test",
            "USER_PASSWORD": "test"
        },
        ports={'2222/tcp': 2222},
        detach=True
    )
    yield container
    container.stop()
    container.remove()

@pytest.fixture
def temp_workspace():
    """임시 작업 공간 fixture"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        (workspace / "cases").mkdir()
        (workspace / "results").mkdir()
        yield workspace
```

### 6.3 E2E Test Example
```python
# tests/e2e/test_workflow.py
import pytest
from src.container import Container
from tests.fixtures import create_test_case_files

class TestE2EWorkflow:
    """End-to-End 워크플로우 테스트"""
    
    @pytest.fixture
    def container(self, ssh_server, temp_workspace):
        """DI Container fixture"""
        container = Container()
        container.config.from_dict({
            "paths": {
                "local_logdata": str(temp_workspace / "cases"),
                "remote_workspace": "/tmp/mqi"
            },
            "ssh": {
                "host": "localhost",
                "port": 2222,
                "username": "test",
                "password": "test"
            }
        })
        return container
    
    def test_complete_workflow(self, container, temp_workspace):
        """전체 워크플로우 테스트"""
        # Given: 테스트 케이스 파일 생성
        case_id = create_test_case_files(temp_workspace / "cases")
        
        # When: 워크플로우 실행
        orchestrator = container.workflow_orchestrator()
        orchestrator.process_case(case_id)
        
        # Then: 결과 확인
        results_path = temp_workspace / "results" / case_id
        assert results_path.exists()
        assert (results_path / "output.dcm").exists()
```

## 7. CI/CD Pipeline

### 7.1 GitHub Actions Workflow
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      ssh:
        image: linuxserver/openssh-server
        env:
          PASSWORD_ACCESS: true
          USER_NAME: test
          USER_PASSWORD: test
        ports:
          - 2222:2222
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install poetry
        poetry install
    
    - name: Run linting
      run: |
        poetry run black --check src tests
        poetry run flake8 src tests
        poetry run mypy src
    
    - name: Run unit tests
      run: |
        poetry run pytest tests/unit -v --cov=src --cov-report=xml
    
    - name: Run integration tests
      run: |
        poetry run pytest tests/integration -v
    
    - name: Run E2E tests
      run: |
        poetry run pytest tests/e2e -v
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## 8. 배포 스크립트

### 8.1 Deployment Script
```bash
#!/bin/bash
# scripts/deploy.sh

set -e

# 환경 변수 확인
if [ -z "$ENV" ]; then
    echo "ENV not set. Using 'production'"
    ENV="production"
fi

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 마이그레이션 실행
python scripts/migrate_state.py

# 설정 검증
python -m src.utils.validate_config

# 서비스 시작
if [ "$ENV" == "production" ]; then
    # Production: systemd service
    sudo systemctl restart mqi-communicator
else
    # Development: direct run
    python main.py
fi
```

## 9. 문제 해결 가이드

### 9.1 Common Issues
| 문제 | 원인 | 해결 방법 |
|-----|------|----------|
| SSH 연결 실패 | 네트워크 문제 | Retry with exponential backoff |
| GPU 할당 실패 | 리소스 부족 | Queue 대기 또는 우선순위 조정 |
| 상태 파일 손상 | 비정상 종료 | Backup 복구 또는 재스캔 |
| 메모리 누수 | 리소스 미해제 | Context manager 사용 |

### 9.2 Debug Mode
```python
# src/utils/debug.py
import os
import logging

def setup_debug_mode():
    """디버그 모드 설정"""
    if os.getenv("DEBUG", "").lower() == "true":
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 추가 디버그 설정
        import paramiko
        paramiko.util.log_to_file("paramiko.log")
        
        # SQL 쿼리 로깅
        logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
```

## 10. 성능 최적화

### 10.1 Caching Strategy
```python
# src/utils/caching.py
from functools import lru_cache, wraps
import time

def timed_lru_cache(seconds: int, maxsize: int = 128):
    """시간 제한 LRU 캐시"""
    def wrapper(func):
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = seconds
        func.expiration = time.time() + seconds
        
        @wraps(func)
        def wrapped(*args, **kwargs):
            if time.time() >= func.expiration:
                func.cache_clear()
                func.expiration = time.time() + func.lifetime
            return func(*args, **kwargs)
        
        return wrapped
    return wrapper

class CacheManager:
    """캐시 관리자"""
    
    @timed_lru_cache(seconds=300)  # 5분 캐시
    def get_gpu_status(self):
        """GPU 상태 조회 (캐시됨)"""
        return self._fetch_gpu_status()
```

### 10.2 Async I/O
```python
# src/utils/async_io.py
import asyncio
import aiofiles
from typing import List

class AsyncTransferManager:
    """비동기 파일 전송 관리자"""
    
    async def upload_files(self, files: List[str]):
        """병렬 파일 업로드"""
        tasks = [self._upload_file(f) for f in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def _upload_file(self, filepath: str):
        """단일 파일 업로드"""
        async with aiofiles.open(filepath, 'rb') as f:
            content = await f.read()
            # SFTP 업로드 로직
            return await self._sftp_upload(filepath, content)
```