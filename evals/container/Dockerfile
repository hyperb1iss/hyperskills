FROM node:22-bookworm-slim
ARG CLAUDE_VERSION
RUN test -n "$CLAUDE_VERSION" \
    && apt-get update \
    && apt-get install -y --no-install-recommends python3 git ca-certificates \
    && npm install --global "@anthropic-ai/claude-code@$CLAUDE_VERSION" \
    && apt-get clean \
    && rm -r /var/lib/apt/lists/*
WORKDIR /workspace
