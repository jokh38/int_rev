# MQI Communicator Operations Manual

## 1. Introduction

This document provides detailed operational information for system administrators and operators responsible for running and monitoring the MQI Communicator application.

## 2. System Architecture

The application is composed of several layers:

-   **Application Layer:** The main entry point and lifecycle management.
-   **Domain Layer:** High-level orchestration logic (`WorkflowOrchestrator`, `TaskScheduler`).
-   **Service Layer:** Core business logic for managing cases, jobs, resources, and transfers.
-   **Infrastructure Layer:** Components for interacting with external systems (state management, SSH, command execution).

## 3. Monitoring and Observability

### 3.1. Structured Logging

The application outputs structured JSON logs to standard output. Each log entry contains detailed context, including a timestamp, log level, message, and the module/function where the log originated.

**Example Log Entry:**
```json
{
    "timestamp": "2025-01-01T12:00:00Z",
    "level": "INFO",
    "message": "Found 3 new cases to process",
    "logger_name": "root",
    "module": "workflow_orchestrator",
    "funcName": "_main_loop",
    "lineno": 70
}
```

It is recommended to forward these logs to a centralized logging platform (e.g., ELK Stack, Splunk, Graylog) for analysis and alerting.

### 3.2. Prometheus Metrics

The application exposes key performance indicators via a Prometheus endpoint.

-   **Endpoint:** `http://<host>:8000/` (port is configurable)
-   **Key Metrics:**
    -   `mqi_cases_received_total`: Total number of new cases detected.
    -   `mqi_cases_completed_total`: Counter for successfully processed cases.
    -   `mqi_cases_failed_total`: Counter for failed cases.
    -   `mqi_active_jobs`: A gauge showing the number of jobs currently in progress.
    -   `mqi_task_execution_duration_seconds`: A histogram of execution times for different task types.
    -   `mqi_gpu_utilization_percent`: Utilization for each GPU.

These metrics should be scraped by a Prometheus server and can be used to build dashboards (e.g., in Grafana) to monitor the health and performance of the application.

## 4. Error Conditions and Recovery

### 4.1. State File Corruption

-   **Symptom:** The application fails to start, with errors related to JSON parsing in the logs.
-   **Cause:** The `state.json` file has been corrupted due to an ungraceful shutdown or manual edit.
-   **Recovery:**
    1.  Stop the application.
    2.  Delete the corrupted `state.json` file.
    3.  Restart the application. It will create a new, empty state file and will re-process all cases found in the `local_logdata` directory.

### 4.2. Stale PID File

-   **Symptom:** The application refuses to start, claiming another instance is already running, but no other process exists.
-   **Cause:** The application terminated ungracefully without deleting its PID file.
-   **Recovery:**
    -   The application will automatically detect that the PID in the file is stale and will remove the file on the next startup. Manual intervention is typically not required.

### 4.3. Remote Connection Failure

-   **Symptom:** Logs contain errors related to SSH connection timeouts or failures.
-   **Cause:** Network issues between the application host and the HPC, or incorrect SSH configuration.
-   **Recovery:**
    1.  Verify network connectivity to the HPC.
    2.  Check the `ssh` section of the `config.yaml` file for correctness.
    3.  The application's built-in retry policy will attempt to recover from transient network failures automatically. If the issue is persistent, manual intervention is required.
