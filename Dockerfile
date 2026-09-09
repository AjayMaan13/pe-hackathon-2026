FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
COPY uv.lock* .

RUN uv sync --no-dev

COPY . .

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "run_fastapi:app", "--host", "0.0.0.0", "--port", "8080"]
