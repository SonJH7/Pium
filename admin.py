import streamlit as st
import pandas as pd
from db import get_conn

def dashboard_view():
    """1. 대시보드: 시스템 통계 및 로그 확인"""
    st.subheader("📊 시스템 현황 대시보드")
    conn = get_conn()
    col1, col2 = st.columns(2)
    
    # 식물별 졸업률
    with col1:
        st.markdown("**식물별 완주(졸업) 현황**")
        try:
            df_stats = pd.read_sql("SELECT common_name, total_users, completed_users, completion_rate FROM plant_completion_stats", conn)
            st.dataframe(df_stats, hide_index=True, use_container_width=True)
            if not df_stats.empty:
                st.bar_chart(df_stats.set_index("common_name")["completion_rate"])
        except Exception:
            st.error("통계 View를 불러올 수 없습니다.")

    # 최근 포인트 로그
    with col2:
        st.markdown("**최근 포인트 트랜잭션**")
        sql_log = """
            SELECT l.logged_at, u.name, l.transaction_type, l.amount 
            FROM transaction_log l
            JOIN user_account u ON l.user_id = u.user_id
            ORDER BY l.logged_at DESC LIMIT 10
        """
        try:
            df_log = pd.read_sql(sql_log, conn)
            st.dataframe(df_log, hide_index=True, use_container_width=True)
        except Exception:
            st.error("로그 조회 실패")
    conn.close()

def user_management_view():
    """2. 회원 관리: 전문가 신청 승인/거절"""
    st.subheader("👥 전문가 신청 관리")
    conn = get_conn()
    cursor = conn.cursor()
    
    sql = """
        SELECT a.user_id, u.name, u.department, u.student_id, a.request_text, a.status
        FROM expert_application a
        JOIN user_account u ON a.user_id = u.user_id
        WHERE a.status = 'PENDING'
    """
    cursor.execute(sql)
    requests = cursor.fetchall()
    
    if not requests:
        st.info("대기 중인 전문가 신청이 없습니다.")
    else:
        for req in requests:
            uid, name, dept, sid, text, status = req
            with st.expander(f"신청자: {name} ({dept})"):
                st.write(f"**사유**: {text}")
                c1, c2 = st.columns(2)
                if c1.button("승인", key=f"app_{uid}"):
                    cursor.execute("UPDATE expert_application SET status='APPROVED', decided_at=NOW() WHERE user_id=%s", (uid,))
                    cursor.execute("UPDATE user_account SET role='Expert' WHERE user_id=%s", (uid,))
                    conn.commit()
                    st.success("승인 완료!")
                    st.rerun()
                if c2.button("거절", key=f"rej_{uid}"):
                    cursor.execute("UPDATE expert_application SET status='REJECTED', decided_at=NOW() WHERE user_id=%s", (uid,))
                    conn.commit()
                    st.warning("거절 완료.")
                    st.rerun()
    conn.close()

