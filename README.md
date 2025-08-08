# MQI Communicator

**Codename: MOQUI**

## 1. Overview

MQI Communicator is a Python-based system designed to automate the workflow of medical physics Quality Assurance (QA). It monitors a specified directory for new patient cases, transfers them to a remote High-Performance Computing (HPC) environment, orchestrates the execution of GPU-based calculations, and retrieves the results.

The system is built with a clean, layered architecture to ensure maintainability and testability. It features robust error handling with retries and circuit breakers, and provides observability through structured logging and Prometheus metrics.

## 2. Features

- **Automated Workflow:** Monitors for new cases and processes them end-to-end automatically.
- **Remote Execution:** Interfaces with remote HPC environments via SSH.
- **Resource Management:** Manages local and remote resources to prevent overloading.
- **Robustness:** Implements retry policies and circuit breakers for resilient network communication.
- **Observability:** Provides structured JSON logs and Prometheus metrics for monitoring.
- **Configurability:** All aspects of the application (paths, connection details, etc.) are configured via a single YAML file.

## 3. Getting Started

### 3.1. Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/) for dependency management.
- A remote HPC environment accessible via SSH with key-based authentication.
- `rsync` installed locally and on the remote host.

### 3.2. Configuration

1.  Copy the example configuration file `config.example.yaml` to `config.yaml`.
    ```bash
    cp config.example.yaml config.yaml
    ```
    *(Note: I will create `config.example.yaml` in a subsequent step).*

2.  Edit `config.yaml` with your specific environment details:
    - `paths`: Set the local and remote workspace paths.
    - `ssh`: Provide the connection details for your HPC host.
    - `resources`: Configure resource limits based on your hardware.

### 3.3. Running the Application

Once the configuration is complete, you can run the application using the deployment script:

```bash
# Make the script executable
chmod +x deploy.sh

# Run the application with the default config.yaml
./deploy.sh

# Or provide a custom config file path
./deploy.sh /path/to/your/config.yaml
```

## 4. Monitoring

The application exposes Prometheus metrics on port 8000 by default (configurable via `monitoring.metrics_port` in the config file).

Logs are printed to standard output in a structured JSON format.
