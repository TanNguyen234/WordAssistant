import pytest

from wordassistant.backends.word_native.backend import WordNativeBackend


def test_live_native_backend_health_when_available():
    backend = WordNativeBackend()
    health = backend.health()
    if not health.operational:
        pytest.skip(f"Word native unavailable: {health.reason}")
    assert health.backend == "word-native"

