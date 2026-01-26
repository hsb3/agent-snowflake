"""Pytest configuration and shared fixtures for testing."""



def pytest_addoption(parser):
    """Add custom pytest options."""
    parser.addoption(
        "--emulator",
        action="store_true",
        default=False,
        help="Run tests against Docker emulator (requires docker-compose up)",
    )
