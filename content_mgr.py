import streamlit as st
import pandas as pd
from db import get_conn

def insert_audit_log(cursor, admin_id, action_type, target_id, details):
    """감사 로그 기록용 헬퍼 함수"""
    cursor.execute("""
        INSERT INTO audit_log (admin_id, action_type, target_id, details)
        VALUES (%s, %s, %s, %s)
    """, (admin_id, action_type, target_id, details))

def manage_game_config():
    """1. 경제 파라미터 조정"""
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
                insert_audit_log(cur, st.session_state.user['user_id'], 'UPDATE_CONFIG', 0, f"이어하기:{revive_cost}, 보상:{quiz_reward}")
                conn.commit()
                st.success("설정 저장 완료")
            except Exception as e:
                conn.rollback()
                st.error(f"오류: {e}")
    conn.close()

def manage_tips_moderation():
    """2. [UPGRADE] 신고 관리 및 숨김 처리"""
    st.markdown("#### 🚨 신고/숨김 관리")
    
    conn = get_conn()
    cur = conn.cursor()
    
    # --- [PART 1] 들어온 신고 목록 (최우선 표시) ---
    st.markdown("##### 🔥 접수된 신고 목록 (처리 필요)")
    
    # 신고 내역 조회 (팁 정보 + 신고 사유)
    sql_report = """
        SELECT r.report_id, t.tip_id, t.title, t.content, r.reason, u.name, r.created_at
        FROM tip_report r
        JOIN expert_tip t ON r.tip_id = t.tip_id
        JOIN user_account u ON r.reporter_id = u.user_id
        ORDER BY r.created_at DESC
    """
    cur.execute(sql_report)
    reports = cur.fetchall()
    
    if not reports:
        st.success("현재 접수된 신고가 없습니다. 깨끗하네요! ✨")
    else:
        for rep in reports:
            rid, tid, title, content, reason, reporter, date = rep
            
            with st.expander(f"🚨 신고됨: {title} (신고자: {reporter})", expanded=True):
                st.error(f"**신고 사유:** {reason}")
                st.markdown(f"**원본 내용:** {content}")
                st.caption(f"신고일: {date}")
                
                c1, c2 = st.columns(2)
                with c1:
                    # 신고 수락 -> 팁 숨김 + 신고 내역 삭제(처리됨)
                    if st.button("⛔ 신고 수락 (팁 숨기기)", key=f"accept_rep_{rid}", type="primary"):
                        try:
                            # 1. 팁 숨김
                            cur.execute("UPDATE expert_tip SET is_hidden=TRUE WHERE tip_id=%s", (tid,))
                            # 2. 신고 내역 삭제 (처리 완료)
                            cur.execute("DELETE FROM tip_report WHERE report_id=%s", (rid,))
                            # 3. 로그
                            insert_audit_log(cur, st.session_state.user['user_id'], 'HIDE_TIP_REPORT', tid, f"신고 수락 및 숨김: {title}")
                            conn.commit()
                            st.success("처리 완료 (숨김 처리됨)")
                            st.rerun()
                        except Exception as e: st.error(e)
                with c2:
                    # 신고 반려 -> 팁 유지 + 신고 내역 삭제
                    if st.button("❌ 신고 반려 (무시)", key=f"ignore_rep_{rid}"):
                        try:
                            cur.execute("DELETE FROM tip_report WHERE report_id=%s", (rid,))
                            insert_audit_log(cur, st.session_state.user['user_id'], 'IGNORE_REPORT', tid, f"신고 반려: {title}")
                            conn.commit()
                            st.info("신고를 반려했습니다.")
                            st.rerun()
                        except Exception as e: st.error(e)

    st.divider()

    # --- [PART 2] 전체 팁 모니터링 (기존 기능) ---
    st.markdown("##### 🛡️ 전체 게시물 모니터링")
    
    sql_all = """
        SELECT t.tip_id, s.common_name, t.title, t.content, u.name, t.is_hidden, t.created_at
        FROM expert_tip t
        JOIN plant_species s ON t.species_id = s.species_id
        JOIN user_account u ON t.expert_id = u.user_id
        ORDER BY t.created_at DESC
    """
    cur.execute(sql_all)
    all_tips = cur.fetchall()
    
    if all_tips:
        for tip in all_tips:
            tid, pname, title, content, writer, is_hidden, date = tip
            
            # 숨김 상태면 회색 배경
            bg_style = "background-color: #f0f2f6; opacity: 0.6;" if is_hidden else ""
            badge = "🚫 [숨김]" if is_hidden else "✅ [게시]"
            
            with st.container():
                st.markdown(f"""
                <div style="{bg_style} padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 5px;">
                    <small>{badge} | {pname} | {writer}</small><br>
                    <b>{title}</b><br>{content}
                </div>
                """, unsafe_allow_html=True)
                
                # 토글 버튼
                if is_hidden:
                    if st.button("복구", key=f"rec_{tid}"):
                        cur.execute("UPDATE expert_tip SET is_hidden=FALSE WHERE tip_id=%s", (tid,))
                        insert_audit_log(cur, st.session_state.user['user_id'], 'UNHIDE', tid, f"복구: {title}")
                        conn.commit()
                        st.rerun()
                else:
                    if st.button("숨김", key=f"hid_{tid}"):
                        cur.execute("UPDATE expert_tip SET is_hidden=TRUE WHERE tip_id=%s", (tid,))
                        insert_audit_log(cur, st.session_state.user['user_id'], 'HIDE', tid, f"숨김: {title}")
                        conn.commit()
                        st.rerun()
    conn.close()

