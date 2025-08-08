
# MQI Communicator: 최종 개발 명세서 (Final Development Specification)

## 1\. 개요 (Overview)

### 1.1. 프로젝트 목표

의료물리 품질보증(QA) 워크플로우를 자동화하는 분산형 Python 시스템을 구축한다. 이 시스템은 새로운 환자 데이터 스캔, 원격 HPC 환경으로의 전송, GPU 계산 실행, 결과 회수 및 전체 프로세스 관리를 안정적이고 확장 가능하게 수행하는 것을 목표로 한다.

### 1.2. 핵심 아키텍처

본 시스템은 **지휘자-작업자(Conductor-Worker)** 패턴의 마이크로서비스 아키텍처를 채택한다.

  * **지휘자 (Conductor)**: 전체 워크플로우를 조정하고 작업자에게 명령을 내리는 중앙 통제 프로그램.
  * **작업자 (Workers)**: 특정 단일 책임을 수행하는 독립적인 프로그램들.
  * **메시지 큐 (Message Queue)**: 지휘자와 작업자 간의 모든 통신은 메시지 큐를 통해 비동기적으로 이루어져 시스템의 결합도를 낮추고 유연성을 확보한다.

-----

## 2\. 개발 원칙 및 방법론

### 2.1. 설계 원칙

  * **단일 책임 원칙 (SRP)**: 모든 컴포넌트(작업자)는 하나의 명확한 책임을 갖는다.
  * **개방-폐쇄 원칙 (OCP)**: 기능 확장에 열려있고, 기존 코드 수정에는 닫혀있는 구조를 지향한다.
  * **의존성 역전 원칙 (DIP)**: 구체적인 구현이 아닌 추상화(인터페이스, 메시지)에 의존한다.

### 2.2. 개발 방법론

  * **테스트 주도 개발 (TDD)**: 각 컴포넌트 개발 시 단위/통합 테스트 코드를 먼저 작성하고, 이를 통과하는 코드를 구현한다.
  * **점진적 개발**: 핵심 인프라(Phase 0)부터 시작하여 작업자, 지휘자 순으로 점진적으로 개발하고 통합한다.

### 2.3. AI 협업 가이드 (PCIP 적용)

  * **계층적 작업 분해**: '단계별 개발 계획'을 상위 목표로, 각 단계의 세부 항목을 하위 목표로 설정하여 순차 개발한다.
  * **동적 전문가 리더십**: 각 컴포넌트 개발 시, 해당 분야의 전문가(예: `File Transfer` 개발 시 '네트워크 엔지니어') 역할을 부여하여 전문성을 높인다.
  * **상황인지 및 대화형 학습**: 본 명세서 전체를 개발의 유일한 진실 공급원(Single Source of Truth)으로 삼고, 모든 개발 내용은 이 문서에 기반한다.
  * **선제적 외부 지식 통합**: `paramiko`, `prometheus-client` 등 외부 라이브러리 사용 시, 최신 공식 문서와 모범 사례를 적극 참조한다.

-----

## 3\. 시스템 아키텍처 상세

### 3.1. 컴포넌트별 명세

#### **`Conductor` (지휘자)**

  * **역할**: 전체 워크플로우 오케스트레이션.
  * **책임**:
      * `Case Scanner`로부터 신규 케이스 수신 및 워크플로우 시작.
      * 작업 흐름에 따라 적절한 작업자에게 명령 메시지 발행.
      * 작업자로부터 상태/결과 메시지를 수신하여 전체 진행 상황 추적.
      * 오류 발생 시 재시도 및 복구 정책 적용.
      * 모든 케이스와 작업의 상태를 `State Manager`를 통해 영속적으로 관리.
  * **입력**: 모든 작업자로부터의 상태/결과 보고 메시지, `API Gateway`로부터의 사용자 명령.
  * **출력**: 각 작업자에게 전달할 구체적인 명령 메시지.
  * **의존성**: `Message Queue`, `State Manager`.

