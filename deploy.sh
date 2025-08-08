#!/bin/bash
set -e

# --- MQI Communicator Deployment Script ---

# Default configuration file path
CONFIG_FILE="config.yaml"

# Check if a custom config file is provided
if [ -n "$1" ]; then
    CONFIG_FILE="$1"
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Configuration file not found at '$CONFIG_FILE'"
    echo "Usage: $0 [path/to/your/config.yaml]"
    exit 1
fi

echo "--- Checking dependencies with Poetry ---"
# Check if poetry is installed
if ! command -v poetry &> /dev/null
then
    echo "Poetry could not be found. Please install it first."
    exit 1
fi

echo "--- Installing dependencies ---"
poetry install --no-dev --no-root

echo "--- Starting MQI Communicator ---"
# Run the main application, passing the config file path
poetry run python src/mqi_communicator/main.py --config "$CONFIG_FILE"

echo "--- MQI Communicator has exited ---"
