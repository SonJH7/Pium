import streamlit as st
from db import get_conn

def plant_search_view():
    st.header("🔍 식물 도감 검색")

    conn = get_conn()
    if conn is None:
        st.error("DB 연결 실패")
        return
    cursor = conn.cursor()

    # --- 필터링 옵션 ---
    with st.expander("🔎 상세 필터 옵션", expanded=True):
        col1, col2, col3 = st.columns(3)
        search_term = col1.text_input("식물 이름 검색", placeholder="예: 몬스테라")
        diff_filter = col2.selectbox("게임 난이도 선택", ["전체", "1 (쉬움)", "2", "3 (보통)", "4", "5 (어려움)"])
        sort_option = col3.selectbox("정렬 기준", ["이름순 (가나다)", "게임 난이도 낮은순", "게임 난이도 높은순"])

    # --- SQL 쿼리 ---
    sql = "SELECT species_id, common_name, category, difficulty, sun_level, image_url, description FROM plant_species WHERE 1=1"
    params = []

    if search_term:
        sql += " AND common_name LIKE %s"
        params.append(f"%{search_term}%")
    
    if diff_filter != "전체":
        difficulty_val = int(diff_filter.split()[0])
        sql += " AND difficulty = %s"
        params.append(difficulty_val)

    if sort_option == "이름순 (가나다)":
        sql += " ORDER BY common_name ASC"
    elif sort_option == "게임 난이도 낮은순":
        sql += " ORDER BY difficulty ASC"
    elif sort_option == "게임 난이도 높은순":
        sql += " ORDER BY difficulty DESC"

    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    
    # --- 결과 출력 ---
    st.divider()
    
    if not rows:
        st.warning(f"🤔 '{search_term}'에 대한 검색 결과가 없습니다.")
        
        st.markdown("---")
        st.subheader("🙋‍♀️ 찾으시는 식물이 없나요?")
        
        if st.session_state.user:
            st.write("관리자에게 식물 추가를 요청해보세요! 검토 후 도감에 추가됩니다.")
            
            with st.form("request_plant_form"):
                req_name = st.text_input("신청할 식물 이름", value=search_term if search_term else "")
                submitted = st.form_submit_button("🌱 식물 등록 신청하기")
                
                if submitted:
                    if req_name:
                        try:
                            cursor.execute("""
                                INSERT INTO plant_request (requester_id, plant_name, status)
                                VALUES (%s, %s, 'PENDING')
                            """, (st.session_state.user['user_id'], req_name))
                            conn.commit()
                            st.success(f"🎉 '{req_name}' 신청이 접수되었습니다! 관리자가 확인 후 추가할 예정입니다.")
                        except Exception as e:
                            st.error(f"신청 실패: {e}")
                    else:
                        st.warning("식물 이름을 입력해주세요.")
        else:
            st.info("로그인하시면 없는 식물을 신청할 수 있습니다.")
            
    else:
        st.markdown(f"총 **{len(rows)}**개의 식물이 발견되었습니다.")
        
        for row in rows:
            s_id, name, cat, diff, sun, img, desc = row
            
            with st.expander(f"🌱 {name} (게임 난이도 {diff})"):
                c1, c2 = st.columns([1, 2])
                with c1:
                    if img: st.image(img, use_container_width=True)
                    else: st.write("📷 (이미지 없음)")
                
                with c2:
                    st.write(f"**카테고리**: {cat} | **광량**: {sun}")
                    st.write(f"**게임 난이도**: {'⭐'*diff}")
                    
                    st.markdown("##### 📖 도감 정보")
                    if desc:
                        st.info(desc)
                    else:
                        st.caption("등록된 상세 정보가 없습니다.")
                    
                    # --- [수정됨] 전문가 팁 조회 및 신고 기능 ---
                    # 팁 ID(t.tip_id)도 함께 조회하도록 쿼리 수정
                    cursor.execute("""
                        SELECT t.tip_id, t.title, t.content, u.name, t.created_at
                        FROM expert_tip t
                        JOIN user_account u ON t.expert_id = u.user_id
                        WHERE t.species_id = %s AND t.is_hidden = FALSE
                        ORDER BY t.created_at DESC
                    """, (s_id,))
                    tips = cursor.fetchall()

                    if tips:
                        st.write("") 
                        with st.expander(f"🎓 전문가 팁 확인하기 ({len(tips)}개)", expanded=False):
                            for tip in tips:
                                t_id, t_title, t_content, t_author, t_date = tip
                                
                                # 팁 내용 표시 컨테이너
                                with st.container():
                                    st.markdown(f"**💡 {t_title}**")
                                    st.caption(f"작성자: {t_author} | {t_date.strftime('%Y-%m-%d')}")
                                    st.write(t_content)
                                    
                                    # [신고 버튼 영역]
                                    if st.session_state.user:
                                        # 신고하기 팝오버 (Streamlit 1.33+ 기능, 구버전이면 expander 사용)
                                        with st.popover("🚨 신고하기", use_container_width=False):
                                            st.markdown("##### 🚨 부적절한 팁 신고")
                                            with st.form(key=f"report_form_{t_id}"):
                                                reason = st.text_area("신고 사유를 입력해주세요", placeholder="예: 잘못된 정보, 욕설/비방 등")
                                                report_btn = st.form_submit_button("신고 제출")
                                                
                                                if report_btn and reason:
                                                    try:
                                                        # 중복 신고 방지 (선택 사항)
                                                        cursor.execute("SELECT 1 FROM tip_report WHERE tip_id=%s AND reporter_id=%s", (t_id, st.session_state.user['user_id']))
                                                        if cursor.fetchone():
                                                            st.warning("이미 신고한 게시물입니다.")
                                                        else:
                                                            cursor.execute("""
                                                                INSERT INTO tip_report (tip_id, reporter_id, reason)
                                                                VALUES (%s, %s, %s)
                                                            """, (t_id, st.session_state.user['user_id'], reason))
                                                            conn.commit()
                                                            st.success("신고가 접수되었습니다. 관리자가 검토할 예정입니다.")
                                                    except Exception as e:
                                                        st.error(f"오류 발생: {e}")
                                    st.markdown("---")
                    else:
                        st.caption("아직 등록된 전문가 팁이 없습니다.")
                    
                    st.divider()
                    
                    if st.session_state.user:
                        cursor.execute("SELECT 1 FROM user_plant WHERE user_id=%s AND species_id=%s", 
                                     (st.session_state.user['user_id'], s_id))
                        if cursor.fetchone():
                            st.success("✅ 이미 내 정원에 있습니다.")
                        else:
                            if st.button(f"키우기 시작", key=f"btn_{s_id}"):
                                try:
                                    cursor.execute("INSERT INTO user_plant(user_id, species_id) VALUES (%s, %s)", 
                                                 (st.session_state.user['user_id'], s_id))
                                    conn.commit()
                                    st.toast(f"{name} 심기 완료! 🌿")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"오류: {e}")
                    else:
                        st.caption("로그인 후 키울 수 있습니다.")

    conn.close()