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
ENV HOST="0.0.0.0"
ENV PORT="8000"

# Run directly with uvicorn with correct module path
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]