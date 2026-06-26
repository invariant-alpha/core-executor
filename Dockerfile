FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install -e .[test]

COPY . .

CMD ["python", "-m", "core_executor.main"]
