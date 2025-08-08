import pytest
from unittest.mock import patch, MagicMock

# Target for testing
from mqi_communicator.domain.system_monitor import SystemMonitor
from mqi_communicator.domain.interfaces import DiskUsage, GPUStatus

class TestSystemMonitor:

    @pytest.fixture
    def monitor(self) -> SystemMonitor:
        return SystemMonitor()

    @patch('psutil.cpu_percent')
    def test_get_cpu_usage(self, mock_cpu_percent, monitor: SystemMonitor):
        # Given
        mock_cpu_percent.return_value = 42.5

        # When
        usage = monitor.get_cpu_usage()

        # Then
        assert usage == 42.5
        mock_cpu_percent.assert_called_once_with(interval=1)

    @patch('shutil.disk_usage')
    def test_get_disk_usage(self, mock_disk_usage, monitor: SystemMonitor):
        # Given
        # Mock values are in bytes
        total_bytes = 100 * (1024**3)
        used_bytes = 40 * (1024**3)
        free_bytes = 60 * (1024**3)
        mock_disk_usage.return_value = (total_bytes, used_bytes, free_bytes)

        # When
        usage = monitor.get_disk_usage(path="/fake/path")

        # Then
        assert isinstance(usage, DiskUsage)
        assert usage.total_gb == 100.0
        assert usage.used_gb == 40.0
        assert usage.free_gb == 60.0
        mock_disk_usage.assert_called_once_with("/fake/path")

    @patch('subprocess.run')
    def test_get_gpu_status_success(self, mock_subprocess_run, monitor: SystemMonitor):
        # Given
        # Mock the output of nvidia-smi
        nvidia_smi_output = (
            "0, 50.5, 4096\n"
            "1, 10.0, 8192\n"
        )
        mock_subprocess_run.return_value.stdout = nvidia_smi_output
        mock_subprocess_run.return_value.returncode = 0

        # When
        gpu_status = monitor.get_gpu_status()

        # Then
        assert len(gpu_status) == 2
        assert isinstance(gpu_status[0], GPUStatus)
        assert gpu_status[0].id == 0
        assert gpu_status[0].load == 50.5
        assert gpu_status[0].memory_usage == 4096.0
        assert gpu_status[1].id == 1

        expected_command = "nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv,noheader,nounits"
        mock_subprocess_run.assert_called_once_with(
            expected_command, shell=True, capture_output=True, text=True, check=True
        )

    @patch('subprocess.run')
    def test_get_gpu_status_command_fails(self, mock_subprocess_run, monitor: SystemMonitor):
        # Given
        # Mock a failed command execution
        mock_subprocess_run.side_effect = Exception("nvidia-smi not found")

        # When
        gpu_status = monitor.get_gpu_status()

        # Then
        # Should return an empty list if the command fails
        assert gpu_status == []
