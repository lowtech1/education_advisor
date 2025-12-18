import json
import pandas as pd

class AcademicAdvisor:
    def __init__(self, data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.majors = self.data['majors']
        self.subjects = self.data['subjects']

    def calculate_gpa(self, transcript):
        """Tính GPA hiện tại và tổng tín chỉ tích lũy"""
        total_points = 0
        total_credits = 0
        
        grade_map = {
            'A': 4.0, 'B+': 3.5, 'B': 3.0, 'C+': 2.5,
            'C': 2.0, 'D+': 1.5, 'D': 1.0, 'F': 0.0
        }
        
        for sub_id, grade in transcript.items():
            if grade == 'Chưa học' or sub_id not in self.subjects:
                continue
            
            creds = self.subjects[sub_id]['credits']
            gpa_point = grade_map.get(grade, 0)
            
            # Chỉ tính vào GPA nếu không phải F (hoặc tùy quy chế trường)
            # Ở đây giả định F vẫn tính vào mẫu số nhưng tử số là 0
            total_points += gpa_point * creds
            total_credits += creds
            
        gpa = total_points / total_credits if total_credits > 0 else 0.0
        return gpa, total_credits

    def suggest_next_semester(self, transcript, major_code, current_sem, planned_courses=[]):
        """
        Gợi ý môn học thông minh dựa trên Trọng số (Scoring System) - LEVEL 2
        """
        roadmap = self.majors[major_code]['roadmap']
        candidates = []
        
        # 1. Xác định các môn đã qua (D trở lên)
        passed_subjects = {
            s: g for s, g in transcript.items() 
            if g not in ['F', 'Chưa học']
        }
        
        # 2. Duyệt qua tất cả các môn trong chương trình
        all_semesters = sorted([int(k) for k in roadmap.keys()])
        
        for sem in all_semesters:
            sem_subjects = roadmap[str(sem)]
            
            for sub_id in sem_subjects:
                # Bỏ qua nếu đã học, đã chọn trong plan
                if sub_id in passed_subjects or sub_id in planned_courses:
                    continue
                
                subject = self.subjects.get(sub_id)
                if not subject: continue
                
                # --- KIỂM TRA TIÊN QUYẾT ---
                prereqs = subject.get('prerequisites', [])
                is_eligible = True
                
                for pr in prereqs:
                    if pr not in passed_subjects:
                        is_eligible = False
                        break
                
                if not is_eligible:
                    continue 
                
                # --- TÍNH ĐIỂM ƯU TIÊN (SCORING) ---
                priority_score = 0
                reason = ""
                priority_level = 1
                
                # Tiêu chí A: Trả nợ môn cũ (Quan trọng nhất)
                if sem < current_sem:
                    priority_score += 100
                    reason = "🔥 Trả nợ môn các kỳ trước"
                    priority_level = 3
                
                # Tiêu chí B: Môn đúng kỳ
                elif sem == current_sem + 1:
                    priority_score += 50
                    reason = "📘 Theo đúng lộ trình chuẩn"
                    priority_level = 1
                
                # Tiêu chí C: Học vượt
                else:
                    priority_score += 10
                    reason = "🚀 Học vượt"
                    priority_level = 1

                # Tiêu chí D: Mở khóa môn khác (Critical Path)
                unlock_power = 0
                for other_id, other_sub in self.subjects.items():
                    if sub_id in other_sub.get('prerequisites', []):
                        unlock_power += 1
                
                if unlock_power > 0:
                    priority_score += (unlock_power * 5)
                    if "Trả nợ" not in reason:
                        reason = f"🔑 Mở khóa cho {unlock_power} môn sau này"
                        priority_level = 2

                candidates.append({
                    'id': sub_id,
                    'name': subject['name'],
                    'credits': subject['credits'],
                    'difficulty': subject.get('difficulty', 3),
                    'priority': priority_level, 
                    'score': priority_score,
                    'reason': reason
                })

        # 3. Sắp xếp danh sách theo Điểm số (Cao xuống thấp)
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates

    def optimize_gpa(self, transcript, target_gpa):
        """Hàm cũ (ROI cơ bản) - Giữ lại để tránh lỗi nếu code cũ gọi"""
        pass 

    # === DƯỚI ĐÂY LÀ 2 HÀM BỊ THIẾU ===
    def calculate_credits_needed(self, current_gpa, current_credits, target_gpa, performance_gpa=4.0):
        """Tính toán cần bao nhiêu tín chỉ nữa để đạt Target"""
        if target_gpa <= current_gpa:
            return 0
        if performance_gpa <= target_gpa:
            return float('inf') 
            
        needed_credits = current_credits * (target_gpa - current_gpa) / (performance_gpa - target_gpa)
        return max(0, needed_credits)

    def find_easiest_subjects(self, transcript, planned_ids, limit=4):
        """Tìm các môn chưa học có độ khó thấp nhất (Easy Wins)"""
        candidates = []
        passed_subjects = set(transcript.keys())
        
        for sub_id, sub in self.subjects.items():
            if sub_id in passed_subjects or sub_id in planned_ids:
                continue
            candidates.append({
                'id': sub_id,
                'name': sub['name'],
                'credits': sub['credits'],
                'difficulty': sub.get('difficulty', 3)
            })
            
        # Sắp xếp: Độ khó tăng dần -> Tín chỉ giảm dần
        candidates.sort(key=lambda x: (x['difficulty'], -x['credits']))
        return candidates[:limit]