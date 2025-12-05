import streamlit as st
import pandas as pd
from db import get_conn

def dashboard_view():
    """시스템 통계 및 로그"""
    st.subheader("📊 시스템 관리자 대시보드")
    conn = get_conn()
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("**🏆 식물별 졸업률 통계**")
        try:
            df = pd.read_sql("SELECT * FROM plant_completion_stats", conn)
            st.dataframe(df, hide_index=True, use_container_width=True)
            if not df.empty: st.bar_chart(df.set_index("common_name")["completion_rate"])
        except: st.error("View 없음")
        
    with c2:
        st.markdown("**📜 실시간 거래/행동 로그**")
        # 최근 20개 로그 조회
        sql = """
            SELECT l.logged_at, u.login_id, u.name, l.transaction_type, l.amount 
            FROM transaction_log l JOIN user_account u ON l.user_id = u.user_id 
            ORDER BY l.logged_at DESC LIMIT 20
        """
        st.dataframe(pd.read_sql(sql, conn), hide_index=True, use_container_width=True)
    conn.close()

def user_role_management():
    """회원 권한 관리 (전문가 승인 + 관리자 임명)"""
    st.subheader("👥 계정 및 권한 관리")
    conn = get_conn()
    cur = conn.cursor()
    
    # 1. 전문가 승인 대기 목록
    st.markdown("##### 1. 전문가(Expert) 승인 대기")
    cur.execute("""
        SELECT a.user_id, u.name, u.department, a.request_text 
        FROM expert_application a JOIN user_account u ON a.user_id = u.user_id 
        WHERE a.status = 'PENDING'
    """)
    rows = cur.fetchall()
    if rows:
        for r in rows:
            uid, name, dept, txt = r
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.info(f"**{name}({dept})**: {txt}")
            if c2.button("승인", key=f"ok_{uid}"):
                cur.execute("UPDATE expert_application SET status='APPROVED' WHERE user_id=%s", (uid,))
                cur.execute("UPDATE user_account SET role='Expert' WHERE user_id=%s", (uid,))
                conn.commit()
                st.rerun()
            if c3.button("거절", key=f"no_{uid}"):
                cur.execute("UPDATE expert_application SET status='REJECTED' WHERE user_id=%s", (uid,))
                conn.commit()
                st.rerun()
    else:
        st.caption("대기 중인 신청이 없습니다.")

    st.divider()

    # 2. 전체 유저 권한 변경 (관리자/콘텐츠 관리자 임명)
    st.markdown("##### 2. 관리자/콘텐츠 관리자 임명")
    
    # 유저 검색
    target_id = st.text_input("권한을 변경할 유저의 로그인 ID 입력")
    if target_id:
        cur.execute("SELECT user_id, name, role FROM user_account WHERE login_id=%s", (target_id,))
        user = cur.fetchone()
        if user:
            st.write(f"대상: **{user[1]}** (현재 권한: {user[2]})")
            new_role = st.selectbox("변경할 권한 선택", ["User", "Expert", "Content", "Admin"])
            if st.button("권한 변경 실행"):
                cur.execute("UPDATE user_account SET role=%s WHERE user_id=%s", (new_role, user[0]))
                conn.commit()
                st.success(f"{user[1]}님의 권한이 {new_role}(으)로 변경되었습니다.")
                st.rerun()
        else:
            st.error("해당 ID의 유저를 찾을 수 없습니다.")
    conn.close()

def admin_view():
    if st.session_state.user['role'] != 'Admin':
        st.error("최고 관리자(Admin)만 접근 가능합니다.")
        return
    st.header("⚙️ 시스템 관리자(Admin) 페이지")
    t1, t2 = st.tabs(["📊 통계 및 로그", "👥 권한 관리"])
    with t1: dashboard_view()
    with t2: user_role_management()