def content_management_view():
    """3. 콘텐츠 관리: 식물/퀴즈 등록 + [수정 기능 추가]"""
    st.subheader("🌱 식물 및 퀘스트 데이터 관리")
    
    # 탭을 3개로 늘렸습니다.
    tab1, tab2, tab3 = st.tabs(["1단계: 새 식물 등록", "2단계: 퀴즈 추가", "3단계: 퀴즈 조회/수정"])
    
    conn = get_conn()
    cursor = conn.cursor()

    # --- 탭 1: 식물 등록 (기존 동일) ---
    with tab1:
        with st.form("new_plant_form"):
            st.write("새로운 식물 종 추가")
            c1, c2 = st.columns(2)
            name = c1.text_input("식물 이름")
            cat = c2.selectbox("카테고리", ["leaf", "flower", "fruit", "succulent"])
            c3, c4 = st.columns(2)
            diff = c3.slider("난이도", 1, 5, 2)
            sun = c4.selectbox("광조", ["Low", "Mid", "High"])
            img_url = st.text_input("이미지 URL")
            
            if st.form_submit_button("식물 등록"):
                if name:
                    try:
                        cursor.execute("INSERT INTO plant_species(common_name, category, difficulty, sun_level, image_url) VALUES (%s, %s, %s, %s, %s)", 
                                       (name, cat, diff, sun, img_url))
                        conn.commit()
                        st.success(f"'{name}' 등록 성공!")
                    except Exception as e:
                        st.error(f"오류: {e}")

    # --- 탭 2: 퀴즈 추가 (기존 동일) ---
    with tab2:
        st.info("기존 식물에 새로운 단계를 추가합니다.")
        cursor.execute("SELECT species_id, common_name FROM plant_species ORDER BY species_id DESC")
        plants = cursor.fetchall()
        plant_dict = {p[1]: p[0] for p in plants}
        
        if plants:
            sel_name = st.selectbox("식물 선택 (추가)", list(plant_dict.keys()), key="add_q_sel")
            sel_pid = plant_dict[sel_name]
            
            with st.form("add_step_form"):
                c1, c2 = st.columns(2)
                step = c1.number_input("단계 순서", min_value=1, value=1)
                stage = c2.text_input("단계 명", "Seed")
                q = st.text_area("질문")
                ans = st.radio("정답", [True, False], format_func=lambda x: "O" if x else "X")
                expl = st.text_input("해설")
                
                if st.form_submit_button("퀴즈 추가"):
                    try:
                        cursor.execute("INSERT INTO species_step(species_id, step_order, stage_name, quiz_question, correct_answer, explanation) VALUES (%s, %s, %s, %s, %s, %s)", 
                                       (sel_pid, step, stage, q, ans, expl))
                        conn.commit()
                        st.success("추가 완료!")
                    except Exception as e:
                        st.error(f"오류: {e}")
        else:
            st.warning("식물부터 등록하세요.")

    # --- [NEW] 탭 3: 퀴즈 조회 및 수정 ---
    with tab3:
        st.info("등록된 퀴즈를 확인하고 내용을 수정합니다.")
        
        # 1. 식물 선택
        cursor.execute("SELECT species_id, common_name FROM plant_species ORDER BY species_id")
        all_plants = cursor.fetchall()
        p_dict = {p[1]: p[0] for p in all_plants}
        
        if all_plants:
            target_name = st.selectbox("수정할 식물 선택", list(p_dict.keys()), key="edit_q_sel")
            target_pid = p_dict[target_name]
            
            # 2. 해당 식물의 퀴즈 목록 조회
            sql_steps = """
                SELECT step_id, step_order, stage_name, quiz_question, correct_answer, explanation 
                FROM species_step 
                WHERE species_id = %s 
                ORDER BY step_order
            """
            cursor.execute(sql_steps, (target_pid,))
            steps = cursor.fetchall()
            
            if steps:
                # 3. 데이터프레임으로 목록 보여주기
                df_steps = pd.DataFrame(steps, columns=["ID", "단계", "이름", "질문", "정답", "해설"])
                # 정답 boolean을 O/X로 변환해서 보여주기
                df_steps["정답"] = df_steps["정답"].apply(lambda x: "O" if x else "X")
                st.dataframe(df_steps, hide_index=True, use_container_width=True)
                
                st.divider()
                st.write("🔽 **수정할 단계 선택**")
                
                # 4. 수정할 Step 선택 (Selectbox)
                step_options = {f"{s[1]}단계 ({s[2]})": s for s in steps}
                selected_step_key = st.selectbox("어떤 퀴즈를 수정하시겠습니까?", list(step_options.keys()))
                
                # 선택된 데이터 가져오기
                # s구조: (step_id, step_order, stage_name, quiz_question, correct_answer, explanation)
                sel_data = step_options[selected_step_key]
                s_id = sel_data[0]
                
                # 5. 수정 폼 (기존 데이터 채워넣기)
                with st.form(key=f"edit_form_{s_id}"):
                    ec1, ec2 = st.columns(2)
                    new_order = ec1.number_input("단계 순서", value=sel_data[1], min_value=1)
                    new_stage = ec2.text_input("단계 이름", value=sel_data[2])
                    new_q = st.text_area("질문 수정", value=sel_data[3])
                    
                    # 기존 정답이 True면 index 0('O'), False면 index 1('X')
                    default_idx = 0 if sel_data[4] else 1
                    new_ans = st.radio("정답 수정", [True, False], index=default_idx, format_func=lambda x: "O" if x else "X")
                    
                    new_expl = st.text_input("해설 수정", value=sel_data[5])
                    
                    if st.form_submit_button("수정 내용 저장"):
                        try:
                            update_sql = """
                                UPDATE species_step 
                                SET step_order=%s, stage_name=%s, quiz_question=%s, correct_answer=%s, explanation=%s
                                WHERE step_id=%s
                            """
                            cursor.execute(update_sql, (new_order, new_stage, new_q, new_ans, new_expl, s_id))
                            conn.commit()
                            st.success("수정되었습니다!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"수정 실패: {e}")
            else:
                st.warning("이 식물에는 아직 등록된 퀴즈가 없습니다.")
        else:
            st.warning("등록된 식물이 없습니다.")

    conn.close()

def admin_view():
    if st.session_state.user['role'] != 'Admin':
        st.error("관리자 권한이 필요합니다.")
        return

    st.header("⚙️ 시스템 관리자 페이지")
    tab1, tab2, tab3 = st.tabs(["📊 대시보드", "👥 회원/권한 관리", "🌱 식물/퀴즈 데이터 관리"])
    
    with tab1: dashboard_view()
    with tab2: user_management_view()
    with tab3: content_management_view()