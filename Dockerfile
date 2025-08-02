FROM python:3.12-slim

WORKDIR /app

# Cài đặt libGL cần cho OpenCV
# Cài các thư viện hệ thống cần thiết (zbar)
RUN apt-get update && apt-get install -y \
    libzbar0 \
    libglib2.0-0 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Tạo thư mục app
WORKDIR /app

# Copy toàn bộ project
COPY . .

# Cài thư viện Python
RUN pip install --no-cache-dir -r requirements.txt
RUN ls -l /opt/render/project/src/
RUN ls /opt/render/project/src/gmail_security_setup_optimized.py

# Start bằng gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]
