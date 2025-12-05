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
        diff_filter = col2.selectbox("난이도 선택", ["전체", "1 (쉬움)", "2", "3 (보통)", "4", "5 (어려움)"])
        sort_option = col3.selectbox("정렬 기준", ["이름순 (가나다)", "난이도 낮은순", "난이도 높은순"])

    # --- SQL 쿼리 (description 추가됨) ---
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
    elif sort_option == "난이도 낮은순":
        sql += " ORDER BY difficulty ASC"
    elif sort_option == "난이도 높은순":
        sql += " ORDER BY difficulty DESC"

    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    
    # --- 결과 출력 ---
    st.divider()
    if not rows:
        st.info("검색 결과가 없습니다.")
    else:
        st.markdown(f"총 **{len(rows)}**개의 식물이 발견되었습니다.")
        
        for row in rows:
            # description을 6번째 인덱스(맨 마지막)로 받아옴
            s_id, name, cat, diff, sun, img, desc = row
            
            with st.expander(f"🌱 {name} (난이도 {diff})"):
                c1, c2 = st.columns([1, 2])
                with c1:
                    if img: st.image(img, use_container_width=True)
                    else: st.write("📷 (이미지 없음)")
                
                with c2:
                    st.write(f"**카테고리**: {cat} | **광량**: {sun}")
                    st.write(f"**게임난이도**: {'⭐'*diff}")
                    
                    # [추가됨] 식물 상세 설명 표시
                    st.markdown("##### 📖 도감 정보")
                    if desc:
                        st.info(desc)
                    else:
                        st.caption("등록된 상세 정보가 없습니다.")
                    
                    st.divider()
                    
                    # 키우기 버튼 로직
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