FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8080

# Cloud Run sets $PORT. We default to 8080 for local docker run.
CMD ["sh", "-c", "python -m uvicorn platform_api.app:app --host 0.0.0.0 --port ${PORT:-8080}"]

# Mental Health Safety Tester — run personas against SUT and score with judge.
# Build: docker build -t mental-health-tester .
# Run:   docker run --env-file .env -v $(pwd)/results:/app/results mental-health-tester --persona passive_ideation.json --mock
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt pytest

# Copy app (personas, main, runner, judge, sut_backends, etc.)
COPY main.py runner.py judge.py sut_backends.py ./
COPY personas/ ./personas/
COPY mental_health_tester/ ./mental_health_tester/ 2>/dev/null || true
COPY pyproject.toml ./
COPY scripts/ ./scripts/ 2>/dev/null || true

# Optional: default results dir
ENV OUTPUT_DIR=/app/results
RUN mkdir -p /app/results

# Mount .env or pass ANTHROPIC_API_KEY etc. at run time.
# Example: docker run --env-file .env -v $(pwd)/results:/app/results mental-health-tester --persona passive_ideation.json
ENTRYPOINT ["python3", "main.py"]
CMD ["--help"]
