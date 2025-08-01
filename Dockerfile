FROM python:3.12-slim

WORKDIR /app

# Cài đặt libGL cần cho OpenCV
RUN apt-get update && apt-get install -y libgl1-mesa-glx

# Cài đặt các package Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY . .

# Chạy Gunicorn cho Flask app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080"]
