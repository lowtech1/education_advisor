import json
import networkx as nx
import os

class CourseGraph:
    def __init__(self, data_dir):
        self.graph = nx.DiGraph()
        self.subjects_map = {}
        self._load_data(data_dir)

    def _load_data(self, data_dir):
        if not os.path.exists(data_dir):
            print(f"Warning: Directory {data_dir} not found.")
            return

        for filename in os.listdir(data_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        # TRƯỜNG HỢP 1: File JSON là một danh sách các môn học (List)
                        if isinstance(data, list):
                            for item in data:
                                self._add_subject_to_graph(item)
                                
                        # TRƯỜNG HỢP 2: File JSON là một môn học đơn lẻ (Dict)
                        elif isinstance(data, dict):
                            self._add_subject_to_graph(data)
                            
                except Exception as e:
                    print(f"Error loading file {filename}: {e}")

    def _add_subject_to_graph(self, data):
        """Hàm phụ trợ để thêm môn vào đồ thị"""
        if 'id' not in data: return # Bỏ qua nếu data rác
        
        self.graph.add_node(data['id'], **data)
        self.subjects_map[data['id']] = data
        
        if 'prerequisites' in data:
            for pre_id in data['prerequisites']:
                self.graph.add_edge(pre_id, data['id'])

    def get_prerequisites(self, subject_id):
        """Lấy danh sách môn tiên quyết (Cha)"""
        if subject_id in self.graph:
            return list(self.graph.predecessors(subject_id))
        return []

    def get_dependents(self, subject_id):
        """Lấy danh sách môn học sau (Con)"""
        if subject_id in self.graph:
            return list(self.graph.successors(subject_id))
        return []

    # --- 👇 PHẦN MỚI: THUẬT TOÁN GỢI Ý THÔNG MINH 👇 ---
    
    def calculate_subject_weight(self, subject_id):
        """
        Tính trọng số (độ quan trọng) của môn học dựa trên đồ thị.
        Logic: Môn nào mở khóa càng nhiều môn phía sau thì càng quan trọng.
        """
        if subject_id not in self.graph: return 0
        
        # Đếm tổng số môn "cháu chắt chút chít" phụ thuộc vào môn này
        descendants = nx.descendants(self.graph, subject_id)
        return len(descendants)

    def get_recommendations(self, user_profile):
        """
        Input: user_profile (dict chứa passed_subjects, failed_subjects, current_semester)
        Output: Danh sách gợi ý đã sắp xếp theo độ ưu tiên
        """
        passed = set(user_profile['passed_subjects'])
        failed = set(user_profile['failed_subjects'])
        current_sem = user_profile.get('current_semester', 1)
        
        recommendations = []
        
        for sub_id, sub_data in self.subjects_map.items():
            # 1. Bỏ qua môn đã qua
            if sub_id in passed:
                continue
                
            # 2. Kiểm tra điều kiện tiên quyết
            prereqs = self.get_prerequisites(sub_id)
            if not all(p in passed for p in prereqs):
                continue # Chưa đủ điều kiện học
            
            # 3. TÍNH ĐIỂM ƯU TIÊN (SCORING)
            score = 0
            reasons = []
            
            # Tiêu chí A: Môn rớt (Quan trọng nhất)
            if sub_id in failed:
                score += 1000
                reasons.append("⚠️ Cần học lại ngay")
                
            # Tiêu chí B: Môn quan trọng (Mở khóa nhiều môn khác)
            importance = self.calculate_subject_weight(sub_id)
            if importance > 0:
                score += importance * 10 # Mỗi môn phụ thuộc +10 điểm
                if importance >= 3: # Ngưỡng
                    reasons.append(f"🔓 Mở khóa {importance} môn sau")
            
            # Tiêu chí C: Đúng lộ trình (Đúng kỳ đang học)
            semesters = sub_data.get('semesters_offered', [])
            # Giả sử kỳ 5 là kỳ lẻ, kỳ 6 là kỳ chẵn (hoặc đúng số kỳ)
            if current_sem in semesters:
                score += 50
                reasons.append("📅 Đúng lộ trình kỳ này")
            elif any(s < current_sem for s in semesters):
                score += 30
                reasons.append("Giai đoạn trước (Học bù)")
                
            # Tiêu chí D: Môn tự chọn hoặc ít quan trọng
            if score == 0:
                score = 1
                reasons.append("Môn tự chọn / Bổ trợ")

            recommendations.append({
                "id": sub_id,
                "name": sub_data['name'],
                "credits": sub_data['credits'],
                "score": score,
                "reasons": reasons
            })
            
        # 4. Sắp xếp: Điểm cao lên đầu
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations