import streamlit as st
import auth
import plant
import game
import expert
import admin

def init_session():
    """세션 초기화: 새로고침 해도 로그인 데이터가 유지되도록 설정"""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "show_auth" not in st.session_state:
        st.session_state.show_auth = False

def main():
    # 1. 페이지 기본 설정
    st.set_page_config(
        page_title="P-Plant: 대학생 식물 키우기", 
        layout="wide", 
        page_icon="🌱"
    )
    init_session()

    # 2. 상단 헤더 영역 (제목 + 로그인 정보)
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("🌱 P-Plant: 인터랙티브 식물 도감")
        st.caption("식물을 검색하고, 퀴즈를 풀며 내 정원을 가꿔보세요!")
    
    with col2:
        # 로그인 상태가 아닐 때
        if st.session_state.user is None:
            if st.button("로그인 / 회원가입", use_container_width=True):
                st.session_state.show_auth = True
        
        # 로그인 상태일 때
        else:
            u = st.session_state.user
            # 대학생 프로젝트답게 학번/학과 표시
            st.success(f"👤 {u['name']}님 ({u['department']})")
            st.markdown(f"**학번:** {u['student_id']} | **포인트:** {u['points']} P")
            
            if st.button("로그아웃", use_container_width=True):
                st.session_state.user = None
                st.rerun()

    st.markdown("---")

    # 3. 로그인/회원가입 모달 처리
    if st.session_state.show_auth:
        auth.auth_view()
        return  # 로그인 창이 떠있으면 아래 메인 화면은 가림

    # 4. 사이드바 메뉴 구성
    st.sidebar.header("메뉴 선택")
    
    # 기본 메뉴
    menu_options = ["🏠 홈 / 도감 검색"]
    
    # 로그인한 유저만 보이는 메뉴
    if st.session_state.user:
        role = st.session_state.user["role"]
        menu_options.append("🌿 내 식물 키우기 (게임)")
        
        # 전문가/관리자 전용 메뉴 (권한별 분기)
        if role in ["Expert", "Admin"]:
            menu_options.append("🎓 전문가 페이지")
        if role in ["Admin"]:
            menu_options.append("⚙️ 관리자 설정")

    choice = st.sidebar.radio("이동할 페이지를 선택하세요", menu_options)

    # --- 전문가 신청 기능 (거절된 경우 재신청 가능) ---
    if st.session_state.user and st.session_state.user['role'] == 'User':
        st.sidebar.markdown("---")
        with st.sidebar.expander("🎓 전문가 등급 신청"):
            
            conn = auth.get_conn()
            cur = conn.cursor()
            
            # 1. 현재 신청 상태 확인
            cur.execute("SELECT status FROM expert_application WHERE user_id=%s", (st.session_state.user['user_id'],))
            row = cur.fetchone()
            
            can_apply = True
            
            # 이미 신청 기록이 있는 경우 상태 체크
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
                    # can_apply는 True로 유지 (재신청 허용)

            # 2. 신청 폼 (신청 가능할 때만 보임)
            if can_apply:
                with st.form("expert_apply_form"):
                    st.write("식물에 대한 전문 지식이 있으신가요?")
                    reason = st.text_area("신청 사유", height=100, placeholder="예: 원예학과 4학년, 식물 관리사 자격증 보유 등")
                    submitted = st.form_submit_button("신청서 제출")
                    
                    if submitted and reason:
                        try:
                            # 3. UPSERT 쿼리 (없으면 INSERT, 있으면 상태를 PENDING으로 UPDATE)
                            upsert_sql = """
                                INSERT INTO expert_application (user_id, request_text, status, decided_at)
                                VALUES (%s, %s, 'PENDING', NULL)
                                ON CONFLICT (user_id) 
                                DO UPDATE SET 
                                    request_text = EXCLUDED.request_text,
                                    status = 'PENDING',
                                    decided_at = NULL;
                            """
                            cur.execute(upsert_sql, (st.session_state.user['user_id'], reason))
                            conn.commit()
                            st.success("제출 완료! 관리자 승인을 기다려주세요.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"오류: {e}")
            
            conn.close()
    # --------------------------------------------------------

    # 5. 페이지 라우팅 (선택한 메뉴에 따라 화면 표시)
    if choice == "🏠 홈 / 도감 검색":
        # plant.py의 함수 호출
        plant.plant_search_view()
        
    elif choice == "🌿 내 식물 키우기 (게임)":
        # game.py의 함수 호출
        game.game_view()
        
    elif choice == "🎓 전문가 페이지":
        st.subheader("🎓 전문가 전용 페이지")
        st.info("이 기능은 전문가(Expert) 권한을 가진 사용자만 접근 가능합니다.")
        expert.expert_view()
        
    elif choice == "⚙️ 관리자 설정":
        st.subheader("⚙️ 시스템 관리자 페이지")
        st.info("관리자(Admin) 권한을 가진 사용자만 접근 가능합니다.")
        admin.admin_view()    

    # 6. 하단 푸터 (선택 사항)
    st.markdown("---")
    st.caption("2025 Database Project")
    st.caption("© 부산대학교 정보컴퓨터공학부 202355545 손정훈,202355625 박소영의 식물도감 app")

if __name__ == "__main__":
    main()