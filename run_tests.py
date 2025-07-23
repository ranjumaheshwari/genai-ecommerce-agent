#!/usr/bin/env python3
"""
Test runner script for the GenAI E-commerce Agent
"""
import subprocess
import sys
import os
from pathlib import Path

def install_test_dependencies():
    """Install test dependencies"""
    print("📦 Installing test dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "pytest==7.4.3", 
            "pytest-asyncio==0.21.1", 
            "pytest-cov==4.1.0", 
            "httpx==0.25.2"
        ], check=True)
        print("✅ Test dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install test dependencies: {e}")
        return False

def run_tests(coverage=True, verbose=True):
    """Run the test suite"""
    print("🧪 Running test suite...")
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=70"
        ])
    
    cmd.extend([
        "tests/",
        "--tb=short",
        "--color=yes"
    ])
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False

def run_specific_test(test_file=None, test_function=None):
    """Run a specific test file or function"""
    cmd = [sys.executable, "-m", "pytest", "-v"]
    
    if test_file:
        if test_function:
            cmd.append(f"tests/{test_file}::{test_function}")
        else:
            cmd.append(f"tests/{test_file}")
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Main test runner"""
    print("🚀 GenAI E-commerce Agent Test Runner")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Install dependencies if needed
    try:
        import pytest
        print("✅ Test dependencies already installed")
    except ImportError:
        if not install_test_dependencies():
            sys.exit(1)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--install-deps":
            install_test_dependencies()
            return
        elif sys.argv[1] == "--no-coverage":
            success = run_tests(coverage=False)
        elif sys.argv[1].startswith("--file="):
            test_file = sys.argv[1].split("=")[1]
            success = run_specific_test(test_file)
        elif sys.argv[1] == "--help":
            print("""
Usage: python run_tests.py [options]

Options:
  --install-deps    Install test dependencies only
  --no-coverage     Run tests without coverage report
  --file=<name>     Run specific test file (e.g., --file=test_config.py)
  --help           Show this help message

Examples:
  python run_tests.py                    # Run all tests with coverage
  python run_tests.py --no-coverage      # Run tests without coverage
  python run_tests.py --file=test_config.py  # Run specific test file
            """)
            return
        else:
            print(f"❌ Unknown option: {sys.argv[1]}")
            print("Use --help for usage information")
            sys.exit(1)
    else:
        # Run all tests with coverage
        success = run_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        if Path("htmlcov").exists():
            print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
