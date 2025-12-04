import streamlit as st
import pandas as pd
from db import get_conn

def write_tip_view(user_id):
    """팁 작성 화면"""
    st.subheader("📝 식물 재배 팁 작성")
    
    conn = get_conn()
    cursor = conn.cursor()
    
    # 1. 대상 식물 선택
    cursor.execute("SELECT species_id, common_name FROM plant_species")
    species_list = cursor.fetchall()
    
    # 선택 박스 (ID와 이름 매핑)
    species_dict = {name: sid for sid, name in species_list}
    selected_name = st.selectbox("어떤 식물에 대한 팁인가요?", list(species_dict.keys()))
    selected_sid = species_dict[selected_name]
    
    # 2. 팁 입력
    title = st.text_input("팁 제목")
    content = st.text_area("내용 (상세한 노하우를 적어주세요)")
    
    if st.button("팁 등록하기"):
        if title and content:
            try:
                # INSERT
                cursor.execute("""
                    INSERT INTO expert_tip(expert_id, species_id, title, content)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, selected_sid, title, content))
                conn.commit()
                st.success("팁이 등록되었습니다! 사용자들에게 큰 도움이 될 거예요.")
                st.rerun()
            except Exception as e:
                st.error(f"등록 실패: {e}")
        else:
            st.warning("제목과 내용을 모두 입력해주세요.")
    conn.close()

def my_tips_view(user_id):
    """내가 쓴 팁 목록 조회"""
    st.subheader("📂 내가 등록한 팁 목록")
    
    conn = get_conn()
    # JOIN을 사용하여 식물 이름까지 가져오기
    sql = """
        SELECT t.tip_id, s.common_name, t.title, t.created_at
        FROM expert_tip t
        JOIN plant_species s ON t.species_id = s.species_id
        WHERE t.expert_id = %s
        ORDER BY t.created_at DESC
    """
    df = pd.read_sql(sql, conn, params=(user_id,))
    conn.close()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("아직 등록한 팁이 없습니다.")

def expert_view():
    """전문가 메인 화면"""
    # 권한 체크 (URL로 직접 접속하는 경우 방지)
    if st.session_state.user['role'] not in ['Expert', 'Admin']:
        st.error("접근 권한이 없습니다.")
        return

    st.header("🎓 전문가(Expert) 페이지")
    
    tab1, tab2 = st.tabs(["팁 작성하기", "내가 쓴 팁 관리"])
    
    with tab1:
        write_tip_view(st.session_state.user['user_id'])
    
    with tab2:
        my_tips_view(st.session_state.user['user_id'])