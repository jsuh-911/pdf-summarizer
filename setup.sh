#!/bin/bash

# Pure Python setup script - no conda dependencies

echo "Setting up PDF Summarizer with pure Python/PyPI..."

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies from PyPI..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Ollama if not present
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install ollama
        else
            echo "Please install Ollama from https://ollama.ai"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -fsSL https://ollama.ai/install.sh | sh
    else
        echo "Please install Ollama from https://ollama.ai"
        exit 1
    fi
fi

# Start Ollama if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama..."
    ollama serve &
    sleep 3
fi

# Pull model
echo "Pulling Mistral model..."
ollama pull mistral:latest

# Create output directory
mkdir -p summaries

echo "Setup complete! To use:"
echo "1. Activate environment: source venv/bin/activate"
echo "2. Run: python main.py setup"
echo "3. Process PDFs: python main.py process your-file.pdf"