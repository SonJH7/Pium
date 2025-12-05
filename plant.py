import streamlit as st
from db import get_conn

def plant_search_view():
    st.header("🔍 식물 도감 검색")

    conn = get_conn()
    if conn is None:
        st.error("DB 연결 실패")
        return
    cursor = conn.cursor()

    # --- [업그레이드] 필터링 및 정렬 옵션 ---
    with st.expander("🔎 상세 필터 옵션 열기", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        # 1. 이름 검색
        search_term = col1.text_input("식물 이름 검색", placeholder="예: 몬스테라")
        
        # 2. 난이도 필터
        diff_filter = col2.selectbox("난이도 선택", ["전체", "1 (쉬움)", "2", "3 (보통)", "4", "5 (어려움)"])
        
        # 3. 정렬 기준
        sort_option = col3.selectbox("정렬 기준", ["이름순 (가나다)", "난이도 낮은순", "난이도 높은순"])

    # --- SQL 쿼리 동적 생성 ---
    sql = "SELECT species_id, common_name, category, difficulty, sun_level, image_url FROM plant_species WHERE 1=1"
    params = []

    # 조건 1: 이름 검색
    if search_term:
        sql += " AND common_name LIKE %s"
        params.append(f"%{search_term}%")
    
    # 조건 2: 난이도 필터
    if diff_filter != "전체":
        difficulty_val = int(diff_filter.split()[0]) # "1 (쉬움)" -> 1
        sql += " AND difficulty = %s"
        params.append(difficulty_val)

    # 조건 3: 정렬 (SQL Injection 방지를 위해 파라미터가 아닌 구문으로 처리)
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
            s_id, name, cat, diff, sun, img = row
            
            with st.expander(f"🌱 {name} (난이도 {diff})"):
                c1, c2 = st.columns([1, 3])
                with c1:
                    if img: st.image(img, use_container_width=True)
                    else: st.write("📷 (이미지 없음)")
                
                with c2:
                    st.write(f"**카테고리**: {cat} | **광조**: {sun}")
                    st.write(f"**난이도**: {'⭐'*diff}")
                    
                    if st.session_state.user:
                        # 이미 키우고 있는지 확인
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