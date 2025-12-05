import streamlit as st
import pandas as pd
from db import get_conn

def write_tip_view(user_id):
    """팁 작성 화면"""
    st.subheader("📝 식물 재배 팁 작성")
    
    conn = get_conn()
    cursor = conn.cursor()
    
    # 1. 대상 식물 선택
    cursor.execute("SELECT species_id, common_name FROM plant_species ORDER BY species_id")
    species_list = cursor.fetchall()
    
    if not species_list:
        st.warning("등록된 식물이 없습니다. 관리자에게 문의하세요.")
        conn.close()
        return

    # 선택 박스 (ID와 이름 매핑)
    species_dict = {name: sid for sid, name in species_list}
    selected_name = st.selectbox("어떤 식물에 대한 팁인가요?", list(species_dict.keys()))
    selected_sid = species_dict[selected_name]
    
    # 2. 팁 입력
    title = st.text_input("팁 제목", placeholder="예: 몬스테라 잎이 찢어지게 하려면?")
    content = st.text_area("내용 (상세한 노하우를 적어주세요)", height=200)
    
    if st.button("팁 등록하기", type="primary"):
        if title and content:
            try:
                # INSERT
                cursor.execute("""
                    INSERT INTO expert_tip(expert_id, species_id, title, content)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, selected_sid, title, content))
                conn.commit()
                st.success("팁이 등록되었습니다! 사용자들에게 큰 도움이 될 거예요.")
                # 성공 시 2번째 탭(관리)으로 넘어가게 하거나 리런
                # st.rerun() 
            except Exception as e:
                st.error(f"등록 실패: {e}")
        else:
            st.warning("제목과 내용을 모두 입력해주세요.")
    conn.close()

def my_tips_view(user_id):
    """[수정됨] 내가 쓴 팁 목록 조회 및 수정/삭제"""
    st.subheader("📂 내가 등록한 팁 관리")
    
    conn = get_conn()
    cursor = conn.cursor()
    
    # 1. 내가 쓴 팁 목록 가져오기
    sql = """
        SELECT t.tip_id, s.common_name, t.title, t.content, t.created_at
        FROM expert_tip t
        JOIN plant_species s ON t.species_id = s.species_id
        WHERE t.expert_id = %s
        ORDER BY t.created_at DESC
    """
    cursor.execute(sql, (user_id,))
    tips = cursor.fetchall()
    
    if not tips:
        st.info("아직 등록한 팁이 없습니다. '팁 작성하기' 탭에서 노하우를 공유해주세요!")
        conn.close()
        return

    # 2. 팁 선택 (Selectbox)
    # 팁 구분을 위해 '식물명 | 제목' 형태로 표시
    tip_options = {f"[{t[1]}] {t[2]} (작성일: {t[4].strftime('%Y-%m-%d')})": t for t in tips}
    selected_option = st.selectbox("수정/삭제할 팁을 선택하세요", list(tip_options.keys()))
    
    # 선택된 팁 데이터 언패킹
    # 구조: (tip_id, common_name, title, content, created_at)
    sel_tip = tip_options[selected_option]
    tip_id = sel_tip[0]
    cur_plant_name = sel_tip[1]
    cur_title = sel_tip[2]
    cur_content = sel_tip[3]
    
    st.divider()
    st.markdown(f"**선택된 팁:** {cur_plant_name} - {cur_title}")

    # 3. 수정 폼
    with st.form(key=f"edit_tip_form_{tip_id}"):
        new_title = st.text_input("제목 수정", value=cur_title)
        new_content = st.text_area("내용 수정", value=cur_content, height=200)
        
        c1, c2 = st.columns([1, 5])
        with c1:
            update_btn = st.form_submit_button("수정 저장", type="primary")
        
        if update_btn:
            try:
                cursor.execute("""
                    UPDATE expert_tip 
                    SET title=%s, content=%s 
                    WHERE tip_id=%s
                """, (new_title, new_content, tip_id))
                conn.commit()
                st.success("수정되었습니다!")
                st.rerun()
            except Exception as e:
                st.error(f"수정 실패: {e}")

    # 4. 삭제 버튼 (실수 방지를 위해 폼 밖에 배치)
    with st.expander("🗑️ 이 팁을 삭제하시겠습니까?"):
        st.warning("삭제된 팁은 복구할 수 없습니다.")
        if st.button("네, 영구 삭제합니다", key=f"del_tip_{tip_id}"):
            try:
                cursor.execute("DELETE FROM expert_tip WHERE tip_id=%s", (tip_id,))
                conn.commit()
                st.success("삭제되었습니다.")
                st.rerun()
            except Exception as e:
                st.error(f"삭제 실패: {e}")

    conn.close()

def expert_view():
    """전문가 메인 화면"""
    # 권한 체크
    if st.session_state.user['role'] not in ['Expert', 'Admin', 'Content']:
        st.error("접근 권한이 없습니다.")
        return

    st.header("🎓 전문가(Expert) 페이지")
    
    tab1, tab2 = st.tabs(["팁 작성하기", "내가 쓴 팁 관리(수정/삭제)"])
    
    with tab1:
        write_tip_view(st.session_state.user['user_id'])
    
    with tab2:
        my_tips_view(st.session_state.user['user_id'])