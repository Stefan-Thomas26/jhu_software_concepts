FROM python:3.11-slim
WORKDIR /app
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY worker/ .
COPY db/ /app/db/
COPY shared/ /app/shared/
USER 1000
CMD ["python", "consumer.py"]