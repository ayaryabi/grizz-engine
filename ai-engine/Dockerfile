FROM python:3.13.3 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app


RUN python -m venv .venv
COPY requirements.txt ./
RUN .venv/bin/pip install -r requirements.txt

FROM python:3.13.3-slim
WORKDIR /app
COPY --from=builder /app/.venv .venv/
COPY . .

# Set environment variables for proper binding
ENV HOST="0.0.0.0" \
    PORT="8000" \
    PYTHONPATH="/app" \
    PATH="/app/.venv/bin:$PATH"

# Make scripts executable
RUN chmod +x /app/launcher.py /app/app/workers/llm_worker.py

# New CMD for debugging: run launcher, and if it exits, print web_server.log
CMD sh -c "/app/.venv/bin/python launcher.py --workers 2 ; echo 'Launcher exited. Contents of web_server.log:'; cat /app/logs/web_server.log || echo 'web_server.log not found or cat failed'"