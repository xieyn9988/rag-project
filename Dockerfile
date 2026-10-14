FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl libgomp1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV HF_HOME=/app/storage/hf_cache
ENV HF_ENDPOINT=https://hf-mirror.com

# 用官方源升级 pip
RUN pip install --upgrade pip -i https://pypi.org/simple

COPY . .

# torch 用阿里源 + PyTorch 源
RUN pip install --timeout 600 torch \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -i https://mirrors.aliyun.com/pypi/simple

# 项目用阿里源
RUN pip install --timeout 300 -e "." -i https://mirrors.aliyun.com/pypi/simple

EXPOSE 8000

CMD ["uvicorn", "rag.api.app:app", "--host", "0.0.0.0", "--port", "8000"]