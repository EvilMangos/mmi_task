# Run Tests

Run the test suite using pytest.

## Instructions

1. If a path argument is provided (`$ARGUMENTS`), run tests for that specific path
2. If no argument is provided, run all tests from the repository root
3. Use verbose output (`-v`) for better visibility
4. Report the results clearly

## Execution

```bash
# If argument provided, run tests for that path; otherwise run all tests
pytest -v ${ARGUMENTS:-.}
```

Run the above command and report the results. If tests fail, summarize the failures.