#### **`Case Scanner` (작업자)**

  * **역할**: 신규 데이터 스캔.
  * **책임**:
      * 지정된 로컬 디렉터리를 주기적으로 스캔.
      * 기존에 처리되지 않은 신규 케이스(디렉터리) 발견 시, 해당 정보를 담은 메시지를 메시지 큐로 발행.
  * **입력**: 없음 (자체 스케줄에 따라 동작).
  * **출력**: `new_case_found` 메시지 (Payload: `case_id`).
  * **의존성**: `Message Queue`, 로컬 파일 시스템.

#### **`File Transfer` (작업자)**

  * **역할**: 파일 업로드 및 다운로드.
  * **책임**:
      * `upload_case` 명령 수신 시, 지정된 케이스 파일을 원격지로 SFTP/SSH를 통해 전송.
      * `download_results` 명령 수신 시, 원격지의 결과 파일을 지정된 로컬 경로로 다운로드.
      * 전송 성공/실패 여부를 메시지로 발행.
  * **입력**: `upload_case`, `download_results` 명령 메시지.
  * **출력**: `upload_success`, `upload_failed`, `download_success`, `download_failed` 상태 메시지.
  * **의존성**: `Message Queue`, `SSHConnectionPool`.

#### **`Remote Executor` (작업자)**

  * **역할**: 원격 명령어 실행.
  * **책임**:
      * `execute_command` 명령 수신 시, SSH를 통해 원격지에서 주어진 명령어(예: `sbatch run_calc.sh`) 실행.
      * 명령 실행 시작, 성공, 실패 상태를 메시지로 발행.
  * **입력**: `execute_command` 명령 메시지.
  * **출력**: `execution_started`, `execution_success`, `execution_failed` 상태 메시지.
  * **의존성**: `Message Queue`, `SSHConnectionPool`.

#### **`System Curator` (작업자)**

  * **역할**: 시스템 상태 해석 및 정보 제공.
  * **책임**:
      * 로컬 및 원격 시스템의 리소스(GPU 사용률, 디스크 공간 등)를 주기적으로 모니터링.
      * 단순 데이터가 아닌, 해석된 정보(예: '신규 작업 할당 가능' 상태)를 메시지로 발행하여 `Conductor`의 결정을 도움.
  * **입력**: 없음 (자체 스케줄에 따라 동작).
  * **출력**: `system_status_update` 메시지 (Payload: `{ "gpu_available": true, ... }`).
  * **의존성**: `Message Queue`.

#### **지원 컴포넌트**

  * **`Logger`**: 모든 컴포넌트의 로그를 수집하는 중앙화된 로거. 구조화된 JSON 형식으로 로그를 출력하여 추적성을 높인다.
  * **`Process Manager`**: 모든 작업자 프로세스의 상태를 감시하고, 비정상(좀비) 프로세스를 자동 재시작하여 시스템 안정성을 보장한다.
  * **`Configuration Manager`**: YAML 기반의 중앙 설정 저장소에서 환경설정을 읽어와 각 컴포넌트에 제공한다.

### 3.2. 통신 프로토콜

  * **메시지 큐**: RabbitMQ 사용을 권장 (Topic 기반 라우팅 활용).
  * **메시지 포맷**: 모든 메시지는 아래 구조의 JSON 형식을 따른다.
    ```json
    {
      "command": "command_name",
      "payload": { "key": "value" },
      "timestamp": "2025-08-08T08:30:00Z",
      "correlation_id": "unique_id_for_workflow_trace"
    }
    ```

-----

## 4\. 공통 구현 가이드라인

### 4.1. 데이터 모델

  * **`CaseStatus` (Enum)**: `NEW`, `QUEUED`, `PROCESSING`, `COMPLETED`, `FAILED`
  * **`JobStatus` (Enum)**: `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`
  * `Case`, `Job` 등 핵심 데이터 클래스는 `dataclasses`를 사용하여 불변(immutable) 객체로 정의한다.

