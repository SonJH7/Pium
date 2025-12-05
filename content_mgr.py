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
    
    # 탭 확장: [식물 정보 수정] 탭 추가됨
    tab_req, tab1, tab1_edit, tab2, tab3, tab4 = st.tabs([
        "📩 신청 내역", 
        "1. 새 식물 등록", 
        "1.5. 식물 정보 수정", 
        "2. 퀴즈 추가", 
        "3. 퀴즈 수정", 
        "🚨 4. 식물 삭제"
    ])
    
    conn = get_conn()
    cursor = conn.cursor()

    # --- 탭 0: 식물 신청 내역 ---
    with tab_req:
        st.info("유저들이 도감에 추가해달라고 요청한 식물 목록입니다.")
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
            st.success("대기 중인 신청이 없습니다.")
        else:
            for req in requests:
                req_id, p_name, u_name, dept, date = req
                with st.expander(f"📌 요청: **{p_name}** (신청자: {u_name})"):
                    st.write(f"- 신청일: {date} | 소속: {dept}")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ 처리 완료", key=f"done_{req_id}"):
                            cursor.execute("UPDATE plant_request SET status='DONE', processed_by=%s WHERE request_id=%s", (st.session_state.user['user_id'], req_id))
                            conn.commit()
                            st.rerun()
                    with c2:
                        if st.button("❌ 거절", key=f"rej_{req_id}"):
                            cursor.execute("UPDATE plant_request SET status='REJECTED', processed_by=%s WHERE request_id=%s", (st.session_state.user['user_id'], req_id))
                            conn.commit()
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
            description = st.text_area("식물 설명", height=150, max_chars=2000)
            
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

    # --- [NEW] 탭 1.5: 식물 정보 수정 ---
    with tab1_edit:
        st.info("이미 등록된 식물의 정보(이름, 설명, 사진 등)를 수정합니다.")
        
        # 식물 선택
        cursor.execute("SELECT species_id, common_name FROM plant_species ORDER BY species_id")
        all_plants = cursor.fetchall()
        p_dict = {p[1]: p[0] for p in all_plants}
        
        if all_plants:
            edit_name = st.selectbox("수정할 식물 선택", list(p_dict.keys()), key="edit_plant_sel")
            edit_pid = p_dict[edit_name]
            
            # 기존 정보 불러오기
            cursor.execute("SELECT common_name, category, difficulty, sun_level, image_url, description FROM plant_species WHERE species_id=%s", (edit_pid,))
            cur_info = cursor.fetchone()
            
            if cur_info:
                # 폼에 기존 값 미리 채워넣기
                with st.form(key="edit_plant_form"):
                    ec1, ec2 = st.columns(2)
                    new_name = ec1.text_input("식물 이름", value=cur_info[0])
                    
                    # Selectbox 인덱스 찾기
                    cats = ["leaf", "flower", "fruit", "succulent"]
                    cat_idx = cats.index(cur_info[1]) if cur_info[1] in cats else 0
                    new_cat = ec2.selectbox("카테고리", cats, index=cat_idx)
                    
                    ec3, ec4 = st.columns(2)
                    new_diff = ec3.slider("게임 난이도", 1, 5, value=cur_info[2])
                    
                    suns = ["Low", "Mid", "High"]
                    sun_idx = suns.index(cur_info[3]) if cur_info[3] in suns else 1
                    new_sun = ec4.selectbox("광량", suns, index=sun_idx)
                    
                    new_img = st.text_input("이미지 URL", value=cur_info[4] if cur_info[4] else "")
                    new_desc = st.text_area("식물 설명", value=cur_info[5] if cur_info[5] else "", height=150)
                    
                    if st.form_submit_button("수정 내용 저장"):
                        try:
                            cursor.execute("""
                                UPDATE plant_species 
                                SET common_name=%s, category=%s, difficulty=%s, sun_level=%s, image_url=%s, description=%s
                                WHERE species_id=%s
                            """, (new_name, new_cat, new_diff, new_sun, new_img, new_desc, edit_pid))
                            conn.commit()
                            st.success(f"'{new_name}' 정보가 수정되었습니다!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"수정 실패: {e}")
        else:
            st.warning("등록된 식물이 없습니다.")

    # --- 탭 2: 퀴즈 추가 ---
    with tab2:
        cursor.execute("SELECT species_id, common_name FROM plant_species ORDER BY species_id DESC")
        plants = cursor.fetchall()
        plant_dict_q = {p[1]: p[0] for p in plants}
        
        if plants:
            sel_name_q = st.selectbox("식물 선택", list(plant_dict_q.keys()), key="add_q_sel")
            sel_pid_q = plant_dict_q[sel_name_q]
            
            with st.form("add_step_form"):
                c1, c2 = st.columns(2)
                step = c1.number_input("단계 순서", min_value=1, value=1)
                stage = c2.text_input("단계 명", "Seed")
                q = st.text_area("질문")
                ans = st.radio("정답", [True, False], format_func=lambda x: "O" if x else "X")
                expl = st.text_input("해설")
                
                if st.form_submit_button("퀴즈 추가"):
                    cursor.execute("INSERT INTO species_step(species_id, step_order, stage_name, quiz_question, correct_answer, explanation) VALUES (%s, %s, %s, %s, %s, %s)", 
                                   (sel_pid_q, step, stage, q, ans, expl))
                    conn.commit()
                    st.success("추가 완료!")

    # --- 탭 3: 퀴즈 수정 ---
    with tab3:
        cursor.execute("SELECT species_id, common_name FROM plant_species ORDER BY species_id")
        all_plants = cursor.fetchall()
        p_dict_eq = {p[1]: p[0] for p in all_plants}
        
        if all_plants:
            target_name = st.selectbox("수정할 식물", list(p_dict_eq.keys()), key="edit_q_sel")
            target_pid = p_dict_eq[target_name]
            
            cursor.execute("SELECT step_id, step_order, stage_name, quiz_question, correct_answer, explanation FROM species_step WHERE species_id = %s ORDER BY step_order", (target_pid,))
            steps = cursor.fetchall()
            
            if steps:
                step_options = {f"{s[1]}단계 ({s[2]})": s for s in steps}
                sel_key = st.selectbox("수정할 단계", list(step_options.keys()))
                sel_data = step_options[sel_key]
                s_id = sel_data[0]
                
                with st.form(key=f"edit_q_form_{s_id}"):
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
        st.warning("⚠️ 주의: 식물 삭제 시 관련 유저 데이터와 퀴즈가 모두 사라집니다.")
        cursor.execute("SELECT species_id, common_name FROM plant_species ORDER BY species_id")
        all_plants_del = cursor.fetchall()
        del_dict = {p[1]: p[0] for p in all_plants_del}
        
        if all_plants_del:
            del_name = st.selectbox("삭제할 식물 선택", list(del_dict.keys()), key="del_plant_sel")
            del_pid = del_dict[del_name]
            
            cursor.execute("SELECT COUNT(*) FROM user_plant WHERE species_id = %s", (del_pid,))
            active_users = cursor.fetchone()[0]
            
            if active_users > 0:
                st.error(f"🚨 현재 {active_users}명이 키우는 중입니다!")
            
            st.divider()

            if st.button("삭제하기", type="primary"):
                st.session_state['delete_confirm_pid'] = del_pid
            
            if st.session_state.get('delete_confirm_pid') == del_pid:
                st.error(f"정말로 '{del_name}' 데이터를 영구 삭제하시겠습니까?")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("네, 삭제합니다", type="primary"):
                        cursor.execute("DELETE FROM plant_species WHERE species_id = %s", (del_pid,))
                        conn.commit()
                        st.success("삭제 완료")
                        st.session_state['delete_confirm_pid'] = None
                        st.rerun()
                with c2:
                    if st.button("취소"):
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