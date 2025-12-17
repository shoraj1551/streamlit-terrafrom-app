"""
Automated Test Runner Script

Runs all tests (unit, integration, E2E) with comprehensive reporting.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py --unit       # Run unit tests only
    python run_tests.py --integration # Run integration tests only
    python run_tests.py --e2e        # Run E2E tests only
    python run_tests.py --coverage   # Run with coverage report
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


class TestRunner:
    """Automated test runner with reporting"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.tests_dir = self.project_root / "tests"
        self.results_dir = self.project_root / "test_results"
        self.results_dir.mkdir(exist_ok=True)
    
    def run_tests(
        self,
        test_type="all",
        coverage=False,
        verbose=True,
        fail_fast=False,
    ):
        """
        Run tests with specified options
        
        Args:
            test_type: Type of tests to run (all, unit, integration, e2e)
            coverage: Whether to generate coverage report
            verbose: Verbose output
            fail_fast: Stop on first failure
        """
        print("=" * 80)
        print("🧪 TERRAFORM-STREAMLIT AUTOMATED TEST SUITE")
        print("=" * 80)
        print(f"Test Type: {test_type.upper()}")
        print(f"Coverage: {'Enabled' if coverage else 'Disabled'}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
        
        # Build pytest command
        cmd = ["pytest"]
        
        # Add test directory based on type
        if test_type == "unit":
            cmd.append(str(self.tests_dir / "unit"))
        elif test_type == "integration":
            cmd.append(str(self.tests_dir / "integration"))
        elif test_type == "e2e":
            cmd.append(str(self.tests_dir / "e2e"))
        else:
            cmd.append(str(self.tests_dir))
        
        # Add options
        if verbose:
            cmd.append("-v")
        
        if fail_fast:
            cmd.append("-x")
        
        # Add coverage
        if coverage:
            cmd.extend([
                "--cov=app",
                "--cov-report=html",
                "--cov-report=term",
                f"--cov-report=html:{self.results_dir}/coverage",
            ])
        
        # Add output options
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        junit_file = self.results_dir / f"junit_{test_type}_{timestamp}.xml"
        html_file = self.results_dir / f"report_{test_type}_{timestamp}.html"
        
        cmd.extend([
            f"--junitxml={junit_file}",
            f"--html={html_file}",
            "--self-contained-html",
        ])
        
        # Run tests
        print(f"Running command: {' '.join(cmd)}")
        print()
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            
            print()
            print("=" * 80)
            
            if result.returncode == 0:
                print("✅ ALL TESTS PASSED!")
            else:
                print("❌ SOME TESTS FAILED")
            
            print("=" * 80)
            print()
            print("📊 Test Reports:")
            print(f"  - JUnit XML: {junit_file}")
            print(f"  - HTML Report: {html_file}")
            
            if coverage:
                print(f"  - Coverage Report: {self.results_dir}/coverage/index.html")
            
            print()
            
            return result.returncode
            
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return 1
    
    def run_quick_check(self):
        """Run quick smoke tests"""
        print("🚀 Running Quick Smoke Tests...")
        print()
        
        # Run only fast unit tests
        cmd = [
            "pytest",
            str(self.tests_dir / "unit"),
            "-v",
            "-m", "not slow",
            "--tb=short",
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root)
        
        if result.returncode == 0:
            print("\n✅ Quick check passed!")
        else:
            print("\n❌ Quick check failed!")
        
        return result.returncode
    
    def run_security_tests(self):
        """Run security-focused tests"""
        print("🔒 Running Security Tests...")
        print()
        
        # Run tests marked as security
        cmd = [
            "pytest",
            str(self.tests_dir),
            "-v",
            "-k", "security or auth or encryption or sanitize",
            "--tb=short",
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root)
        
        if result.returncode == 0:
            print("\n✅ Security tests passed!")
        else:
            print("\n❌ Security tests failed!")
        
        return result.returncode
    
    def generate_summary(self):
        """Generate test summary"""
        print("📈 Generating Test Summary...")
        print()
        
        # Count test files
        unit_tests = list((self.tests_dir / "unit").glob("test_*.py"))
        integration_tests = list((self.tests_dir / "integration").glob("test_*.py"))
        e2e_tests = list((self.tests_dir / "e2e").glob("test_*.py"))
        
        print(f"Unit Tests: {len(unit_tests)} files")
        print(f"Integration Tests: {len(integration_tests)} files")
        print(f"E2E Tests: {len(e2e_tests)} files")
        print(f"Total: {len(unit_tests) + len(integration_tests) + len(e2e_tests)} test files")
        print()


def main():
    parser = argparse.ArgumentParser(description="Run Terraform-Streamlit tests")
    
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run unit tests only",
    )
    
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests only",
    )
    
    parser.add_argument(
        "--e2e",
        action="store_true",
        help="Run E2E tests only",
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report",
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick smoke tests",
    )
    
    parser.add_argument(
        "--security",
        action="store_true",
        help="Run security tests only",
    )
    
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failure",
    )
    
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show test summary",
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Show summary if requested
    if args.summary:
        runner.generate_summary()
        return 0
    
    # Run quick check
    if args.quick:
        return runner.run_quick_check()
    
    # Run security tests
    if args.security:
        return runner.run_security_tests()
    
    # Determine test type
    if args.unit:
        test_type = "unit"
    elif args.integration:
        test_type = "integration"
    elif args.e2e:
        test_type = "e2e"
    else:
        test_type = "all"
    
    # Run tests
    return runner.run_tests(
        test_type=test_type,
        coverage=args.coverage,
        fail_fast=args.fail_fast,
    )


if __name__ == "__main__":
    sys.exit(main())
