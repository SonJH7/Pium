import streamlit as st
import auth
import plant
import game
import expert
import content_mgr
import admin

def init_session():
    """세션 초기화"""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "show_auth" not in st.session_state:
        st.session_state.show_auth = False

def get_role_badge(role):
    """역할에 따른 HTML 배지 디자인 반환"""
    
    # 역할별 디자인 설정 (배경색, 글자색, 아이콘, 표시 이름)
    badges = {
        "User": {
            "bg": "#e8f5e9", "color": "#2e7d32", "border": "#c8e6c9",
            "icon": "🌱", "label": "새싹 농부"
        },
        "Expert": {
            "bg": "#fff8e1", "color": "#f9a825", "border": "#ffe082",
            "icon": "🎓", "label": "식물 전문가"
        },
        "Content": {
            "bg": "#e3f2fd", "color": "#1565c0", "border": "#bbdefb",
            "icon": "📝", "label": "콘텐츠 에디터"
        },
        "Admin": {
            "bg": "#ffebee", "color": "#c62828", "border": "#ffcdd2",
            "icon": "🛡️", "label": "시스템 관리자"
        }
    }
    
    # 기본값 (User)
    style = badges.get(role, badges["User"])
    
    html = f"""
    <span style='
        display: inline-flex;
        align-items: center;
        background-color: {style['bg']};
        color: {style['color']};
        border: 1px solid {style['border']};
        padding: 4px 10px;
        border-radius: 15px;
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 5px;
    '>
        <span style='margin-right: 6px;'>{style['icon']}</span> {style['label']}
    </span>
    """
    return html

def main():
    st.set_page_config(
        page_title="Pium: 인터랙티브 식물 도감", 
        layout="wide", 
        page_icon="🌱"
    )
    init_session()

    # --- 헤더 영역 ---
    col1, col2 = st.columns([3, 1.2])
    
    with col1:
        st.title("🌱 Pium: 인터랙티브 식물 도감")
        st.caption("식물을 검색하고, 퀴즈를 풀며 나만의 정원을 '피움(Pium)'하세요!")
    
    with col2:
        if st.session_state.user is None:
            st.write("") # 간격 맞춤
            if st.button("로그인 / 회원가입", use_container_width=True):
                st.session_state.show_auth = True
        else:
            u = st.session_state.user
            
            # [변경됨] 역할 배지 표시
            role_badge_html = get_role_badge(u['role'])
            
            with st.container(border=True):
                # 배지와 이름 표시
                st.markdown(f"{role_badge_html} &nbsp; **{u['name']}**님", unsafe_allow_html=True)
                st.caption(f"{u['department']} | {u['student_id']}")
                st.markdown(f"💰 **포인트:** :green[{u['points']:,} P]")
                
                if st.button("로그아웃", use_container_width=True, key="logout_btn"):
                    st.session_state.user = None
                    st.rerun()

    st.markdown("---")

    # --- 모달 ---
    if st.session_state.show_auth:
        auth.auth_view()
        return

    # --- 사이드바 ---
    st.sidebar.header("User Menu")
    
    # 사이드바에도 배지 표시 (로그인 시)
    if st.session_state.user:
        u = st.session_state.user
        st.sidebar.markdown(get_role_badge(u['role']), unsafe_allow_html=True)
        st.sidebar.markdown(f"**{u['name']}**님 환영합니다!")
        st.sidebar.divider()

    menu = ["🏠 홈 / 도감"]
    
    if st.session_state.user:
        role = st.session_state.user['role']
        
        # 1. 플레이어 기능
        menu.append("🌿 내 식물 키우기")
        
        # 2. 전문가 기능
        if role in ['Expert', 'Content', 'Admin']:
            menu.append("🎓 전문가: 팁 작성")
            
        # 3. 콘텐츠 관리자 기능
        if role in ['Content', 'Admin']:
            menu.append("📝 콘텐츠 관리 (식물/경제)")
            
        # 4. 시스템 관리자 기능
        if role == 'Admin':
            menu.append("⚙️ 시스템 관리 (계정/로그)")

    choice = st.sidebar.radio("Go to", menu)
    
    # 전문가 신청 버튼 (User일 때만)
    if st.session_state.user and st.session_state.user['role'] == 'User':
        st.sidebar.markdown("---")
        with st.sidebar.expander("🎓 전문가 등급 신청"):
            conn = auth.get_conn()
            cur = conn.cursor()
            
            cur.execute("SELECT status FROM expert_application WHERE user_id=%s", (st.session_state.user['user_id'],))
            row = cur.fetchone()
            can_apply = True
            
            if row:
                status = row[0]
                if status == 'PENDING':
                    st.info("🕒 심사 대기 중입니다.")
                    can_apply = False
                elif status == 'APPROVED':
                    st.success("✅ 이미 전문가 승인을 받았습니다.")
                    can_apply = False
                elif status == 'REJECTED':
                    st.error("반려되었습니다. 내용을 보완해 다시 신청하세요.")

            if can_apply:
                with st.form("expert_apply_form"):
                    st.write("전문 지식이 있으신가요?")
                    reason = st.text_area("신청 사유", height=80, placeholder="학과, 자격증 등")
                    submitted = st.form_submit_button("신청서 제출")
                    
                    if submitted and reason:
                        try:
                            upsert_sql = """
                                INSERT INTO expert_application (user_id, request_text, status, decided_at)
                                VALUES (%s, %s, 'PENDING', NULL)
                                ON CONFLICT (user_id) DO UPDATE SET 
                                    request_text = EXCLUDED.request_text, status = 'PENDING';
                            """
                            cur.execute(upsert_sql, (st.session_state.user['user_id'], reason))
                            conn.commit()
                            st.success("제출 완료!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"오류: {e}")
            conn.close()

    # --- 라우팅 ---
    if choice == "🏠 홈 / 도감":
        plant.plant_search_view()
    elif choice == "🌿 내 식물 키우기":
        game.game_view()
    elif choice == "🎓 전문가: 팁 작성":
        expert.expert_view()
    elif choice == "📝 콘텐츠 관리 (식물/경제)":
        content_mgr.content_mgr_view()
    elif choice == "⚙️ 시스템 관리 (계정/로그)":
        admin.admin_view()

    # --- 푸터 ---
    st.markdown("---")
    st.caption("2025 Database Project")
    st.caption("© 부산대학교 정보컴퓨터공학부 202355545 손정훈, 202355625 박소영의 식물도감 app")

if __name__ == "__main__":
    main()