# Agent and grader image for replayed fix commits. The build context is the
# Python subset of the target repository at the dependency base commit,
# materialized under tree/ by build.py.
FROM ghcr.io/astral-sh/uv:latest AS uv
FROM node:22-bookworm-slim
ARG CLAUDE_VERSION
ENV UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1
COPY --from=uv /uv /usr/local/bin/uv
RUN test -n "$CLAUDE_VERSION" \
    && apt-get update \
    && apt-get install -y --no-install-recommends python3 git ca-certificates \
    && npm install --global "@anthropic-ai/claude-code@$CLAUDE_VERSION" \
    && apt-get clean \
    && rm -r /var/lib/apt/lists/*
COPY tree /workspace
WORKDIR /workspace
# Workspace members install editable, so their import paths stay under
# /workspace and resolve to whichever trial tree is mounted there.
RUN uv sync --frozen --all-packages --no-cache \
    && find /workspace -mindepth 1 -delete
ENV PATH=/opt/venv/bin:$PATH
