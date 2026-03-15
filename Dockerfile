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
