FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements-lock.txt .

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements-lock.txt

COPY . .

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import os,sys,urllib.request; req=urllib.request.Request('http://127.0.0.1:8787/health', headers={'Authorization': f\"Bearer {os.getenv('AGENT_HUB_API_KEY','')}\"}); resp=urllib.request.urlopen(req, timeout=3); sys.exit(0 if resp.status == 200 else 1)"

CMD ["python", "scripts/agent_hub.py", "serve", "--host", "0.0.0.0", "--port", "8787"]