def view_audit_logs():
    """3. 감사 로그 조회"""
    st.markdown("#### 📜 감사 로그 (Audit Log)")
    conn = get_conn()
    try:
        df = pd.read_sql("""
            SELECT l.log_id, u.name AS admin, l.action_type, l.details, l.created_at 
            FROM audit_log l JOIN user_account u ON l.admin_id=u.user_id 
            ORDER BY l.created_at DESC LIMIT 50
        """, conn)
        st.dataframe(df, use_container_width=True, hide_index=True)
    except: st.error("로그 조회 실패")
    conn.close()

def manage_plants_and_quizzes():
    """4. 식물 데이터 관리 (신청/등록/수정/삭제/퀴즈)"""
    st.markdown("#### 🌱 식물 및 퀘스트 데이터 관리")
    
    tab_req, tab1, tab1_edit, tab2, tab3, tab4 = st.tabs([
        "📩 신청 내역", "1. 새 식물 등록", "1.5. 식물 정보 수정", 
        "2. 퀴즈 추가", "3. 퀴즈 수정", "🚨 4. 식물 삭제"
    ])
    
    conn = get_conn()
    cursor = conn.cursor()

    # [탭 0: 신청 내역]
    with tab_req:
        st.info("유저 식물 신청 목록")
        cursor.execute("SELECT r.request_id, r.plant_name, u.name, r.created_at FROM plant_request r JOIN user_account u ON r.requester_id=u.user_id WHERE r.status='PENDING' ORDER BY r.created_at DESC")
        reqs = cursor.fetchall()
        if not reqs: st.success("대기 중인 신청 없음")
        else:
            for r in reqs:
                rid, pname, uname, date = r
                with st.expander(f"📌 {pname} ({uname})"):
                    c1, c2 = st.columns(2)
                    if c1.button("✅ 완료", key=f"done_{rid}"):
                        cursor.execute("UPDATE plant_request SET status='DONE', processed_by=%s WHERE request_id=%s", (st.session_state.user['user_id'], rid))
                        insert_audit_log(cursor, st.session_state.user['user_id'], 'REQ_DONE', rid, f"요청 처리: {pname}")
                        conn.commit()
                        st.rerun()
                    if c2.button("❌ 반려", key=f"rej_{rid}"):
                        cursor.execute("UPDATE plant_request SET status='REJECTED', processed_by=%s WHERE request_id=%s", (st.session_state.user['user_id'], rid))
                        insert_audit_log(cursor, st.session_state.user['user_id'], 'REQ_REJECT', rid, f"요청 반려: {pname}")
                        conn.commit()
                        st.rerun()

    # [탭 1: 등록]
    with tab1:
        with st.form("new_plant"):
            name = st.text_input("이름")
            cat = st.selectbox("종류", ["leaf", "flower", "fruit", "succulent"])
            c1, c2 = st.columns(2)
            diff = c1.slider("난이도", 1, 5, 2)
            sun = c2.selectbox("광량", ["Low", "Mid", "High"])
            img = st.text_input("이미지 URL")
            desc = st.text_area("설명", height=100)
            if st.form_submit_button("등록"):
                try:
                    cursor.execute("INSERT INTO plant_species(common_name, category, difficulty, sun_level, image_url, description) VALUES (%s, %s, %s, %s, %s, %s) RETURNING species_id", (name, cat, diff, sun, img, desc))
                    nid = cursor.fetchone()[0]
                    insert_audit_log(cursor, st.session_state.user['user_id'], 'ADD_PLANT', nid, f"등록: {name}")
                    conn.commit()
                    st.success("등록 완료")
                except Exception as e: st.error(e)

    # [탭 1.5: 수정]
    with tab1_edit:
        cursor.execute("SELECT species_id, common_name FROM plant_species ORDER BY species_id")
        ap = cursor.fetchall()
        if ap:
            pd_map = {p[1]: p[0] for p in ap}
            en = st.selectbox("수정할 식물", list(pd_map.keys()), key="ep_sel")
            epid = pd_map[en]
            cursor.execute("SELECT common_name, image_url, description FROM plant_species WHERE species_id=%s", (epid,))
            info = cursor.fetchone()
            with st.form("ep_form"):
                nn = st.text_input("이름", info[0])
                ni = st.text_input("이미지", info[1] or "")
                nd = st.text_area("설명", info[2] or "")
                if st.form_submit_button("수정 저장"):
                    cursor.execute("UPDATE plant_species SET common_name=%s, image_url=%s, description=%s WHERE species_id=%s", (nn, ni, nd, epid))
                    insert_audit_log(cursor, st.session_state.user['user_id'], 'EDIT_PLANT', epid, f"수정: {nn}")
                    conn.commit()
                    st.success("완료")
                    st.rerun()

    # [탭 2: 퀴즈 추가]
    with tab2:
        if ap:
            sn = st.selectbox("식물", list(pd_map.keys()), key="aq_sel")
            spid = pd_map[sn]
            with st.form("aq_form"):
                st_ord = st.number_input("단계", 1)
                st_nm = st.text_input("단계명")
                qq = st.text_area("질문")
                qa = st.radio("정답", [True, False])
                qe = st.text_input("해설")
                if st.form_submit_button("추가"):
                    cursor.execute("INSERT INTO species_step(species_id, step_order, stage_name, quiz_question, correct_answer, explanation) VALUES (%s, %s, %s, %s, %s, %s) RETURNING step_id", (spid, st_ord, st_nm, qq, qa, qe))
                    sid = cursor.fetchone()[0]
                    insert_audit_log(cursor, st.session_state.user['user_id'], 'ADD_QUIZ', sid, f"퀴즈추가: {sn} {st_ord}")
                    conn.commit()
                    st.success("완료")

    # [탭 3: 퀴즈 수정]
    with tab3:
        if ap:
            tn = st.selectbox("식물", list(pd_map.keys()), key="eq_sel")
            tid = pd_map[tn]
            cursor.execute("SELECT step_id, step_order, quiz_question, correct_answer, explanation FROM species_step WHERE species_id=%s ORDER BY step_order", (tid,))
            qs = cursor.fetchall()
            if qs:
                q_map = {f"{q[1]}단계": q for q in qs}
                qk = st.selectbox("단계", list(q_map.keys()))
                qd = q_map[qk]
                qid = qd[0]
                with st.form(f"eqf_{qid}"):
                    nq = st.text_area("질문", qd[2])
                    na = st.radio("정답", [True, False], index=0 if qd[3] else 1)
                    ne = st.text_input("해설", qd[4])
                    if st.form_submit_button("수정"):
                        cursor.execute("UPDATE species_step SET quiz_question=%s, correct_answer=%s, explanation=%s WHERE step_id=%s", (nq, na, ne, qid))
                        insert_audit_log(cursor, st.session_state.user['user_id'], 'EDIT_QUIZ', qid, f"퀴즈수정: {tn}")
                        conn.commit()
                        st.success("완료")
                        st.rerun()

    # [탭 4: 삭제]
    with tab4:
        if ap:
            dn = st.selectbox("삭제 식물", list(pd_map.keys()), key="dp_sel")
            dpid = pd_map[dn]
            if st.button("삭제하기"): st.session_state['dpid'] = dpid
            if st.session_state.get('dpid') == dpid:
                st.error("정말 삭제합니까?")
                if st.button("네, 삭제"):
                    cursor.execute("DELETE FROM plant_species WHERE species_id=%s", (dpid,))
                    insert_audit_log(cursor, st.session_state.user['user_id'], 'DEL_PLANT', dpid, f"삭제: {dn}")
                    conn.commit()
                    st.success("삭제됨")
                    st.session_state['dpid'] = None
                    st.rerun()

    conn.close()

def content_mgr_view():
    if st.session_state.user['role'] not in ['Content', 'Admin']:
        st.error("권한이 없습니다.")
        return

    st.header("📝 콘텐츠 관리자 페이지")
    tab1, tab2, tab3, tab4 = st.tabs(["🌱 식물/퀴즈 데이터", "💰 게임 경제 설정", "🚨 신고/숨김 관리", "📜 감사 로그"])
    
    with tab1: manage_plants_and_quizzes()
    with tab2: manage_game_config()
    with tab3: manage_tips_moderation()
    with tab4: view_audit_logs()