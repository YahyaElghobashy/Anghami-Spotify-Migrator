#!/bin/bash

# Convenience wrapper for the test runner
# Forwards all arguments to the actual test runner script

exec "$(dirname "$0")/tests/scripts/run_tests.sh" "$@" 