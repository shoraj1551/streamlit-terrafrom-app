# Test Suite

This directory contains comprehensive tests for the Cloud Infrastructure Deployer.

## Test Structure

```
tests/
├── test_auth_system.py        - Authentication tests
├── test_ai_agent.py           - AI requirements agent tests
├── test_multi_cloud_analyzer.py - Multi-cloud analysis tests
├── test_integration.py        - End-to-end integration tests
└── run_tests.py              - Test runner
```

## Running Tests

### Run All Tests
```bash
python tests/run_tests.py
```

### Run Specific Test Suite
```bash
python -m unittest tests.test_auth_system
python -m unittest tests.test_ai_agent
python -m unittest tests.test_multi_cloud_analyzer
python -m unittest tests.test_integration
```

### Run Single Test
```bash
python -m unittest tests.test_auth_system.TestAuthenticationSystem.test_signup_success
```

## Test Coverage

### Authentication System (test_auth_system.py)
- ✅ User signup (success, duplicate, weak password)
- ✅ User login (success, wrong password, nonexistent user)
- ✅ JWT token generation and verification
- ✅ Password change functionality

### AI Requirements Agent (test_ai_agent.py)
- ✅ Rule-based extraction (basic, ML, healthcare, fintech, e-commerce)
- ✅ Default requirements structure
- ✅ Requirement validation

### Multi-Cloud Analyzer (test_multi_cloud_analyzer.py)
- ✅ Environment-specific cost calculation
- ✅ Cost score calculation
- ✅ All provider analysis
- ✅ Recommendation generation
- ✅ GCP cost advantage verification

### Integration Tests (test_integration.py)
- ✅ Complete user journey (signup → deployment)
- ✅ Service integration
- ✅ Data flow validation

## Expected Results

All tests should pass with 100% success rate:

```
Tests Run: 20+
Successes: 20+
Failures: 0
Errors: 0
```

## Adding New Tests

1. Create test file: `test_<component>.py`
2. Import unittest and component
3. Create test class inheriting from `unittest.TestCase`
4. Add test methods (must start with `test_`)
5. Run tests to verify

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Tests
  run: python tests/run_tests.py
```
