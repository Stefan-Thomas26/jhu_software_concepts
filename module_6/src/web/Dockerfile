FROM python:3.11-slim
WORKDIR /app
COPY web/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY web/ .
COPY db/ /app/db/
COPY shared/ /app/shared/
EXPOSE 8080
USER 1000
CMD ["python", "run.py"]