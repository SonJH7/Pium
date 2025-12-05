import streamlit as st
import pandas as pd
from db import get_conn

def insert_audit_log(cursor, admin_id, action_type, target_id, details):
    """
    [공통] 감사 로그 기록용 헬퍼 함수
    모든 중요 변경 사항을 audit_log 테이블에 기록합니다.
    """
    cursor.execute("""
        INSERT INTO audit_log (admin_id, action_type, target_id, details)
        VALUES (%s, %s, %s, %s)
    """, (admin_id, action_type, target_id, details))

def manage_game_config():
    """1. 경제 파라미터 조정 + 로그 기록"""
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
            try:
                cur.execute("UPDATE game_config SET config_value=%s WHERE config_key='revive_cost'", (str(revive_cost),))
                cur.execute("UPDATE game_config SET config_value=%s WHERE config_key='quiz_reward'", (str(quiz_reward),))
                
                # 로그 기록
                insert_audit_log(cur, st.session_state.user['user_id'], 'UPDATE_CONFIG', 0, 
                               f"이어하기:{revive_cost}, 보상:{quiz_reward}로 변경")
                
                conn.commit()
                st.success("설정이 저장되었습니다. (감사 로그 기록됨)")
            except Exception as e:
                conn.rollback()
                st.error(f"오류: {e}")
    conn.close()

