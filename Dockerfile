# Dockerfile for Strange Worlds Taxonomy Experiment
# Provides an isolated environment for running agentic experiments safely

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    tmux \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for Claude Code CLI)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Set working directory
WORKDIR /experiment

# Copy requirements first (for better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the experiment code
COPY . .

# Create directories for outputs (will be overwritten by volume mounts)
RUN mkdir -p taxonomy agents/logs

# Default command - can be overridden
CMD ["bash"]
