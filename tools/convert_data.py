import pandas as pd
import json
import os
import sys

# --- CẤU HÌNH ĐƯỜNG DẪN ---
#Input file data_daotao
INPUT_EXCEL_PATH = 'data/raw/data_daotao.xlsx'
# Thư mục chứa môn học chuẩn 
OUTPUT_BASE_DIR = 'data/knowledge_base'

def clean_list_string(text):
    """
    Hàm hỗ trợ: Chuyển chuỗi 'INT1001, INT1002' thành list ['INT1001', 'INT1002'].
    Xử lý cả trường hợp ô trống (NaN).
    """
    if pd.isna(text) or str(text).strip() == "":
        return []
    # Chuyển thành chuỗi, tách dấu phẩy, và xóa khoảng trắng thừa
    return [item.strip() for item in str(text).split(',') if item.strip()]

def run_conversion():
    print("Bắt đầu quy trình chuyển đổi dữ liệu (ETL)...")
    
    # 1. Kiểm tra file Excel
    if not os.path.exists(INPUT_EXCEL_PATH):
        print(f"LỖI: Không tìm thấy file tại '{INPUT_EXCEL_PATH}'")
        print("Vui lòng tạo file Excel và lưu vào đúng thư mục data/raw/")
        return

    # 2. Đọc file Excel
    try:
        print(f"Đang đọc file: {INPUT_EXCEL_PATH}...")
        # Đọc Sheet 1: Danh sách môn học
        df_subjects = pd.read_excel(INPUT_EXCEL_PATH, sheet_name='SubjectsList', engine='openpyxl')
        # Đọc Sheet 2: Chương trình khung
        df_curriculum = pd.read_excel(INPUT_EXCEL_PATH, sheet_name='Curriculum', engine='openpyxl')
    except Exception as e:
        print(f"Lỗi khi đọc file Excel: {e}")
        print("Hãy chắc chắn bạn đã tạo đúng 2 Sheet tên là 'SubjectsList' và 'Curriculum'")
        return

    # --- BƯỚC 3: XỬ LÝ DANH SÁCH MÔN (SubjectsList) ---
    subjects_data = []
    relations_data = []

    print("Đang xử lý danh sách môn học...")
    for _, row in df_subjects.iterrows():
        try:
            ma_mon = str(row['SubjectID']).strip()
            
            # Tạo object môn học
            sub_item = {
                "id": ma_mon,
                "name": str(row['Name']).strip(),
                "credits": int(row['Credits']),
                # Xử lý cột Semesters (VD: "1, 2" -> [1, 2])
                "semesters_offered": [int(k) for k in clean_list_string(row['Semesters']) if str(k).isdigit()]
            }
            subjects_data.append(sub_item)

            # Xử lý cột Prerequisites (Môn tiên quyết)
            tien_quyet_list = clean_list_string(row['Prerequisites'])
            for tq_id in tien_quyet_list:
                rel_item = {
                    "source": tq_id,      # Môn cần học trước
                    "target": ma_mon,     # Môn học sau
                    "type": "prerequisite"
                }
                relations_data.append(rel_item)
        except Exception as e:
            print(f"Cảnh báo: Lỗi dòng dữ liệu môn {row.get('SubjectID', 'Unknown')}: {e}")

    # --- BƯỚC 4: LƯU FILE SUBJECTS VÀ RELATIONS ---
    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True) # Tạo thư mục nếu chưa có

    # Lưu subjects.json
    with open(f'{OUTPUT_BASE_DIR}/subjects.json', 'w', encoding='utf-8') as f:
        json.dump(subjects_data, f, ensure_ascii=False, indent=2)
    print(f"Đã tạo: {OUTPUT_BASE_DIR}/subjects.json ({len(subjects_data)} môn)")

    # Lưu relations.json
    with open(f'{OUTPUT_BASE_DIR}/relations.json', 'w', encoding='utf-8') as f:
        json.dump(relations_data, f, ensure_ascii=False, indent=2)
    print(f"Đã tạo: {OUTPUT_BASE_DIR}/relations.json ({len(relations_data)} quan hệ)")

    # --- BƯỚC 5: XỬ LÝ CHƯƠNG TRÌNH KHUNG (Curriculum) ---
    print("Đang tách file chương trình đào tạo theo ngành...")
    
    majors_dir = f'{OUTPUT_BASE_DIR}/majors'
    os.makedirs(majors_dir, exist_ok=True)

    # Lấy danh sách các mã ngành duy nhất có trong file
    if 'MajorCode' in df_curriculum.columns:
        list_nganh = df_curriculum['MajorCode'].unique()

        for nganh in list_nganh:
            nganh_code = str(nganh).strip()
            # Lọc lấy các dòng thuộc ngành này
            df_nganh = df_curriculum[df_curriculum['MajorCode'] == nganh]
            
            curriculum_list = []
            for _, row in df_nganh.iterrows():
                curriculum_list.append({
                    "subject_id": str(row['SubjectID']).strip(),
                    "suggested_semester": int(row['SuggestedSem']),
                    "type": str(row['Type']).strip() # BatBuoc / TuChon
                })
            
            # Lưu file json riêng cho từng ngành (VD: CNTT.json)
            file_path = f'{majors_dir}/{nganh_code}.json'
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(curriculum_list, f, ensure_ascii=False, indent=2)
            
            print(f"  -> Đã tạo: {file_path} ({len(curriculum_list)} môn)")
    else:
        print("Lỗi: Không tìm thấy cột 'MajorCode' trong sheet Curriculum.")

    print("\nHOÀN TẤT! Dữ liệu đã sẵn sàng để chạy App.")

# --- CHẠY CHƯƠNG TRÌNH ---
if __name__ == "__main__":
    run_conversion()