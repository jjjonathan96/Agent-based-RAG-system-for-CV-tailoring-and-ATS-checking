# Use a base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy your code into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt


EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]