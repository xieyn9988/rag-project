FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl libgomp1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV HF_HOME=/app/storage/hf_cache

RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

RUN pip install --timeout 600 "torch==2.5.1" --index-url https://download.pytorch.org/whl/cpu

RUN pip install --timeout 300 -e ".[dev]" -i https://pypi.tuna.tsinghua.edu.cn/simple

EXPOSE 8000

CMD ["uvicorn", "rag.api.app:app", "--host", "0.0.0.0", "--port", "8000"]