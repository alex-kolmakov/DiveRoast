FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Install dependencies
RUN uv pip install --system .

# Copy remaining files
COPY tests/ tests/

# Create default dlt config (secrets come from env vars at runtime)
RUN mkdir -p .dlt && printf '[runtime]\ndlthub_telemetry = true\n' > .dlt/config.toml

ENV PYTHONPATH="/app"

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
