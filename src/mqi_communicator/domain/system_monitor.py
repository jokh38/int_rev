from typing import List
import psutil
import shutil
import subprocess

from .interfaces import ISystemMonitor, GPUStatus, DiskUsage

class SystemMonitor(ISystemMonitor):
    """
    Monitors system resources like CPU, GPU, and disk.
    """

    def get_cpu_usage(self) -> float:
        """Returns the system-wide CPU utilization as a percentage."""
        return psutil.cpu_percent(interval=1)

    def get_disk_usage(self, path: str) -> DiskUsage:
        """Returns the disk usage for the partition of the given path."""
        total, used, free = shutil.disk_usage(path)
        return DiskUsage(
            total_gb=total / (1024**3),
            used_gb=used / (1024**3),
            free_gb=free / (1024**3)
        )

    def get_gpu_status(self) -> List[GPUStatus]:
        """
        Returns the status of all available NVIDIA GPUs by calling nvidia-smi.
        Returns an empty list if nvidia-smi is not found or fails.
        """
        command = "nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv,noheader,nounits"
        statuses = []
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout.strip()
            for line in output.splitlines():
                parts = line.split(', ')
                if len(parts) == 3:
                    statuses.append(GPUStatus(
                        id=int(parts[0]),
                        load=float(parts[1]),
                        memory_usage=float(parts[2])
                    ))
            return statuses
        except (subprocess.CalledProcessError, FileNotFoundError, Exception):
            # If the command fails (e.g., nvidia-smi not installed),
            # return an empty list.
            return []
