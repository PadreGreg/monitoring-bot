#!/bin/bash

# Create __init__.py files for proper Python package structure
touch /home/ubuntu/monitoring-bot/src/__init__.py

# Check Python syntax for all Python files
echo "Checking Python syntax..."
for file in /home/ubuntu/monitoring-bot/src/*.py; do
    echo "Checking $file"
    python3 -m py_compile "$file"
    if [ $? -ne 0 ]; then
        echo "Syntax error in $file"
        exit 1
    fi
done

echo "All Python files passed syntax check."

# Verify project structure
echo "Verifying project structure..."
ls -la /home/ubuntu/monitoring-bot/
ls -la /home/ubuntu/monitoring-bot/src/

echo "Validation complete. Project structure looks good."
