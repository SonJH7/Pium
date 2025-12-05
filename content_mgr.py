import streamlit as st
import pandas as pd
from db import get_conn

def manage_game_config():
    """경제 파라미터 조정 (이어하기 비용, 초기 포인트 등)"""
    st.markdown("#### 💰 경제 시스템 설정")
    st.caption("게임의 난이도와 경제 밸런스를 조절합니다.")
    
    conn = get_conn()
    cur = conn.cursor()
    
    # 현재 설정값 불러오기
    cur.execute("SELECT config_key, config_value FROM game_config")
    configs = dict(cur.fetchall())
    
    with st.form("config_form"):
        col1, col2 = st.columns(2)
        revive_cost = col1.number_input("이어하기 비용 (revive_cost)", 
                                      value=int(configs.get('revive_cost', 500)))
        quiz_reward = col2.number_input("퀴즈 정답 보상 (quiz_reward)", 
                                      value=int(configs.get('quiz_reward', 100)))
        
        if st.form_submit_button("설정 저장"):
            try:
                # Upsert 방식으로 업데이트
                cur.execute("UPDATE game_config SET config_value=%s WHERE config_key='revive_cost'", (str(revive_cost),))
                cur.execute("UPDATE game_config SET config_value=%s WHERE config_key='quiz_reward'", (str(quiz_reward),))
                conn.commit()
                st.success("게임 경제 설정이 업데이트되었습니다!")
            except Exception as e:
                st.error(f"설정 저장 실패: {e}")
    conn.close()

def manage_plants_and_quizzes():
    """식물 및 퀴즈 데이터 CRUD (기존 admin 기능을 여기로 이동)"""
    st.markdown("#### 🌱 식물 및 퀘스트 데이터 관리")
    
    tab1, tab2, tab3 = st.tabs(["1단계: 새 식물 등록", "2단계: 퀴즈 추가", "3단계: 퀴즈 수정"])
    
    conn = get_conn()
    cursor = conn.cursor()

    # --- 탭 1: 식물 등록 ---
    with tab1:
        with st.form("new_plant_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("식물 이름")
            cat = c2.selectbox("카테고리", ["leaf", "flower", "fruit", "succulent"])
            c3, c4 = st.columns(2)
            diff = c3.slider("난이도", 1, 5, 2)
            sun = c4.selectbox("광조", ["Low", "Mid", "High"])
            img_url = st.text_input("이미지 URL")
            
            if st.form_submit_button("식물 등록"):
                try:
                    cursor.execute("INSERT INTO plant_species(common_name, category, difficulty, sun_level, image_url) VALUES (%s, %s, %s, %s, %s)", 
                                   (name, cat, diff, sun, img_url))
                    conn.commit()
                    st.success(f"'{name}' 등록 성공!")
                except Exception as e:
                    st.error(f"오류: {e}")

    # --- 탭 2: 퀴즈 추가 ---
    with tab2:
        cursor.execute("SELECT species_id, common_name FROM plant_species ORDER BY species_id DESC")
        plants = cursor.fetchall()
        plant_dict = {p[1]: p[0] for p in plants}
        
        if plants:
            sel_name = st.selectbox("식물 선택", list(plant_dict.keys()), key="add_q_sel")
            sel_pid = plant_dict[sel_name]
            
            with st.form("add_step_form"):
                c1, c2 = st.columns(2)
                step = c1.number_input("단계 순서", min_value=1, value=1)
                stage = c2.text_input("단계 명", "Seed")
                q = st.text_area("질문")
                ans = st.radio("정답", [True, False], format_func=lambda x: "O" if x else "X")
                expl = st.text_input("해설")
                
                if st.form_submit_button("퀴즈 추가"):
                    try:
                        cursor.execute("INSERT INTO species_step(species_id, step_order, stage_name, quiz_question, correct_answer, explanation) VALUES (%s, %s, %s, %s, %s, %s)", 
                                       (sel_pid, step, stage, q, ans, expl))
                        conn.commit()
                        st.success("추가 완료!")
                    except Exception as e:
                        st.error(f"오류: {e}")

    # --- 탭 3: 퀴즈 수정 ---
    with tab3:
        cursor.execute("SELECT species_id, common_name FROM plant_species ORDER BY species_id")
        all_plants = cursor.fetchall()
        p_dict = {p[1]: p[0] for p in all_plants}
        
        if all_plants:
            target_name = st.selectbox("수정할 식물", list(p_dict.keys()), key="edit_q_sel")
            target_pid = p_dict[target_name]
            
            sql_steps = "SELECT step_id, step_order, stage_name, quiz_question, correct_answer, explanation FROM species_step WHERE species_id = %s ORDER BY step_order"
            cursor.execute(sql_steps, (target_pid,))
            steps = cursor.fetchall()
            
            if steps:
                df_steps = pd.DataFrame(steps, columns=["ID", "단계", "이름", "질문", "정답", "해설"])
                df_steps["정답"] = df_steps["정답"].apply(lambda x: "O" if x else "X")
                st.dataframe(df_steps, hide_index=True, use_container_width=True)
                
                step_options = {f"{s[1]}단계 ({s[2]})": s for s in steps}
                sel_key = st.selectbox("수정할 단계", list(step_options.keys()))
                sel_data = step_options[sel_key]
                s_id = sel_data[0]
                
                with st.form(key=f"edit_form_{s_id}"):
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
    conn.close()

def content_mgr_view():
    if st.session_state.user['role'] not in ['Content', 'Admin']:
        st.error("콘텐츠 관리자 권한이 필요합니다.")
        return

    st.header("📝 콘텐츠 관리자 페이지")
    tab1, tab2 = st.tabs(["🌱 식물/퀴즈 데이터", "💰 게임 경제 설정"])
    
    with tab1:
        manage_plants_and_quizzes()
    with tab2:
        manage_game_config()