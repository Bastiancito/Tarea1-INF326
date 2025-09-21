FROM python:3.11-slim

WORKDIR /app
COPY main.py /app/main.py
COPY requirements.txt /app/requirements.txt

RUN apt-get update \
	&& apt-get install -y --no-install-recommends wget \
	&& rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
