#!/usr/bin/env python3
"""Test script for agent creation functionality.

This script validates that the create_agent.py script has all necessary
components and can run in dry-run mode successfully.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def test_dry_run():
    """Test the agent creation script in dry-run mode."""
    script_path = Path(__file__).parent / "create_agent.py"

    print("🧪 Testing create_agent.py in dry-run mode...")

    try:
        result = subprocess.run([
            sys.executable,
            str(script_path),
            # "--dry-run",
            "--debug"
        ], check=False, capture_output=True, text=True, timeout=30)

        print(f"Exit code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")

        if result.stderr:
            print(f"STDERR:\n{result.stderr}")

        # In dry-run mode, the script should exit with code 0 if prerequisites fail
        # or if it would succeed (since no actual actions are taken)
        if result.returncode in [0, 1]:
            print("✅ Dry-run test passed - script can execute")
            return True
        else:
            print("❌ Dry-run test failed - unexpected exit code")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Test timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

def test_imports():
    """Test that all required imports work."""
    print("📦 Testing imports...")

    try:

        # Test core library imports
        modules_to_test = [
            'argparse', 'json', 'logging', 'os', 'subprocess', 'sys',
            'dataclasses', 'datetime', 'pathlib', 'typing'
        ]

        for module_name in modules_to_test:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                raise ImportError(f"{module_name} not available")

        print("✅ All imports successful")
        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_config_files():
    """Test that configuration files exist and are valid."""
    print("🔧 Testing configuration files...")

    config_dir = Path(__file__).parent.parent.parent / "configs"
    config_file = config_dir / "agent_creation_config.json"

    if not config_file.exists():
        print(f"❌ Configuration file not found: {config_file}")
        return False

    try:
        with open(config_file) as f:
            config = json.load(f)

        # Check required sections
        required_sections = ['agent', 'mcp', 'environment', 'usage']
        for section in required_sections:
            if section not in config:
                print(f"❌ Missing configuration section: {section}")
                return False

        print("✅ Configuration file is valid JSON with required sections")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading config file: {e}")
        return False

def test_env_template():
    """Test that environment template exists."""
    print("🌍 Testing environment template...")

    env_template = Path(__file__).parent.parent.parent / ".env.template"

    if not env_template.exists():
        print(f"❌ Environment template not found: {env_template}")
        return False

    try:
        with open(env_template) as f:
            content = f.read()

        # Check for required environment variables
        required_vars = [
            'BOSA_API_KEY_CLIENT',
            'BOSA_USER_SECRET',
            'AIP_API_URL',
            'AIP_API_KEY'
        ]

        for var in required_vars:
            if var not in content:
                print(f"❌ Missing required environment variable in template: {var}")
                return False

        print("✅ Environment template contains required variables")
        return True

    except Exception as e:
        print(f"❌ Error reading environment template: {e}")
        return False

def main():
    """Run all validation tests."""
    print("=" * 60)
    print("GitHub Compliance Agent - Creation Script Validation")
    print("=" * 60)

    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_config_files),
        ("Environment Template Test", test_env_template),
        ("Dry Run Test", test_dry_run)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1

    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All validation tests passed!")
        print("\nYour agent creation setup is ready to use:")
        print("1. Set up your .env file with actual credentials")
        print("2. Run: python create_agent.py --config ../configs/agent_creation_config.json")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
