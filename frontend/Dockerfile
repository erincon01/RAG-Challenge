FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app/app_refactored.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
