FROM python:3.9-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Copy file requirements trước để tận dụng Docker cache
# (Giúp build lại nhanh hơn nếu code thay đổi nhưng thư viện không đổi)
COPY requirements.txt .

# Cài đặt các thư viện phụ thuộc
# --no-cache-dir giúp giảm kích thước image
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn dự án vào container
COPY . .

# Mở port 8501
EXPOSE 8501

# Lệnh chạy ứng dụng khi container khởi động
# Quan trọng: server.address=0.0.0.0 để truy cập được từ bên ngoài container
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]