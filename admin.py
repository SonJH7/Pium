import streamlit as st
import pandas as pd
from db import get_conn

def dashboard_view():
    """시스템 통계 및 로그 (View 활용 강화)"""
    st.subheader("📊 시스템 현황 대시보드")
    conn = get_conn()
    
    # 탭을 나눠서 SQL View 활용 능력을 각각 보여줌
    t1, t2, t3 = st.tabs(["🏆 졸업률 & 로그", "💰 포인트 분포", "🏫 학과별 활동(Having)"])
    
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**🌱 식물별 완주(졸업) 현황**")
            try:
                # View: plant_completion_stats
                df_stats = pd.read_sql("SELECT * FROM plant_completion_stats", conn)
                st.dataframe(df_stats, hide_index=True, use_container_width=True)
                if not df_stats.empty:
                    # 완주율 바 차트
                    st.bar_chart(df_stats.set_index("common_name")["completion_rate"])
            except: 
                st.error("View 조회 실패 (plant_completion_stats)")

        with c2:
            st.markdown("**📜 최근 포인트 로그**")
            sql_log = """
                SELECT l.logged_at, u.name, l.transaction_type, l.amount 
                FROM transaction_log l JOIN user_account u ON l.user_id = u.user_id
                ORDER BY l.logged_at DESC LIMIT 10
            """
            st.dataframe(pd.read_sql(sql_log, conn), hide_index=True, use_container_width=True)

    with t2:
        st.markdown("**💰 사용자 포인트 보유 분포 (Histogram)**")
        st.caption("경제 밸런스 확인용 (View: point_distribution)")
        try:
            # View: point_distribution
            df_point = pd.read_sql("SELECT * FROM point_distribution", conn)
            
            col_a, col_b = st.columns([2, 1])
            with col_a:
                if not df_point.empty:
                    # X축: 포인트 구간, Y축: 유저 수
                    st.bar_chart(df_point.set_index("bucket_start")["user_count"])
                else:
                    st.info("데이터가 충분하지 않습니다.")
            with col_b:
                st.dataframe(df_point, hide_index=True, use_container_width=True)
        except: 
            st.error("View 조회 실패 (point_distribution)")

    with t3:
        st.markdown("**🏫 활성 학과 통계 (Active Departments)**")
        st.caption("활동 유저가 1명 이상인 학과만 조회 (GROUP BY + HAVING 적용 View)")
        try:
            # View: active_department_stats (HAVING 절 적용됨)
            df_dept = pd.read_sql("SELECT * FROM active_department_stats ORDER BY avg_points DESC", conn)
            st.dataframe(df_dept, use_container_width=True)
            
            if not df_dept.empty:
                st.markdown("##### 학과별 평균 포인트")
                st.bar_chart(df_dept.set_index("department")["avg_points"])
        except: 
            st.error("View 조회 실패 (active_department_stats)")

    conn.close()

def user_role_management():
    """회원 권한 관리 (전문가 승인 + 관리자 임명)"""
    st.subheader("👥 계정 및 권한 관리")
    conn = get_conn()
    cur = conn.cursor()
    
    # 1. 전문가 승인 대기 목록
    st.markdown("##### 1. 전문가(Expert) 승인 대기")
    cur.execute("""
        SELECT a.user_id, u.name, u.department, u.student_id, a.request_text, a.status
        FROM expert_application a JOIN user_account u ON a.user_id = u.user_id
        WHERE a.status = 'PENDING'
    """)
    rows = cur.fetchall()
    
    if rows:
        for r in rows:
            uid, name, dept, sid, txt, status = r
            with st.expander(f"신청자: {name} ({dept})"):
                st.write(f"**학번**: {sid}")
                st.write(f"**사유**: {txt}")
                c1, c2 = st.columns(2)
                if c1.button("승인", key=f"ok_{uid}"):
                    cur.execute("UPDATE expert_application SET status='APPROVED', decided_at=NOW() WHERE user_id=%s", (uid,))
                    cur.execute("UPDATE user_account SET role='Expert' WHERE user_id=%s", (uid,))
                    conn.commit()
                    st.success("승인 완료!")
                    st.rerun()
                if c2.button("거절", key=f"no_{uid}"):
                    cur.execute("UPDATE expert_application SET status='REJECTED', decided_at=NOW() WHERE user_id=%s", (uid,))
                    conn.commit()
                    st.warning("거절 완료.")
                    st.rerun()
    else:
        st.info("대기 중인 전문가 신청이 없습니다.")

    st.divider()

    # 2. 전체 유저 권한 변경 (관리자/콘텐츠 관리자 임명)
    st.markdown("##### 2. 관리자/콘텐츠 관리자 임명")
    
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
    
    # 탭으로 화면 구성
    tab1, tab2 = st.tabs(["📊 대시보드 (통계/로그)", "👥 회원/권한 관리"])
    
    with tab1:
        dashboard_view()
    with tab2:
        user_role_management()