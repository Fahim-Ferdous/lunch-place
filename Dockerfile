FROM python:3.11-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY *.py .

# For running locally
COPY .env .

EXPOSE 8000/tcp
CMD uvicorn main:app --host=0.0.0.0
