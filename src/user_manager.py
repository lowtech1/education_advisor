import json
import os

# Xác định đường dẫn tới file users.json
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DATA_FILE = os.path.join(PROJECT_ROOT, 'data', 'users.json')

class UserManager:
    def __init__(self):
        self.data_file = DATA_FILE
        self.users = self.load_data()

    def load_data(self):
        """Đọc dữ liệu từ file JSON"""
        if not os.path.exists(self.data_file):
            return {} # Trả về rỗng nếu chưa có file
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Lỗi đọc data user: {e}")
            return {}

    def save_data(self):
        """Ghi dữ liệu hiện tại vào file JSON"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Lỗi lưu data: {e}")
            return False

    def authenticate(self, user_id):
        """Kiểm tra đăng nhập"""
        return self.users.get(user_id)

    def update_plan(self, user_id, selected_subjects):
        """Cập nhật kế hoạch đăng ký môn của sinh viên"""
        if user_id in self.users:
            # Chuyển set thành list để lưu được vào JSON
            self.users[user_id]['planned_subjects'] = list(selected_subjects)
            return self.save_data()
        return False

    def get_user_plan(self, user_id):
        """Lấy danh sách môn đã đăng ký (trả về dạng Set)"""
        if user_id in self.users:
            return set(self.users[user_id].get('planned_subjects', []))
        return set()