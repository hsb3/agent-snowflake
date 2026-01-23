#!/usr/bin/env python3
"""
Interactive setup script for local Snowflake testing.
Helps you choose and configure the best testing option for your needs.
"""

import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_section(text):
    """Print a formatted section."""
    print(f"\n{text}")
    print("-" * len(text))


def check_docker():
    """Check if Docker is available and running."""
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_package(package_name):
    """Check if a Python package is installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


def main():
    """Main interactive setup."""
    print_header("Snowflake Local Testing Setup")

    print("This script will help you set up local Snowflake testing.")
    print("You'll be able to test your Snowflake agent without cloud credentials.")

    # Check environment
    print_section("Checking environment...")

    docker_available = check_docker()
    fakesnow_installed = check_package("fakesnow")

    print(f"Docker available: {'✓ Yes' if docker_available else '✗ No'}")
    print(f"fakesnow installed: {'✓ Yes' if fakesnow_installed else '✗ No'}")

    # Present options
    print_section("Available Testing Options")

    print("\n1. fakesnow (Recommended)")
    print("   - Pure Python solution")
    print("   - No Docker required")
    print("   - Very fast")
    print("   - Perfect for unit tests and CI/CD")
    print("   - ~95% Snowflake compatibility")

    print("\n2. snowflake-emulator (Docker)")
    print("   - Runs in Docker container")
    print("   - Persistent storage")
    print("   - Good for integration tests")
    print("   - ~85% Snowflake compatibility")
    if not docker_available:
        print("   ⚠ Docker not detected - you'll need to install it first")

    print("\n3. Snowflake Trial")
    print("   - Real Snowflake instance")
    print("   - $400 free credits")
    print("   - 100% compatibility")
    print("   - Requires account signup")

    print("\n4. View documentation only")

    # Get user choice
    print_section("Make your choice")

    while True:
        try:
            choice = input("\nSelect option (1-4): ").strip()
            if choice in ["1", "2", "3", "4"]:
                break
            print("Please enter 1, 2, 3, or 4")
        except KeyboardInterrupt:
            print("\n\nSetup cancelled.")
            return 1

    # Handle choice
    if choice == "1":
        setup_fakesnow(fakesnow_installed)
    elif choice == "2":
        setup_docker(docker_available)
    elif choice == "3":
        setup_trial()
    elif choice == "4":
        show_documentation()

    return 0


def setup_fakesnow(already_installed):
    """Set up fakesnow."""
    print_header("Setting up fakesnow")

    if already_installed:
        print("✓ fakesnow is already installed!")
    else:
        print("Installing fakesnow...")
        print("\nRun this command:")
        print("  uv add fakesnow")
        print("\nWould you like to install it now? (y/n): ", end="")

        try:
            response = input().strip().lower()
            if response == "y":
                print("\nInstalling...")
                result = subprocess.run(
                    ["uv", "add", "fakesnow"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print("✓ fakesnow installed successfully!")
                else:
                    print(f"✗ Installation failed: {result.stderr}")
                    print("\nPlease run manually: uv add fakesnow")
            else:
                print("\nPlease install manually: uv add fakesnow")
        except KeyboardInterrupt:
            print("\n\nInstallation skipped.")

    # Show next steps
    print_section("Next Steps")
    print("\n1. Run the test script:")
    print("   uv run python test_fakesnow.py")
    print("\n2. Read the documentation:")
    print("   TESTING_FAKESNOW.md")
    print("\n3. Example usage:")
    print("""
   import fakesnow
   import snowflake.connector

   with fakesnow.patch():
       conn = snowflake.connector.connect()
       cursor = conn.cursor()
       cursor.execute("SELECT 'Hello!' as message")
       print(cursor.fetchone())
    """)


def setup_docker(docker_available):
    """Set up Docker emulator."""
    print_header("Setting up Docker Emulator")

    if not docker_available:
        print("⚠ Docker is not available or not running.")
        print("\nTo use the Docker emulator, you need to:")
        print("1. Install Docker Desktop from: https://www.docker.com/products/docker-desktop")
        print("2. Start Docker Desktop")
        print("3. Run this setup script again")
        return

    print("Docker is available!")
    print("\nTo start the emulator:")
    print("  docker-compose up -d")
    print("\nWould you like to start it now? (y/n): ", end="")

    try:
        response = input().strip().lower()
        if response == "y":
            print("\nStarting emulator...")
            result = subprocess.run(
                ["docker-compose", "up", "-d"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✓ Emulator started successfully!")
                print("\nRunning test script...")
                subprocess.run(["python", "test_emulator.py"])
            else:
                print(f"✗ Failed to start: {result.stderr}")
        else:
            print("\nYou can start it manually later: docker-compose up -d")
    except KeyboardInterrupt:
        print("\n\nStartup skipped.")

    # Show next steps
    print_section("Next Steps")
    print("\n1. Test the connection:")
    print("   uv run python test_emulator.py")
    print("\n2. Read the documentation:")
    print("   TESTING.md")
    print("\n3. Useful commands:")
    print("   docker-compose up -d     # Start")
    print("   docker-compose stop      # Stop (keeps data)")
    print("   docker-compose down -v   # Stop and remove data")


def setup_trial():
    """Set up Snowflake trial."""
    print_header("Snowflake Trial Setup")

    print("To use a real Snowflake trial account:")
    print("\n1. Sign up at: https://signup.snowflake.com/")
    print("2. Select your cloud provider and region")
    print("3. You'll get $400 in free credits")
    print("4. Trial lasts 30 days")

    print("\nAfter signing up:")
    print("1. Copy your account identifier")
    print("2. Create .env file from .env.example")
    print("3. Fill in your Snowflake credentials")

    print("\nSample datasets are available in:")
    print("  SNOWFLAKE_SAMPLE_DATA.TPCH_SF1")
    print("  SNOWFLAKE_SAMPLE_DATA.TPCH_SF10")
    print("  SNOWFLAKE_SAMPLE_DATA.TPCH_SF100")

    print_section("Documentation")
    print("\nSee README_TESTING.md for detailed setup instructions.")


def show_documentation():
    """Show documentation links."""
    print_header("Documentation")

    docs = [
        ("README_TESTING.md", "Main testing guide (all options)"),
        ("TESTING_FAKESNOW.md", "fakesnow detailed documentation"),
        ("TESTING.md", "Docker emulator detailed documentation"),
        ("LOCAL_TESTING_SUMMARY.md", "Implementation summary"),
    ]

    print("Available documentation:\n")
    for filename, description in docs:
        path = Path(filename)
        exists = "✓" if path.exists() else "✗"
        print(f"{exists} {filename}")
        print(f"  {description}\n")

    print("\nYou can read these files in your text editor or IDE.")
    print("\nQuick links:")
    print("- fakesnow: https://github.com/tekumara/fakesnow")
    print("- snowflake-emulator: https://github.com/nnnkkk7/snowflake-emulator")
    print("- Snowflake docs: https://docs.snowflake.com/")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(1)
