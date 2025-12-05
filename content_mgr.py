import streamlit as st
import pandas as pd
from db import get_conn

def manage_game_config():
    """경제 파라미터 조정"""
    st.markdown("#### 💰 경제 시스템 설정")
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT config_key, config_value FROM game_config")
    configs = dict(cur.fetchall())
    
    with st.form("config_form"):
        col1, col2 = st.columns(2)
        revive_cost = col1.number_input("이어하기 비용", value=int(configs.get('revive_cost', 500)))
        quiz_reward = col2.number_input("퀴즈 보상", value=int(configs.get('quiz_reward', 100)))
        
        if st.form_submit_button("설정 저장"):
            cur.execute("UPDATE game_config SET config_value=%s WHERE config_key='revive_cost'", (str(revive_cost),))
            cur.execute("UPDATE game_config SET config_value=%s WHERE config_key='quiz_reward'", (str(quiz_reward),))
            conn.commit()
            st.success("저장 완료!")
    conn.close()

def manage_plants_and_quizzes():
    """식물 및 퀴즈 데이터 CRUD + 식물 신청 관리"""
    st.markdown("#### 🌱 식물 및 퀘스트 데이터 관리")
    
    # 탭을 5개로 확장 (맨 앞에 신청 내역 탭 추가)
    tab_req, tab1, tab2, tab3, tab4 = st.tabs(["📩 식물 신청 내역", "1단계: 새 식물 등록", "2단계: 퀴즈 추가", "3단계: 퀴즈 수정", "🚨 4단계: 식물 삭제"])
    
    conn = get_conn()
    cursor = conn.cursor()

    # --- [NEW] 탭 0: 유저들의 식물 신청 내역 ---
    with tab_req:
        st.info("유저들이 도감에 추가해달라고 요청한 식물 목록입니다.")
        
        # PENDING 상태인 요청만 조회 (최신순)
        sql_req = """
            SELECT r.request_id, r.plant_name, u.name, u.department, r.created_at
            FROM plant_request r
            JOIN user_account u ON r.requester_id = u.user_id
            WHERE r.status = 'PENDING'
            ORDER BY r.created_at DESC
        """
        cursor.execute(sql_req)
        requests = cursor.fetchall()
        
        if not requests:
            st.success("대기 중인 신청이 없습니다. (모두 처리됨)")
        else:
            for req in requests:
                req_id, p_name, u_name, dept, date = req
                
                with st.expander(f"📌 요청: **{p_name}** (신청자: {u_name})"):
                    st.write(f"- 신청일: {date}")
                    st.write(f"- 소속: {dept}")
                    st.caption("이 식물을 '1단계: 새 식물 등록' 탭에서 등록한 후, 아래 완료 버튼을 눌러주세요.")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ 처리 완료 (등록함)", key=f"done_req_{req_id}"):
                            # 상태를 DONE으로 변경, 처리자(현재 로그인한 관리자) 기록
                            cursor.execute("""
                                UPDATE plant_request 
                                SET status='DONE', processed_by=%s 
                                WHERE request_id=%s
                            """, (st.session_state.user['user_id'], req_id))
                            conn.commit()
                            st.success(f"'{p_name}' 요청을 처리 완료했습니다.")
                            st.rerun()
                            
                    with c2:
                        if st.button("❌ 거절 (반려)", key=f"rej_req_{req_id}"):
                            cursor.execute("""
                                UPDATE plant_request 
                                SET status='REJECTED', processed_by=%s 
                                WHERE request_id=%s
                            """, (st.session_state.user['user_id'], req_id))
                            conn.commit()
                            st.warning("요청을 거절했습니다.")
                            st.rerun()

    # --- 탭 1: 식물 등록 ---
    with tab1:
        with st.form("new_plant_form"):
            st.write("새로운 식물 종을 도감에 추가합니다.")
            c1, c2 = st.columns(2)
            name = c1.text_input("식물 이름")
            cat = c2.selectbox("카테고리", ["leaf", "flower", "fruit", "succulent"])
            c3, c4 = st.columns(2)
            diff = c3.slider("게임 난이도", 1, 5, 2)
            sun = c4.selectbox("광량", ["Low", "Mid", "High"])
            img_url = st.text_input("이미지 URL")
            
            st.markdown("**📖 식물 도감 상세 정보**")
            description = st.text_area("식물 설명 (특징, 유래, 관리법 등)", height=150, max_chars=2000)
            
            if st.form_submit_button("식물 등록"):
                try:
                    cursor.execute("""
                        INSERT INTO plant_species(common_name, category, difficulty, sun_level, image_url, description) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (name, cat, diff, sun, img_url, description))
                    conn.commit()
                    st.success(f"'{name}' 등록 성공!")
                except Exception as e:
                    st.error(f"오류: {e}")

    # --- 탭 2: 퀴즈 추가 ---
    with tab2:
        cursor.execute("SELECT species_id, common_name FROM plant_species ORDER BY species_id DESC")
        plants = cursor.fetchall()
        plant_dict = {p[1]: p[0] for p in plants}
        
        if plants:
            sel_name = st.selectbox("식물 선택", list(plant_dict.keys()), key="add_q_sel")
            sel_pid = plant_dict[sel_name]
            
            with st.form("add_step_form"):
                c1, c2 = st.columns(2)
                step = c1.number_input("단계 순서", min_value=1, value=1)
                stage = c2.text_input("단계 명", "Seed")
                q = st.text_area("질문")
                ans = st.radio("정답", [True, False], format_func=lambda x: "O" if x else "X")
                expl = st.text_input("해설")
                
                if st.form_submit_button("퀴즈 추가"):
                    cursor.execute("INSERT INTO species_step(species_id, step_order, stage_name, quiz_question, correct_answer, explanation) VALUES (%s, %s, %s, %s, %s, %s)", 
                                   (sel_pid, step, stage, q, ans, expl))
                    conn.commit()
                    st.success("추가 완료!")

    # --- 탭 3: 퀴즈 수정 ---
    with tab3:
        cursor.execute("SELECT species_id, common_name FROM plant_species ORDER BY species_id")
        all_plants = cursor.fetchall()
        p_dict = {p[1]: p[0] for p in all_plants}
        
        if all_plants:
            target_name = st.selectbox("수정할 식물", list(p_dict.keys()), key="edit_q_sel")
            target_pid = p_dict[target_name]
            
            cursor.execute("SELECT step_id, step_order, stage_name, quiz_question, correct_answer, explanation FROM species_step WHERE species_id = %s ORDER BY step_order", (target_pid,))
            steps = cursor.fetchall()
            
            if steps:
                step_options = {f"{s[1]}단계 ({s[2]})": s for s in steps}
                sel_key = st.selectbox("수정할 단계", list(step_options.keys()))
                sel_data = step_options[sel_key]
                s_id = sel_data[0]
                
                with st.form(key=f"edit_form_{s_id}"):
                    ec1, ec2 = st.columns(2)
                    new_order = ec1.number_input("단계", value=sel_data[1], min_value=1)
                    new_stage = ec2.text_input("이름", value=sel_data[2])
                    new_q = st.text_area("질문", value=sel_data[3])
                    def_idx = 0 if sel_data[4] else 1
                    new_ans = st.radio("정답", [True, False], index=def_idx, format_func=lambda x: "O" if x else "X")
                    new_expl = st.text_input("해설", value=sel_data[5])
                    
                    if st.form_submit_button("수정 저장"):
                        cursor.execute("UPDATE species_step SET step_order=%s, stage_name=%s, quiz_question=%s, correct_answer=%s, explanation=%s WHERE step_id=%s", 
                                       (new_order, new_stage, new_q, new_ans, new_expl, s_id))
                        conn.commit()
                        st.success("수정됨!")
                        st.rerun()

    # --- 탭 4: 식물 삭제 ---
    with tab4:
        st.warning("⚠️ 주의: 식물을 삭제하면 해당 식물을 키우던 모든 사용자의 데이터와 퀴즈 기록이 영구적으로 사라집니다.")
        
        cursor.execute("SELECT species_id, common_name FROM plant_species ORDER BY species_id")
        all_plants_del = cursor.fetchall()
        del_dict = {p[1]: p[0] for p in all_plants_del}
        
        if all_plants_del:
            del_name = st.selectbox("삭제할 식물 선택", list(del_dict.keys()), key="del_plant_sel")
            del_pid = del_dict[del_name]
            
            cursor.execute("SELECT COUNT(*) FROM user_plant WHERE species_id = %s", (del_pid,))
            active_users = cursor.fetchone()[0]
            
            if active_users > 0:
                st.error(f"🚨 현재 {active_users}명의 사용자가 이 식물을 키우고 있습니다!")
            else:
                st.info("현재 이 식물을 키우는 사용자는 없습니다.")

            st.divider()

            if st.button("삭제하기", type="primary"):
                st.session_state['delete_confirm_pid'] = del_pid
            
            if st.session_state.get('delete_confirm_pid') == del_pid:
                st.markdown(f"""
                <div style="background-color: #ffebee; padding: 20px; border-radius: 10px; border: 1px solid #ef9a9a;">
                    <h4 style="color: #c62828;">💣 정말로 삭제하시겠습니까?</h4>
                    <p><b>'{del_name}'</b> 데이터와 관련된 <b>모든 유저의 성장 기록</b>이 즉시 삭제됩니다.<br>
                    작업은 되돌릴 수 없습니다.</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    if st.button("네, 모든 데이터를 지우겠습니다", type="primary"):
                        try:
                            cursor.execute("DELETE FROM plant_species WHERE species_id = %s", (del_pid,))
                            conn.commit()
                            st.success(f"'{del_name}' 삭제가 완료되었습니다.")
                            st.session_state['delete_confirm_pid'] = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"삭제 실패: {e}")
                
                with col_d2:
                    if st.button("취소 (유지)"):
                        st.session_state['delete_confirm_pid'] = None
                        st.rerun()

    conn.close()

def content_mgr_view():
    if st.session_state.user['role'] not in ['Content', 'Admin']:
        st.error("권한이 없습니다.")
        return

    st.header("📝 콘텐츠 관리자 페이지")
    tab1, tab2 = st.tabs(["🌱 식물/퀴즈 데이터", "💰 게임 경제 설정"])
    
    with tab1: manage_plants_and_quizzes()
    with tab2: manage_game_config()