def manage_tips_moderation():
    """2. [NEW] 부적절한 팁 숨김 처리 (신고 관리)"""
    st.markdown("#### 🚨 게시물 모니터링 및 숨김 처리")
    st.caption("유해하거나 부적절한 전문가 팁을 숨김 처리(Blind)합니다.")
    
    conn = get_conn()
    cur = conn.cursor()
    
    # 팁 목록 조회 (작성자 정보 포함)
    sql = """
        SELECT t.tip_id, s.common_name, t.title, t.content, u.name, t.is_hidden, t.created_at
        FROM expert_tip t
        JOIN plant_species s ON t.species_id = s.species_id
        JOIN user_account u ON t.expert_id = u.user_id
        ORDER BY t.created_at DESC
    """
    cur.execute(sql)
    tips = cur.fetchall()
    
    if not tips:
        st.info("등록된 팁이 없습니다.")
    else:
        for tip in tips:
            tid, pname, title, content, writer, is_hidden, date = tip
            
            # 디자인: 숨겨진 글은 회색조 배경
            box_style = "background-color: #f0f2f6; opacity: 0.7;" if is_hidden else "background-color: #ffffff;"
            status_badge = "🚫 [숨김 상태]" if is_hidden else "✅ [게시 중]"
            
            with st.container():
                st.markdown(f"""
                <div style="{box_style} padding: 15px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 10px;">
                    <small>{status_badge} | {pname} | 작성자: {writer} ({date})</small>
                    <h5 style="margin: 5px 0;">{title}</h5>
                    <p>{content}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 6])
                with col1:
                    if is_hidden:
                        if st.button("복구 (공개)", key=f"unhide_{tid}"):
                            try:
                                cur.execute("UPDATE expert_tip SET is_hidden=FALSE WHERE tip_id=%s", (tid,))
                                insert_audit_log(cur, st.session_state.user['user_id'], 'UNHIDE_TIP', tid, f"팁 복구: {title}")
                                conn.commit()
                                st.rerun()
                            except Exception as e: st.error(e)
                    else:
                        if st.button("⛔ 숨기기", key=f"hide_{tid}", type="primary"):
                            try:
                                cur.execute("UPDATE expert_tip SET is_hidden=TRUE WHERE tip_id=%s", (tid,))
                                insert_audit_log(cur, st.session_state.user['user_id'], 'HIDE_TIP', tid, f"부적절한 팁 숨김: {title}")
                                conn.commit()
                                st.rerun()
                            except Exception as e: st.error(e)
    conn.close()

def view_audit_logs():
    """3. [NEW] 감사 로그 조회"""
    st.markdown("#### 📜 감사 로그 (Audit Log)")
    st.caption("관리자의 모든 중요 활동(수정, 숨김, 삭제 등)이 기록됩니다.")
    
    conn = get_conn()
    # 최신 로그 50개 조회
    sql = """
        SELECT l.log_id, u.name AS admin_name, u.department, l.action_type, l.details, l.created_at
        FROM audit_log l
        JOIN user_account u ON l.admin_id = u.user_id
        ORDER BY l.created_at DESC
        LIMIT 50
    """
    try:
        df = pd.read_sql(sql, conn)
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error("로그 테이블이 없거나 조회 실패. (DB에 audit_log 테이블을 생성했는지 확인하세요)")
    finally:
        conn.close()

def manage_plants_and_quizzes():
    """4. 식물 및 퀴즈 데이터 CRUD (모든 작업에 로그 기록 추가됨)"""
    st.markdown("#### 🌱 식물 및 퀘스트 데이터 관리")
    
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
        st.info("유저들이 요청한 식물 목록입니다. 등록 후 '완료' 처리를 해주세요.")
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
                            # 상태 변경 + 로그 기록
                            cursor.execute("UPDATE plant_request SET status='DONE', processed_by=%s WHERE request_id=%s", 
                                         (st.session_state.user['user_id'], req_id))
                            insert_audit_log(cursor, st.session_state.user['user_id'], 'REQ_DONE', req_id, f"요청 처리 완료: {p_name}")
                            conn.commit()
                            st.success("처리되었습니다.")
                            st.rerun()
                    with c2:
                        if st.button("❌ 거절", key=f"rej_{req_id}"):
                            cursor.execute("UPDATE plant_request SET status='REJECTED', processed_by=%s WHERE request_id=%s", 
                                         (st.session_state.user['user_id'], req_id))
                            insert_audit_log(cursor, st.session_state.user['user_id'], 'REQ_REJECT', req_id, f"요청 반려: {p_name}")
                            conn.commit()
                            st.warning("거절되었습니다.")
                            st.rerun()

    # --- 탭 1: 식물 등록 ---
    with tab1:
        with st.form("new_plant_form"):
            st.write("새 식물 등록")
            c1, c2 = st.columns(2)
            name = c1.text_input("식물 이름")
            cat = c2.selectbox("카테고리", ["leaf", "flower", "fruit", "succulent"])
            c3, c4 = st.columns(2)
            diff = c3.slider("게임 난이도", 1, 5, 2)
            sun = c4.selectbox("광량", ["Low", "Mid", "High"])
            img_url = st.text_input("이미지 URL")
            desc = st.text_area("식물 설명", height=100)
            
            if st.form_submit_button("식물 등록"):
                try:
                    cursor.execute("""
                        INSERT INTO plant_species(common_name, category, difficulty, sun_level, image_url, description) 
                        VALUES (%s, %s, %s, %s, %s, %s) RETURNING species_id
                    """, (name, cat, diff, sun, img_url, desc))
                    new_id = cursor.fetchone()[0]
                    
                    # 로그 기록
                    insert_audit_log(cursor, st.session_state.user['user_id'], 'ADD_PLANT', new_id, f"새 식물 등록: {name}")
                    conn.commit()
                    st.success(f"'{name}' 등록 성공!")
                except Exception as e:
                    st.error(f"오류: {e}")

    # --- 탭 1.5: 식물 수정 ---
    with tab1_edit:
        cursor.execute("SELECT species_id, common_name FROM plant_species ORDER BY species_id")
        all_plants = cursor.fetchall()
        p_dict = {p[1]: p[0] for p in all_plants}
        
        if all_plants:
            edit_name = st.selectbox("수정할 식물", list(p_dict.keys()), key="edit_plant_sel")
            edit_pid = p_dict[edit_name]
            cursor.execute("SELECT common_name, category, difficulty, sun_level, image_url, description FROM plant_species WHERE species_id=%s", (edit_pid,))
            cur_info = cursor.fetchone()
            
            with st.form("edit_plant_form"):
                new_name = st.text_input("이름", value=cur_info[0])
                # (간략화를 위해 일부 필드 생략 가능하나 전체 구현함)
                new_img = st.text_input("이미지 URL", value=cur_info[4] if cur_info[4] else "")
                new_desc = st.text_area("설명", value=cur_info[5] if cur_info[5] else "")
                
                if st.form_submit_button("수정 저장"):
                    cursor.execute("UPDATE plant_species SET common_name=%s, image_url=%s, description=%s WHERE species_id=%s", 
                                 (new_name, new_img, new_desc, edit_pid))
                    
                    insert_audit_log(cursor, st.session_state.user['user_id'], 'EDIT_PLANT', edit_pid, f"식물 정보 수정: {new_name}")
                    conn.commit()
                    st.success("수정 완료!")
                    st.rerun()

    # --- 탭 2: 퀴즈 추가 ---
    with tab2:
        if all_plants:
            sel_name_q = st.selectbox("식물 선택", list(p_dict.keys()), key="add_q_sel")
            sel_pid_q = p_dict[sel_name_q]
            with st.form("add_step_form"):
                step = st.number_input("단계", min_value=1)
                stage = st.text_input("단계명", "Seed")
                q = st.text_area("질문")
                ans = st.radio("정답", [True, False])
                expl = st.text_input("해설")
                
                if st.form_submit_button("퀴즈 추가"):
                    cursor.execute("INSERT INTO species_step(species_id, step_order, stage_name, quiz_question, correct_answer, explanation) VALUES (%s, %s, %s, %s, %s, %s) RETURNING step_id", 
                                   (sel_pid_q, step, stage, q, ans, expl))
                    new_sid = cursor.fetchone()[0]
                    insert_audit_log(cursor, st.session_state.user['user_id'], 'ADD_QUIZ', new_sid, f"퀴즈 추가: {sel_name_q} {step}단계")
                    conn.commit()
                    st.success("추가 완료")

    # --- 탭 3: 퀴즈 수정 ---
    with tab3:
        if all_plants:
            target_name = st.selectbox("식물 선택", list(p_dict.keys()), key="edit_q_sel")
            target_pid = p_dict[target_name]
            cursor.execute("SELECT step_id, step_order, quiz_question, correct_answer, explanation FROM species_step WHERE species_id=%s ORDER BY step_order", (target_pid,))
            steps = cursor.fetchall()
            if steps:
                step_opts = {f"{s[1]}단계": s for s in steps}
                sel_k = st.selectbox("단계 선택", list(step_opts.keys()))
                s_data = step_opts[sel_k]
                sid = s_data[0]
                with st.form(f"ef_{sid}"):
                    nq = st.text_area("질문", value=s_data[2])
                    na = st.radio("정답", [True, False], index=0 if s_data[3] else 1)
                    ne = st.text_input("해설", value=s_data[4])
                    
                    if st.form_submit_button("수정 저장"):
                        cursor.execute("UPDATE species_step SET quiz_question=%s, correct_answer=%s, explanation=%s WHERE step_id=%s", (nq, na, ne, sid))
                        insert_audit_log(cursor, st.session_state.user['user_id'], 'EDIT_QUIZ', sid, f"퀴즈 수정: {target_name}")
                        conn.commit()
                        st.success("수정 완료")
                        st.rerun()

    # --- 탭 4: 삭제 ---
    with tab4:
        if all_plants:
            del_name = st.selectbox("삭제할 식물", list(p_dict.keys()), key="del_sel")
            del_pid = p_dict[del_name]
            
            cursor.execute("SELECT COUNT(*) FROM user_plant WHERE species_id=%s", (del_pid,))
            cnt = cursor.fetchone()[0]
            if cnt > 0: st.error(f"🚨 현재 {cnt}명이 키우는 중입니다!")
            
            if st.button("삭제하기"):
                st.session_state['del_pid'] = del_pid
            
            if st.session_state.get('del_pid') == del_pid:
                st.warning("정말 삭제하시겠습니까?")
                if st.button("네, 삭제확인"):
                    cursor.execute("DELETE FROM plant_species WHERE species_id=%s", (del_pid,))
                    insert_audit_log(cursor, st.session_state.user['user_id'], 'DEL_PLANT', del_pid, f"식물 삭제: {del_name}")
                    conn.commit()
                    st.success("삭제 완료")
                    st.session_state['del_pid'] = None
                    st.rerun()

    conn.close()

def content_mgr_view():
    """콘텐츠 관리자 메인 뷰"""
    # 권한 체크
    if st.session_state.user['role'] not in ['Content', 'Admin']:
        st.error("권한이 없습니다.")
        return

    st.header("📝 콘텐츠 관리자 페이지")
    
    # 탭 구성: 식물관리 / 경제설정 / 신고관리 / 감사로그
    tab1, tab2, tab3, tab4 = st.tabs(["🌱 식물/퀴즈 데이터", "💰 게임 경제 설정", "🚨 신고/숨김 관리", "📜 감사 로그"])
    
    with tab1: manage_plants_and_quizzes()
    with tab2: manage_game_config()
    with tab3: manage_tips_moderation()
    with tab4: view_audit_logs()