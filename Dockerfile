FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY src/ src/

EXPOSE 7373
ENTRYPOINT ["python", "-m", "src.server"]
