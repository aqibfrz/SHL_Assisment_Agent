FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (IMPORTANT for ML libs)
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7860

ENV PORT=7860

CMD ["python", "run_api.py"]