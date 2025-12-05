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
    
    # [수정됨] 검색 결과가 없을 때 -> 식물 신청 폼 표시
    if not rows:
        st.warning(f"🤔 '{search_term}'에 대한 검색 결과가 없습니다.")
        
        st.markdown("---")
        st.subheader("🙋‍♀️ 찾으시는 식물이 없나요?")
        
        if st.session_state.user:
            st.write("관리자에게 식물 추가를 요청해보세요! 검토 후 도감에 추가됩니다.")
            
            with st.form("request_plant_form"):
                # 검색어가 있으면 자동으로 채워줌
                req_name = st.text_input("신청할 식물 이름", value=search_term if search_term else "")
                submitted = st.form_submit_button("🌱 식물 등록 신청하기")
                
                if submitted:
                    if req_name:
                        try:
                            # plant_request 테이블에 저장
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
            
    # 검색 결과가 있을 때
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