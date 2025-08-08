import pytest
import time
from unittest.mock import patch

# Target for testing
from mqi_communicator.infrastructure.connection.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

class TestCircuitBreaker:
    @pytest.fixture
    def breaker(self):
        # 3 failures to open, 5 second timeout
        return CircuitBreaker(failure_threshold=3, timeout=5)

    def test_circuit_closed_allows_calls(self, breaker: CircuitBreaker):
        # Given
        action = lambda: "success"

        # When
        result = breaker.call(action)

        # Then
        assert result == "success"
        assert not breaker.is_open()

    def test_circuit_opens_after_threshold_failures(self, breaker: CircuitBreaker):
        # Given
        action = lambda: exec("raise ValueError('action failed')")

        # When / Then
        # First 3 calls should fail and increment failure count
        for _ in range(3):
            with pytest.raises(ValueError, match="action failed"):
                breaker.call(action)

        # The 4th call should fail immediately with CircuitBreakerOpenError
        assert breaker.is_open()
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(action)

    def test_circuit_half_open_after_timeout(self, breaker: CircuitBreaker):
        # Given
        # Trip the breaker
        for _ in range(3):
            with pytest.raises(Exception):
                breaker.call(lambda: exec("raise ValueError()"))
        assert breaker.is_open()

        # When
        # Simulate time passing beyond the timeout
        with patch('time.time', return_value=time.time() + breaker.timeout + 1):
            # Then
            # The breaker should now be half-open. It allows one call.
            # We can't directly check the "half-open" state, but we can infer it.
            # A successful call should close it.
            result = breaker.call(lambda: "success")
            assert result == "success"
            assert not breaker.is_open()

    def test_circuit_reopens_on_failure_in_half_open_state(self, breaker: CircuitBreaker):
        # Given
        # Trip the breaker
        for _ in range(3):
            with pytest.raises(Exception):
                breaker.call(lambda: exec("raise ValueError()"))
        assert breaker.is_open()

        # When
        # Simulate time passing to enter half-open state
        with patch('time.time') as mock_time:
            mock_time.return_value = time.time() + breaker.timeout + 1

            # A failing call in half-open state should re-open the circuit
            with pytest.raises(ValueError, match="failed in half-open"):
                breaker.call(lambda: exec("raise ValueError('failed in half-open')"))

        # Then
        assert breaker.is_open()
        # It should not have reset the failure count, but the last_failure_time should be updated
        # This is an implementation detail we can check if needed.

    def test_circuit_closes_on_success_in_half_open_state(self, breaker: CircuitBreaker):
        # Given
        # Trip the breaker
        for _ in range(3):
            with pytest.raises(Exception):
                breaker.call(lambda: exec("raise ValueError()"))
        assert breaker.is_open()

        # When
        # Simulate time passing to enter half-open state
        with patch('time.time', return_value=time.time() + breaker.timeout + 1):
            # A successful call should close the circuit
            breaker.call(lambda: "success")

        # Then
        assert not breaker.is_open()
        assert breaker.failures == 0
