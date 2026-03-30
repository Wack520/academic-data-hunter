FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir "pydantic>=2.8,<3.0"

COPY . .

EXPOSE 8787

CMD ["python", "scripts/agent_hub.py", "serve", "--host", "0.0.0.0", "--port", "8787"]
