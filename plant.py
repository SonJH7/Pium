import streamlit as st
from db import get_conn

def plant_search_view():
    st.header("🔍 식물 도감 검색")

    # 1. 검색창
    search_term = st.text_input("식물 이름 검색 (예: 몬스테라)", "")
    
    conn = get_conn()
    cursor = conn.cursor()

    # 2. 검색 쿼리
    if search_term:
        sql = """
            SELECT species_id, common_name, category, difficulty, sun_level, image_url 
            FROM plant_species 
            WHERE common_name LIKE %s
        """
        cursor.execute(sql, (f"%{search_term}%",))
    else:
        # 검색어 없으면 전체 목록 (최대 10개)
        cursor.execute("SELECT species_id, common_name, category, difficulty, sun_level, image_url FROM plant_species LIMIT 10")
    
    rows = cursor.fetchall()
    
    # 3. 결과 출력
    if not rows:
        st.info("검색 결과가 없습니다.")
        # (추후 여기에 '없는 식물 신청하기' 버튼 추가 가능)
    else:
        for row in rows:
            s_id, name, cat, diff, sun, img = row
            
            with st.expander(f"🌱 {name} ({cat}) - 난이도 {diff}"):
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    if img:
                        st.image(img)
                    else:
                        st.write("📷 (이미지 없음)")
                
                with col2:
                    st.write(f"**광조 조건**: {sun}")
                    st.write(f"**난이도**: {'⭐'*diff}")
                    
                    # 로그인 상태라면 '키우기 시작' 버튼 표시
                    if st.session_state.user:
                        # 이미 키우고 있는지 확인
                        cursor.execute("SELECT 1 FROM user_plant WHERE user_id=%s AND species_id=%s", 
                                     (st.session_state.user['user_id'], s_id))
                        is_growing = cursor.fetchone()
                        
                        if is_growing:
                            st.success("✅ 이미 키우고 있는 식물입니다.")
                        else:
                            if st.button(f"'{name}' 키우기 시작!", key=f"btn_{s_id}"):
                                try:
                                    # user_plant에 추가
                                    cursor.execute("""
                                        INSERT INTO user_plant(user_id, species_id, current_step, is_completed)
                                        VALUES (%s, %s, 1, false)
                                    """, (st.session_state.user['user_id'], s_id))
                                    conn.commit()
                                    st.toast(f"{name}을(를) 내 정원에 심었습니다! 🌿")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"오류: {e}")
                    else:
                        st.caption("로그인하면 이 식물을 키울 수 있습니다.")

    conn.close()