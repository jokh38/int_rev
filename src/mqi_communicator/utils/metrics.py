from prometheus_client import Counter, Gauge, Histogram

# --- Case Metrics ---
CASES_RECEIVED = Counter(
    'mqi_cases_received_total',
    'Total number of new cases detected'
)
CASES_COMPLETED = Counter(
    'mqi_cases_completed_total',
    'Total number of cases successfully processed'
)
CASES_FAILED = Counter(
    'mqi_cases_failed_total',
    'Total number of cases that failed during processing'
)

# --- Job & Task Metrics ---
JOBS_CREATED = Counter(
    'mqi_jobs_created_total',
    'Total number of jobs created'
)
ACTIVE_JOBS = Gauge(
    'mqi_active_jobs',
    'Number of jobs currently being processed'
)
TASK_EXECUTION_TIME = Histogram(
    'mqi_task_execution_duration_seconds',
    'Histogram of task execution times',
    buckets=('0.1', '0.5', '1', '5', '10', '30', '60', 'inf'),
    labelnames=('task_type',)
)

# --- System Metrics ---
CPU_USAGE = Gauge(
    'mqi_system_cpu_usage_percent',
    'Current system-wide CPU usage'
)
DISK_FREE_GB = Gauge(
    'mqi_system_disk_free_gb',
    'Free disk space in GB on the monitored partition',
    labelnames=('path',)
)
GPU_UTILIZATION = Gauge(
    'mqi_gpu_utilization_percent',
    'GPU utilization percentage',
    labelnames=('gpu_id',)
)
GPU_MEMORY_USAGE = Gauge(
    'mqi_gpu_memory_used_mb',
    'GPU memory used in MB',
    labelnames=('gpu_id',)
)

# --- Transfer Metrics ---
UPLOAD_SIZE_MB = Histogram(
    'mqi_upload_size_mb',
    'Histogram of upload sizes in megabytes'
)
DOWNLOAD_SIZE_MB = Histogram(
    'mqi_download_size_mb',
    'Histogram of download sizes in megabytes'
)