### 4.2. 에러 처리 및 안정성

  * **Custom Exceptions**: `MQIError`를 기반으로 `ConnectionError`, `ResourceError` 등 명확한 예외 계층을 사용한다.
  * **Retry Policy**: 네트워크 관련 작업 실패 시, Exponential Backoff 전략을 사용한 재시도 로직을 구현한다.
  * **Circuit Breaker**: 특정 서비스의 반복적인 실패가 시스템 전체에 영향을 주지 않도록 회로 차단기 패턴을 적용한다.

### 4.3. 상태 관리

  * **`ThreadSafeStateManager`**: `Conductor` 등 상태 정보가 중요한 컴포넌트에서는 스레드 안전 상태 관리자를 사용하여 데이터 무결성을 보장한다. 상태는 JSON 파일로 영속화한다.

-----

## 5\. 로깅 및 모니터링

### 5.1. 구조화된 로깅

모든 로그는 `correlation_id`를 포함한 JSON 형식으로 출력하여, 특정 워크플로우에 대한 모든 관련 로그를 쉽게 필터링할 수 있도록 한다.

```json
{
    "timestamp": "...", "level": "INFO", "module": "FileTransfer",
    "correlation_id": "case_123_abc", "message": "File upload successful"
}
```

### 5.2. 메트릭 수집

Prometheus를 사용하여 주요 지표를 수집하고 Grafana로 시각화한다.

  * `mqi_cases_total` (Counter): 처리된 케이스 총량
  * `mqi_active_workers` (Gauge): 현재 실행 중인 작업자 수
  * `mqi_processing_duration_seconds` (Histogram): 케이스 처리 시간 분포

-----

## 6\. 테스트 전략

  * **단위 테스트**: 각 작업자의 핵심 로직은 Mock 객체를 사용하여 외부 의존성 없이 테스트한다. (100% 커버리지 목표)
  * **통합 테스트**: `File Transfer`와 Mock SFTP 서버, `Remote Executor`와 Mock SSH 서버 등 외부 시스템과의 연동을 테스트한다.
  * **E2E 테스트**: `docker-compose`로 모든 컴포넌트를 실행한 뒤, 실제와 동일한 워크플로우(파일 생성 → 결과 다운로드)를 종단 간 테스트한다.

-----

## 7\. 환경설정 및 배포

### 7.1. 환경설정

  * **형식**: 사람이 읽고 수정하기 쉬우며 주석을 지원하는 **YAML**을 기본 형식으로 채택한다.
  * **관리**: `Configuration Manager`를 통해 중앙에서 모든 설정을 관리한다.

### 7.2. 배포

  * `Process Manager`를 통해 모든 작업자/지원 컴포넌트의 생명주기를 관리한다.
  * 각 컴포넌트는 독립적으로 배포 및 업데이트가 가능해야 한다.

-----

## 8\. 단계별 개발 계획

1.  **Phase 0: 핵심 기반 및 통신 체계 구축** (2일)
      * 공용 데이터 모델 및 메시지 포맷 정의
      * 메시지 큐(RabbitMQ) 설정 및 통신 테스트
2.  **Phase 1: 개별 '작업자' 프로그램 개발** (4일)
      * `Case Scanner`, `System Curator` 개발
      * `File Transfer`, `Remote Executor` 개발 및 단위/통합 테스트
3.  **Phase 2: 지원 컴포넌트 및 '지휘자' 개발** (4일)
      * `Logger`, `Process Manager`, `Configuration Manager` 개발
      * 핵심 워크플로우 로직을 갖춘 `Conductor` 개발
4.  **Phase 3: 시스템 통합 및 E2E 테스트** (3일)
      * `docker-compose`를 이용한 통합 테스트 환경 구축
      * 전체 워크플로우 및 예외 상황 E2E 테스트
5.  **Phase 4: 모니터링, 문서화 및 최종화** (2일)
      * 메트릭 수집 및 대시보드 구성
      * 최종 운영 매뉴얼 작성 및 코드 리뷰