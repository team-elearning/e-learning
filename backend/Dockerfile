# Sử dụng Python base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy file requirements trước để tận dụng cache
COPY requirements.txt .

# Cài dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ project vào container
COPY . .

# Expose port 8000 cho Django
EXPOSE 8000

# Biến môi trường cơ bản
ENV DJANGO_SETTINGS_MODULE=backend.settings
ENV PYTHONUNBUFFERED=1

# Command mặc định (production dùng gunicorn, dev có thể dùng runserver)
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000"]
