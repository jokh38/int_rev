import pytest
import time
from unittest.mock import Mock, patch

# Target for testing
from mqi_communicator.infrastructure.connection.retry_policy import RetryPolicy
from mqi_communicator.exceptions import MQIError # A generic error to catch

class TestRetryPolicy:
    @pytest.fixture
    def retry_policy(self):
        # A policy that retries 3 times with a small base delay
        return RetryPolicy(max_attempts=3, base_delay=0.01)

    def test_action_succeeds_on_first_try(self, retry_policy: RetryPolicy):
        # Given
        action = Mock(return_value="success")

        # When
        result = retry_policy.execute(action, "arg1", kwarg="kwarg1")

        # Then
        assert result == "success"
        action.assert_called_once_with("arg1", kwarg="kwarg1")

    def test_action_succeeds_after_retries(self, retry_policy: RetryPolicy):
        # Given
        # Action fails twice, then succeeds
        action = Mock(side_effect=[MQIError("Failed"), MQIError("Failed again"), "success"])

        # When
        with patch('time.sleep') as mock_sleep:
            result = retry_policy.execute(action)

        # Then
        assert result == "success"
        assert action.call_count == 3
        # Check that sleep was called with exponential backoff
        assert mock_sleep.call_count == 2
        # First delay: 0.01 * 2^0 = 0.01
        mock_sleep.assert_any_call(0.01)
        # Second delay: 0.01 * 2^1 = 0.02
        mock_sleep.assert_any_call(0.02)

    def test_action_fails_after_all_attempts(self, retry_policy: RetryPolicy):
        # Given
        # Action fails on all 3 attempts
        action = Mock(side_effect=MQIError("Permanent failure"))

        # When / Then
        with patch('time.sleep') as mock_sleep:
            with pytest.raises(MQIError, match="Permanent failure"):
                retry_policy.execute(action)

        assert action.call_count == 3
        assert mock_sleep.call_count == 2

    def test_retry_on_specific_exception(self):
        # Given
        class SpecificError(Exception): pass
        class OtherError(Exception): pass

        policy = RetryPolicy(max_attempts=3, retry_on=(SpecificError,))
        action = Mock(side_effect=[SpecificError("Failing"), "success"])

        # When
        result = policy.execute(action)

        # Then
        assert result == "success"
        assert action.call_count == 2

    def test_no_retry_on_unspecified_exception(self):
        # Given
        class SpecificError(Exception): pass
        class OtherError(Exception): pass

        policy = RetryPolicy(max_attempts=3, retry_on=(SpecificError,))
        action = Mock(side_effect=OtherError("This should not be retried"))

        # When / Then
        with pytest.raises(OtherError):
            policy.execute(action)

        assert action.call_count == 1
