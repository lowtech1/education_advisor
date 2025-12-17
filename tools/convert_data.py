import pandas as pd
import json
import os
import sys

# --- CẤU HÌNH ĐƯỜNG DẪN ---
INPUT_EXCEL_PATH = 'data/raw/data_daotao.xlsx'
OUTPUT_BASE_DIR = 'data/knowledge_base'

def clean_list_string(text):
    """
    Hàm hỗ trợ: Chuyển chuỗi 'INT1001, INT1002' thành list ['INT1001', 'INT1002'].
    """
    if pd.isna(text) or str(text).strip() == "":
        return []
    return [item.strip() for item in str(text).split(',') if item.strip()]

def run_conversion():
    print("🚀 Bắt đầu quy trình chuyển đổi dữ liệu (ETL)...")
    
    # 1. Kiểm tra file Excel
    if not os.path.exists(INPUT_EXCEL_PATH):
        print(f"❌ LỖI: Không tìm thấy file tại '{INPUT_EXCEL_PATH}'")
        return

    # 2. Đọc file Excel
    try:
        print(f"📂 Đang đọc file: {INPUT_EXCEL_PATH}...")
        df_subjects = pd.read_excel(INPUT_EXCEL_PATH, sheet_name='SubjectsList', engine='openpyxl')
        df_curriculum = pd.read_excel(INPUT_EXCEL_PATH, sheet_name='Curriculum', engine='openpyxl')
    except Exception as e:
        print(f"❌ Lỗi khi đọc file Excel: {e}")
        return

    # --- BƯỚC 3: XỬ LÝ DANH SÁCH MÔN (SubjectsList) ---
    subjects_data = []
    relations_data = []

    print("⚙️ Đang xử lý danh sách môn học...")
    # Chuẩn hóa tên cột (đề phòng người dùng viết hoa/thường không chuẩn)
    df_subjects.columns = [c.strip() for c in df_subjects.columns]

    for _, row in df_subjects.iterrows():
        try:
            ma_mon = str(row['SubjectID']).strip()
            
            # --- ĐOẠN NÀY ĐÃ ĐƯỢC CẬP NHẬT ---
            # Lấy thông tin Lý thuyết/Thực hành. Nếu để trống thì mặc định là 0.
            theory_cred = int(row['Theory']) if pd.notna(row.get('Theory')) else 0
            practice_cred = int(row['Practice']) if pd.notna(row.get('Practice')) else 0
            
            sub_item = {
                "id": ma_mon,
                "name": str(row['Name']).strip(),
                "credits": int(row['Credits']),
                "theory_credits": theory_cred,      # Mới thêm
                "practice_credits": practice_cred,  # Mới thêm
                "semesters_offered": [int(k) for k in clean_list_string(row['Semesters']) if str(k).isdigit()]
            }
            subjects_data.append(sub_item)

            # Xử lý Tiên quyết
            tien_quyet_list = clean_list_string(row['Prerequisites'])
            for tq_id in tien_quyet_list:
                relations_data.append({
                    "source": tq_id,
                    "target": ma_mon,
                    "type": "prerequisite"
                })
        except Exception as e:
            print(f"⚠️ Cảnh báo lỗi dòng môn {row.get('SubjectID', 'Unknown')}: {e}")

    # --- BƯỚC 4: LƯU FILE JSON ---
    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

    with open(f'{OUTPUT_BASE_DIR}/subjects.json', 'w', encoding='utf-8') as f:
        json.dump(subjects_data, f, ensure_ascii=False, indent=2)
    print(f"✅ Đã cập nhật: subjects.json (Thêm thông tin LT/TH)")

    with open(f'{OUTPUT_BASE_DIR}/relations.json', 'w', encoding='utf-8') as f:
        json.dump(relations_data, f, ensure_ascii=False, indent=2)

    # --- BƯỚC 5: XỬ LÝ NGÀNH (Giữ nguyên) ---
    print("⚙️ Đang tách file ngành...")
    majors_dir = f'{OUTPUT_BASE_DIR}/majors'
    os.makedirs(majors_dir, exist_ok=True)

    if 'MajorCode' in df_curriculum.columns:
        list_nganh = df_curriculum['MajorCode'].unique()
        for nganh in list_nganh:
            nganh_code = str(nganh).strip()
            df_nganh = df_curriculum[df_curriculum['MajorCode'] == nganh]
            
            curriculum_list = []
            for _, row in df_nganh.iterrows():
                curriculum_list.append({
                    "subject_id": str(row['SubjectID']).strip(),
                    "suggested_semester": int(row['SuggestedSem']),
                    "type": str(row['Type']).strip()
                })
            
            with open(f'{majors_dir}/{nganh_code}.json', 'w', encoding='utf-8') as f:
                json.dump(curriculum_list, f, ensure_ascii=False, indent=2)
    
    print("\n🎉 HOÀN TẤT! Dữ liệu mới đã sẵn sàng.")

if __name__ == "__main__":
    run_conversion()