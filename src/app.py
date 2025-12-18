import streamlit as st
import os
import pandas as pd
from decision_engine import AcademicAdvisor

# =============================================================================
# 1. SETUP & STYLES
# =============================================================================
st.set_page_config(page_title="Academic DSS", page_icon="🎓", layout="wide")

def render_custom_css():
    st.markdown("""
        <style>
        .stApp { background-color: #0d1117; color: #c9d1d9; }
        
        /* Card Gợi ý */
        .rec-card {
            background-color: #161b22; border: 1px solid #30363d;
            border-radius: 8px; padding: 12px; margin-bottom: 10px;
        }
        .p-3 { border-left: 4px solid #f85149; background: rgba(248,81,73,0.05); } 
        .p-2 { border-left: 4px solid #d29922; }
        .p-1 { border-left: 4px solid #58a6ff; }

        /* Dashboard phải */
        .plan-dashboard {
            background-color: #161b22; border: 1px solid #30363d;
            border-radius: 10px; padding: 15px; margin-bottom: 15px;
        }
        .stat-label { font-size: 0.8em; color: #8b949e; text-transform: uppercase; }
        .stat-value { font-size: 1.4em; font-weight: bold; color: #fff; }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# 2. UI HELPER FUNCTIONS (Vẽ giao diện HTML)
# =============================================================================

def ui_render_plan_dashboard(planned_ids, advisor):
    """Vẽ Dashboard thống kê bên phải"""
    total_creds = 0
    total_difficulty = 0
    FEE_PER_CREDIT = 750000 
    
    for pid in planned_ids:
        sub = advisor.subjects.get(pid, {})
        total_creds += sub.get('credits', 0)
        total_difficulty += sub.get('difficulty', 3)
        
    avg_diff = (total_difficulty / len(planned_ids)) if planned_ids else 0
    est_fee = total_creds * FEE_PER_CREDIT
    bar_width = min(avg_diff / 5 * 100, 100)
    
    cred_color = '#ff6b6b' if total_creds > 20 else '#51cf66'
    
    if avg_diff > 3.5: comment = "🔥 Khá căng thẳng"
    elif avg_diff < 2.5: comment = "🌱 Vừa sức"
    else: comment = "⚖️ Cân bằng"

    html = f"""
    <div class="plan-dashboard">
        <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
            <div>
                <div class="stat-label">Tổng tín chỉ</div>
                <div class="stat-value" style="color:{cred_color}">{total_creds} <span style="font-size:0.6em; color:#8b949e">/ 20</span></div>
            </div>
            <div style="text-align:right;">
                <div class="stat-label">Học phí (Ước tính)</div>
                <div class="stat-value" style="color:#e0e0e0;">{est_fee:,.0f} đ</div>
            </div>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:end; margin-bottom:5px;">
            <div class="stat-label">Độ khó trung bình</div>
            <div style="font-weight:bold; color:#f0f6fc;">{avg_diff:.1f}/5.0</div>
        </div>
        <div style="height:8px; background:#21262d; border-radius:4px; overflow:hidden;">
            <div style="height:100%; width:{bar_width}%; background: linear-gradient(90deg, #51cf66, #fcc419, #ff6b6b); transition: width 0.5s;"></div>
        </div>
        <div style="font-size:0.8em; color:#8b949e; margin-top:5px; text-align:right; font-style:italic;">{comment}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
    return total_creds

def ui_render_recommendation_card(item):
    """Vẽ thẻ gợi ý môn học"""
    p_cls = f"p-{item['priority']}"
    icon = "🔥" if item['priority']==3 else ("⚠️" if item['priority']==2 else "📘")
    
    html = f"""
    <div class="rec-card {p_cls}">
        <div style="display:flex; justify-content:space-between;">
            <div style="font-weight:bold;">{icon} {item['name']}</div>
            <span style="background:#21262d; padding:2px 8px; border-radius:4px; font-size:0.8em; border:1px solid #30363d;">
                {item['credits']} TC
            </span>
        </div>
        <div style="font-size:0.9em; color:#8b949e; margin-top:4px;">Độ khó: {"⭐"*item['difficulty']}</div>
        <div style="font-size:0.9em; color:#c9d1d9; font-style:italic; margin-top:6px;">👉 {item['reason']}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# =============================================================================
# 3. CORE & INIT
# =============================================================================
@st.cache_resource
def load_advisor():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    data_path = os.path.join(project_root, 'data', 'curriculum.json')
    return AcademicAdvisor(data_path)

render_custom_css()
advisor = load_advisor()

if 'selected_major' not in st.session_state: st.session_state['selected_major'] = list(advisor.majors.keys())[0]
if 'transcript' not in st.session_state: st.session_state['transcript'] = {}
if 'current_sem' not in st.session_state: st.session_state['current_sem'] = 1
if 'planned_subjects' not in st.session_state: st.session_state['planned_subjects'] = [] 

# =============================================================================
# 4. MAIN LAYOUT
# =============================================================================

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Cấu hình")
    new_major = st.selectbox("Ngành học", list(advisor.majors.keys()), format_func=lambda x: advisor.majors[x]['name'])
    if new_major != st.session_state['selected_major']:
        st.session_state['selected_major'] = new_major
        st.session_state['transcript'] = {}
        st.session_state['planned_subjects'] = []
        st.rerun()
    
    st.divider()
    st.session_state['current_sem'] = st.selectbox("Trạng thái hiện tại:", range(1, 10), index=0, format_func=lambda x: f"Đã học xong Kỳ {x}")
    st.divider()
    
    gpa, creds = advisor.calculate_gpa(st.session_state['transcript'])
    st.markdown(f"""
        <div style="background:#21262d; padding:15px; border-radius:10px; text-align:center; border:1px solid #30363d;">
            <div style="color:#8b949e; font-size:0.8em">GPA TÍCH LŨY</div>
            <div style="font-size: 2.2em; font-weight: bold; color: #fff;">{gpa:.2f}</div>
            <div style="color:#238636; font-weight:bold">{creds} Tín chỉ</div>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("🗑️ Xóa dữ liệu", use_container_width=True):
        st.session_state['transcript'] = {}
        st.session_state['planned_subjects'] = []
        st.rerun()

st.title(f"🎓 Dashboard: {advisor.majors[st.session_state['selected_major']]['name']}")
tab1, tab2, tab3 = st.tabs(["📝 Nhập Điểm", "📅 Lập Kế Hoạch", "📈 Chiến Lược GPA"])

# === TAB 1: NHẬP ĐIỂM ===
with tab1:
    roadmap = advisor.majors[st.session_state['selected_major']]['roadmap']
    for sem_idx in sorted([int(k) for k in roadmap.keys()]):
        if sem_idx > st.session_state['current_sem'] + 1: continue
        with st.expander(f"Học kỳ {sem_idx}", expanded=(sem_idx <= st.session_state['current_sem'])):
            cols = st.columns(3)
            for i, sub_id in enumerate(roadmap[str(sem_idx)]):
                with cols[i % 3]:
                    sub = advisor.subjects.get(sub_id, {'name': sub_id})
                    curr = st.session_state['transcript'].get(sub_id, "Chưa học")
                    opts = ["Chưa học", "A", "B+", "B", "C+", "C", "D+", "D", "F"]
                    val = st.selectbox(f"{sub['name']}", opts, index=opts.index(curr), key=f"g_{sub_id}")
                    if val != "Chưa học": st.session_state['transcript'][sub_id] = val
                    elif sub_id in st.session_state['transcript']: del st.session_state['transcript'][sub_id]

# === TAB 2: LẬP KẾ HOẠCH (Code chuẩn) ===
with tab2:
    col_suggest, col_plan = st.columns([1.3, 1])

    # --- CỘT PHẢI: KẾ HOẠCH ---
    with col_plan:
        st.subheader("🎒 Giỏ môn học")
        current_creds = ui_render_plan_dashboard(st.session_state['planned_subjects'], advisor)
        
        if current_creds > 20: st.error("⚠️ Quá tải! > 20 tín chỉ.")
        
        if not st.session_state['planned_subjects']:
            st.info("👈 Chọn môn từ bên trái")
        else:
            st.write("---")
            for pid in st.session_state['planned_subjects']:
                sub = advisor.subjects.get(pid, {})
                c1, c2, c3 = st.columns([5, 2, 1])
                c1.markdown(f"**{sub.get('name', pid)}**")
                c2.caption(f"{sub.get('credits',0)} TC")
                if c3.button("❌", key=f"del_{pid}"):
                    st.session_state['planned_subjects'].remove(pid)
                    st.rerun()
                st.divider()

    # --- CỘT TRÁI: GỢI Ý ---
    with col_suggest:
        st.subheader(f"💡 Gợi ý Kỳ {st.session_state['current_sem'] + 1}")
        
        recs = advisor.suggest_next_semester(
            st.session_state['transcript'], 
            st.session_state['selected_major'], 
            st.session_state['current_sem'],
            planned_courses=st.session_state['planned_subjects']
        )
        
        if not recs:
            st.success("🎉 Không còn môn nào gợi ý!")
        
        for item in recs:
            ui_render_recommendation_card(item)
            c_btn, _ = st.columns([1, 2])
            if c_btn.button("➕ Thêm", key=f"add_{item['id']}"):
                st.session_state['planned_subjects'].append(item['id'])
                st.rerun()

# === TAB 3: CHIẾN LƯỢC (Simulator & Chart) ===
with tab3:
    st.markdown("### 🎯 Mục tiêu & Mô phỏng")
    c_left, c_right = st.columns([1, 2])
    
    # --- CỘT TRÁI: CẤU HÌNH ---
    with c_left:
        st.markdown("#### 1. Thiết lập mục tiêu")
        target_gpa = st.number_input("GPA Mục tiêu:", 0.0, 4.0, 3.2, 0.05)
        
        st.markdown("---")
        st.markdown("#### 2. Giả định phong độ")
        st.caption("Bạn dự định sẽ học các môn tới với điểm trung bình bao nhiêu?")
        
        # Thêm lựa chọn "Tự nhập" vào cuối danh sách
        mode_options = [
            "🔥 Hardcore (Toàn A - 4.0)", 
            "💪 Nỗ lực (A/B+ - 3.6)", 
            "😐 Bình ổn (B - 3.0)", 
            "⚙️ Tự nhập (Custom)"
        ]
        
        performance_mode = st.radio(
            "Chọn chế độ:",
            mode_options,
            index=1 # Mặc định chọn "Nỗ lực"
        )
        
        # Xử lý Logic chọn điểm
        if "Custom" in performance_mode:
            perf_score = st.number_input(
                "Nhập GPA dự kiến của bạn:",
                min_value=0.0, max_value=4.0, value=2.5, step=0.1,
                help="Điểm trung bình các môn sắp tới bạn nghĩ mình sẽ đạt được."
            )
        else:
            # Map preset ra điểm số
            if "Hardcore" in performance_mode: perf_score = 4.0
            elif "Nỗ lực" in performance_mode: perf_score = 3.6
            else: perf_score = 3.0

    # --- CỘT PHẢI: KẾT QUẢ & BIỂU ĐỒ ---
    with c_right:
        gap = target_gpa - gpa
        
        # Case 1: Đã đạt mục tiêu
        if gap <= 0:
            st.success(f"🏆 Tuyệt vời! GPA hiện tại ({gpa:.2f}) đã đạt hoặc vượt mục tiêu ({target_gpa:.2f}).")
            st.balloons()
            
        # Case 2: Phong độ thấp hơn mục tiêu (Không bao giờ kéo lên được)
        elif perf_score <= target_gpa:
            st.error(f"⚠️ **Không khả thi!** Bạn muốn đạt GPA **{target_gpa}** nhưng phong độ dự kiến chỉ là **{perf_score}**. Bạn cần học với điểm trung bình cao hơn mục tiêu mới kéo điểm lên được.")
            
        # Case 3: Tính toán bình thường
        else:
            creds_needed = advisor.calculate_credits_needed(gpa, creds, target_gpa, perf_score)
            
            # Hiển thị Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("GPA Hiện tại", f"{gpa:.2f}")
            m2.metric("GPA Mục tiêu", f"{target_gpa:.2f}", delta=f"{gap:.2f}")
            m3.metric("Cần thêm", f"{creds_needed:.1f} TC", delta_color="inverse", help="Số tín chỉ cần học thêm để đạt mục tiêu")
            
            st.info(f"💡 Với phong độ **{perf_score}**, bạn cần học khoảng **{int(creds_needed)}** tín chỉ nữa (tương đương ~{int(creds_needed/3)} môn) để đạt mục tiêu.")
            
            # --- VẼ BIỂU ĐỒ (Đã fix lỗi chia cho 0) ---
            chart_data = {"Tín chỉ": [], "GPA": []}
            curr_c, curr_g = creds, gpa
            
            # Giới hạn steps để tránh vòng lặp vô tận nếu số quá lớn
            steps = int(creds_needed / 3) + 2
            if steps > 50: steps = 50 
            
            for i in range(steps + 1):
                added = i * 3
                total_new_credits = curr_c + added
                
                if total_new_credits == 0:
                    new_g = 0.0
                else:
                    new_g = ((curr_g * curr_c) + (perf_score * added)) / total_new_credits
                    
                chart_data["Tín chỉ"].append(total_new_credits)
                chart_data["GPA"].append(new_g)
                
            st.line_chart(pd.DataFrame(chart_data), x="Tín chỉ", y="GPA", color="#51cf66")

    st.divider()
    
    # --- GỢI Ý MÔN DỄ ---
    st.subheader("🥝 Gợi ý môn cải thiện điểm")
    st.caption("Các môn chưa học có độ khó thấp nhất, giúp bạn dễ dàng đạt mức điểm phong độ đã chọn.")
    
    easy_subjects = advisor.find_easiest_subjects(st.session_state['transcript'], st.session_state['planned_subjects'])
    
    if easy_subjects:
        cols = st.columns(4)
        for idx, sub in enumerate(easy_subjects):
            with cols[idx % 4]:
                st.markdown(f"""
                <div style="background:#161b22; border:1px solid #30363d; border-radius:8px; padding:15px; text-align:center; height:140px; display:flex; flex-direction:column; justify-content:center;">
                    <div style="font-size:2em;">🍀</div>
                    <div style="font-weight:bold; color:#58a6ff; margin-top:5px;">{sub['name']}</div>
                    <div style="font-size:0.8em; color:#8b949e;">{sub['credits']} TC | Khó: {sub['difficulty']}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Chọn", key=f"boost_{sub['id']}", use_container_width=True):
                    st.session_state['planned_subjects'].append(sub['id'])
                    st.rerun()
    else:
        st.info("Không tìm thấy môn gợi ý phù hợp.")