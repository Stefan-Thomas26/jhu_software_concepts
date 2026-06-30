FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY worker/ .
COPY db/ /app/db/
COPY shared/ /app/shared/

RUN python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF', filename='tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf', local_dir='models')"

RUN mkdir -p /home/worker && chown -R 1000:1000 /home/worker /app
ENV HOME=/home/worker
USER 1000
CMD ["python", "consumer.py"]