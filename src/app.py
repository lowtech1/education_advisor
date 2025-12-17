import streamlit as st
import pandas as pd
from graph_engine import CourseGraph
from user_manager import UserManager
import os

# --- 1. CẤU HÌNH & CSS (DARK MODE) ---
st.set_page_config(layout="wide", page_title="Cổng Đào Tạo & Đăng Ký", page_icon="🎓")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    
    /* CSS Card Trạng thái */
    .status-box { padding: 10px; border-radius: 5px; margin-bottom: 5px; font-size: 0.9rem; }
    .passed { background-color: #1b3a24; border-left: 4px solid #4CAF50; color: #e8f5e9; } 
    .fail { background-color: #4a1818; border-left: 4px solid #ff5252; color: #ffebee; }   
    .selected { background-color: #423608; border-left: 4px solid #fdd835; color: #fffde7; } 
    .locked { background-color: #262730; border-left: 4px solid #6c757d; color: #adb5bd; }   
    
    /* CSS Khung Đăng ký */
    .reg-container { 
        border: 1px solid #4CAF50; 
        padding: 20px; 
        border-radius: 10px; 
        background-color: #161b22; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    .stProgress > div > div > div > div { background-color: #4CAF50; }
    .streamlit-expanderHeader { background-color: #262730; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. KHỞI TẠO HỆ THỐNG (BACKEND) ---
@st.cache_resource
def load_system():
    # Load Graph Engine (Dữ liệu môn học)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    data_path = os.path.join(project_root, 'data', 'knowledge_base')
    
    # Kiểm tra thư mục data
    if not os.path.exists(data_path):
        st.error(f"❌ Không tìm thấy thư mục data: {data_path}")
        st.stop()
        
    engine = CourseGraph(data_dir=data_path)
    user_mgr = UserManager()
    
    return engine, user_mgr

try:
    engine, user_manager = load_system()
except TypeError as e:
    # Bắt đúng lỗi bạn đang gặp phải và hiển thị hướng dẫn
    st.error("❌ LỖI DỮ LIỆU (TYPE ERROR):")
    st.error(f"Chi tiết: {e}")
    st.warning("""
    **Nguyên nhân:** Có thể một file JSON trong thư mục `data` đang là dạng Danh sách `[...]` nhưng hệ thống mong đợi dạng Đối tượng `{...}`.
    \n**Cách sửa:** Vui lòng kiểm tra file `graph_engine.py` và cập nhật hàm `_load_data` (xem hướng dẫn bên dưới).
    """)
    st.stop()
except Exception as e:
    st.error(f"❌ Lỗi khởi tạo hệ thống khác: {e}")
    st.stop()

# --- 3. QUẢN LÝ SESSION ---
if 'user' not in st.session_state: st.session_state['user'] = None
if 'selected_courses' not in st.session_state: st.session_state['selected_courses'] = set()

# --- 4. MÀN HÌNH ĐĂNG NHẬP ---
if st.session_state['user'] is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.title("🎓 Portal Sinh Viên")
        st.caption("Hệ thống Hỗ trợ Học tập & Gợi ý Lộ trình")
        
        with st.container(border=True):
            mssv_input = st.text_input("Mã Sinh Viên", placeholder="Nhập: SV001")
            if st.button("Đăng nhập", type="primary", use_container_width=True):
                user_data = user_manager.authenticate(mssv_input)
                if user_data:
                    st.session_state['user'] = user_data
                    st.session_state['user_id'] = mssv_input
                    # Load kế hoạch cũ
                    saved_plan = user_manager.get_user_plan(mssv_input)
                    st.session_state['selected_courses'] = saved_plan
                    st.rerun()
                else:
                    st.error("⚠️ Không tìm thấy sinh viên! Kiểm tra file users.json")
    st.stop()

# --- 5. GIAO DIỆN DASHBOARD ---
user = st.session_state['user']
user_id = st.session_state['user_id']
passed = set(user['passed_subjects'])
failed = set(user['failed_subjects'])
selected = st.session_state['selected_courses']

# === SIDEBAR ===
with st.sidebar:
    st.title(f"{user['name']}")
    st.caption(f"MSSV: {user_id}")
    st.divider()
    st.markdown(f"**Ngành:** {user['major']}")
    st.markdown(f"**Năm thứ:** {user['year']} (Kỳ {user['current_semester']})")
    
    total_credits = sum(engine.subjects_map[s]['credits'] for s in passed if s in engine.subjects_map)
    st.metric("Tín chỉ tích lũy", f"{total_credits}")
    
    st.divider()
    if st.button("Đăng xuất"):
        st.session_state['user'] = None
        st.session_state['selected_courses'] = set()
        st.rerun()

# === MAIN CONTENT ===
st.title("Lập Kế Hoạch Học Tập")

# --- PHẦN A: TƯƠNG TÁC & GỢI Ý ---
st.markdown(f"### 🤖 Gợi ý Môn học (Kỳ {user['current_semester']})")

try:
    recommendations = engine.get_recommendations(user)
except Exception:
    recommendations = []

# Phân nhóm
critical_group = [r for r in recommendations if r['score'] >= 1000]
high_priority = [r for r in recommendations if 100 <= r['score'] < 1000]
others = [r for r in recommendations if r['score'] < 100]

def render_suggestion_group(group_title, subjects, color_border):
    if not subjects: return
    st.subheader(group_title)
    for sub in subjects:
        sid = sub['id']
        col_check, col_info = st.columns([0.5, 5])
        with col_check:
            is_checked = st.checkbox("Chọn", key=f"chk_{sid}", value=(sid in selected), label_visibility="hidden")
            if is_checked: selected.add(sid)
            elif sid in selected: selected.remove(sid)

        with col_info:
            reason_badges = ""
            for r in sub['reasons']:
                if "Rớt" in r: badge_color = "#ff5252"
                elif "Mở khóa" in r: badge_color = "#AB47BC"
                elif "Đúng lộ trình" in r: badge_color = "#2196F3"
                else: badge_color = "#607d8b"
                reason_badges += f'<span style="background-color:{badge_color}; padding:2px 6px; border-radius:4px; font-size:0.75em; margin-right:5px; color:white;">{r}</span>'

            st.markdown(f"""
            <div style="border-left: 4px solid {color_border}; background-color: #1E2129; padding: 10px; border-radius: 4px; margin-bottom: 8px;">
                <div style="font-weight: bold; font-size: 1.05em; color: white;">
                    {sub['name']} <span style="font-weight:normal; font-size:0.9em; color:#bbb;">({sub['credits']} TC)</span>
                </div>
                <div style="margin-top: 5px;">{reason_badges}</div>
            </div>
            """, unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="reg-container">', unsafe_allow_html=True)
    col_suggestion, col_summary = st.columns([2.2, 1])
    
    with col_suggestion:
        if not recommendations:
            st.success("🎉 Không có môn học nào cần gợi ý thêm!")
        else:
            if critical_group: render_suggestion_group("🔥 Cần xử lý gấp", critical_group, "#ff5252")
            if high_priority: render_suggestion_group("⭐ Lộ trình đề xuất", high_priority, "#FFD700")
            with st.expander("Các môn khác"): render_suggestion_group("Tự chọn / Bổ trợ", others, "#9e9e9e")

    with col_summary:
        st.markdown("#### 📊 Dự kiến")
        current_credits = sum(engine.subjects_map[s]['credits'] for s in selected)
        count_sub = len(selected)
        
        st.info(f"Đang chọn: **{count_sub} môn**")
        progress_val = min(current_credits / 24, 1.0)
        st.write(f"Tổng: **{current_credits}** / 24 TC")
        
        if current_credits > 20: st.progress(progress_val, text="Quá tải")
        else: st.progress(progress_val, text="Ổn định")

        tuition = current_credits * 550000 
        st.write(f"💰 Học phí: `{tuition:,.0f} đ`")

        st.markdown("---")
        if current_credits > 0:
            if st.button("💾 LƯU KẾ HOẠCH", type="primary", use_container_width=True):
                if user_manager.update_plan(user_id, selected):
                    st.toast("Đã lưu thành công!", icon="✅")
                    st.session_state['user']['planned_subjects'] = list(selected)
                else: st.error("Lỗi lưu file!")
        else: st.caption("Hãy chọn môn học.")
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- PHẦN B: LỘ TRÌNH ---
st.markdown("### 🗺️ Toàn cảnh Lộ trình")

curriculum_by_year = {1: [], 2: [], 3: [], 4: []}
for sub in engine.subjects_map.values():
    sem = sub.get('semesters_offered', [1])[0] # Dùng .get để tránh lỗi nếu thiếu field
    year = (sem - 1) // 2 + 1
    if year in curriculum_by_year:
        curriculum_by_year[year].append((sem, sub))

for year_idx in range(1, 5):
    subjects_in_year = curriculum_by_year[year_idx]
    passed_in_year = sum(1 for _, s in subjects_in_year if s['id'] in passed)
    total_in_year = len(subjects_in_year)
    is_expanded = (year_idx == (user['current_semester']-1)//2 + 1)
    
    with st.expander(f"📅 NĂM THỨ {year_idx} ({passed_in_year}/{total_in_year} môn)", expanded=is_expanded):
        col_a, col_b = st.columns(2)
        sem_a, sem_b = year_idx * 2 - 1, year_idx * 2
        
        def render_list(sub_list, col, sem):
            with col:
                st.caption(f"**Học kỳ {sem}**")
                for sub in sub_list:
                    sid = sub['id']
                    css, txt = "locked", "⚪ Chưa học"
                    if sid in passed: css, txt = "passed", "✅ Đã qua"
                    elif sid in failed: css, txt = "fail", "❌ RỚT"
                    elif sid in selected: css, txt = "selected", "🟡 Dự kiến"
                    elif all(p in passed for p in engine.get_prerequisites(sid)): css, txt = "locked", "⚪ Chưa đăng ký"
                    else: css, txt = "locked", "🔒 Khóa"

                    st.markdown(f"""
                    <div class="status-box {css}">
                        <div style="font-weight:bold;">{sub['name']}</div>
                        <div style="display:flex; justify-content:space-between; font-size:0.85em; opacity:0.9;">
                            <span>{sid} • {sub['credits']}TC</span>
                            <span>{txt}</span>
                        </div>
                    </div>""", unsafe_allow_html=True)

        render_list([s for sm, s in subjects_in_year if sm == sem_a], col_a, sem_a)
        render_list([s for sm, s in subjects_in_year if sm == sem_b], col_b, sem_b)