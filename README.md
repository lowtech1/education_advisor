# Hệ Thống Tư Vấn Học Tập & Sắp Xếp Lộ Trình (Thesis Project)

Đồ án tốt nghiệp xây dựng cơ sở tri thức hỗ trợ sinh viên lên kế hoạch học tập, gợi ý môn học dựa trên điều kiện tiên quyết và kết quả học tập quá khứ.

## 1. Tính năng chính
- Gợi ý môn học cho kỳ tiếp theo dựa trên đồ thị tiên quyết (DAG).
- Xử lý tình huống rớt môn và học cải thiện, học vượt.
- Giao diện trực quan hóa lộ trình học tập.

## 2. Công nghệ sử dụng
- **Ngôn ngữ:** Python 3.9
- **Giao diện:** Streamlit
- **Logic:** NetworkX (Graph Theory)
- **Deployment:** Docker

## 3. Cài đặt và Chạy thử

### Cách 1: Chạy bằng Docker (Khuyên dùng)
```bash
docker-compose up --build
```
## 4. Cấu trúc thư mục
```bash
education_advisor/
├── .streamlit/
│   └── config.toml          # Cấu hình giao diện Streamlit (theme, layout)
├── data/
│   ├── raw/                 # Dữ liệu thô (Excel chương trình khung nhà trường)
│   └── knowledge_base/      # Dữ liệu đã chuẩn hóa (JSON/CSV)
│       ├── subjects.json    # Danh sách tất cả môn học (ID, Tên, Số TC)
│       ├── relations.json   # Định nghĩa quan hệ (Prerequisite, Parallel)
│       └── majors/          # Chương trình khung từng ngành
│           ├── cs_curriculum.json  # KH Máy tính
│           ├── ds_curriculum.json  # KH Dữ liệu
│           └── is_curriculum.json  # HT Thông tin
├── src/
│   ├── __init__.py
│   ├── graph_engine.py      # CORE: Chứa logic NetworkX, tạo đồ thị, tìm môn học tiếp theo
│   ├── rules.py             # Các luật nghiệp vụ (Ví dụ: Max tín chỉ 1 kỳ, môn chỉ mở kỳ 1)
│   ├── data_loader.py       # Hàm đọc dữ liệu từ folder data/
│   └── utils.py             # Các hàm phụ trợ (format text, tính điểm GPA giả lập...)
├── tests/                   # Unit test để đảm bảo logic gợi ý đúng
├── app.py                   # Main file chạy Streamlit
├── requirements.txt         # Các thư viện cần thiết
└── README.md                # Hướng dẫn sử dụng
``` 