import streamlit as st
import time
from db import get_conn
# [추가] 꽃비 효과를 위한 라이브러리 임포트
from streamlit_extras.let_it_rain import rain 

def get_config_value(cursor, key, default_val):
    """DB에서 게임 설정값을 가져오는 헬퍼 함수"""
    try:
        cursor.execute("SELECT config_value FROM game_config WHERE config_key = %s", (key,))
        row = cursor.fetchone()
        return int(row[0]) if row else default_val
    except:
        return default_val

def get_user_plants(user_id):
    """사용자가 키우고 있는 식물 목록 가져오기"""
    conn = get_conn()
    if conn is None: return []
    cursor = conn.cursor()
    sql = """
        SELECT up.user_plant_id, s.common_name, up.current_step, up.is_completed, s.species_id
        FROM user_plant up
        JOIN plant_species s ON up.species_id = s.species_id
        WHERE up.user_id = %s
        ORDER BY up.created_at DESC
    """
    cursor.execute(sql, (user_id,))
    data = cursor.fetchall()
    conn.close()
    return data

def get_current_quiz(species_id, step_order):
    """현재 단계의 퀴즈 정보 가져오기"""
    conn = get_conn()
    if conn is None: return None
    cursor = conn.cursor()
    sql = """
        SELECT step_id, stage_name, quiz_question, correct_answer, explanation
        FROM species_step
        WHERE species_id = %s AND step_order = %s
    """
    cursor.execute(sql, (species_id, step_order))
    row = cursor.fetchone()
    conn.close()
    return row

def process_correct_answer(user_plant_id, step_id, user_id):
    """정답 처리: 포인트 지급 + 단계 상승"""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO quiz_attempt(user_plant_id, step_id, is_correct) VALUES (%s, %s, true)", (user_plant_id, step_id))
        
        reward = get_config_value(cursor, 'quiz_reward', 100) # DB에서 값 가져오기
        cursor.execute("UPDATE user_account SET points = points + %s WHERE user_id = %s", (reward, user_id))
        cursor.execute("INSERT INTO transaction_log(user_id, transaction_type, amount) VALUES (%s, 'QUIZ_REWARD', %s)", (user_id, reward))
        
        cursor.execute("SELECT MAX(step_order) FROM species_step WHERE species_id = (SELECT species_id FROM species_step WHERE step_id=%s)", (step_id,))
        max_step = cursor.fetchone()[0]
        
        cursor.execute("SELECT step_order FROM species_step WHERE step_id=%s", (step_id,))
        current_ord = cursor.fetchone()[0]
        
        msg = ""
        is_graduation = False
        
        if current_ord < max_step:
            cursor.execute("UPDATE user_plant SET current_step = current_step + 1 WHERE user_plant_id = %s", (user_plant_id,))
            msg = f"🌸 정답입니다! 포인트 +{reward}P 획득! 식물이 쑥쑥 자랐어요! 🌱"
        else:
            cursor.execute("UPDATE user_plant SET is_completed = true WHERE user_plant_id = %s", (user_plant_id,))
            msg = f"🎓 축하합니다! 식물 졸업! 포인트 +{reward}P 획득!"
            is_graduation = True
        
        st.session_state.user['points'] += reward
        conn.commit()
        return True, msg, is_graduation
    except Exception as e:
        conn.rollback()
        return False, f"오류: {e}", False
    finally:
        conn.close()

def apply_step1_penalty(user_plant_id, step_id, user_id):
    """1단계 실패 패널티"""
    conn = get_conn()
    cursor = conn.cursor()
    penalty = 50
    try:
        cursor.execute("INSERT INTO quiz_attempt(user_plant_id, step_id, is_correct) VALUES (%s, %s, false)", (user_plant_id, step_id))
        cursor.execute("UPDATE user_account SET points = points - %s WHERE user_id = %s", (penalty, user_id))
        cursor.execute("INSERT INTO transaction_log(user_id, transaction_type, amount) VALUES (%s, 'PENALTY_STEP1', %s)", (user_id, -penalty))
        st.session_state.user['points'] -= penalty
        conn.commit()
        return f"❌ 1단계는 봐주지 않습니다! 포인트 -{penalty} 차감."
    except Exception as e:
        conn.rollback()
        return f"오류: {e}"
    finally:
        conn.close()

def apply_rescue_option(user_plant_id, user_id, step_id):
    """옵션 A: 포인트 쓰고 강제 통과 (안전성 보강 버전)"""
    conn = get_conn()
    cursor = conn.cursor()
    # DB에서 비용 가져오기
    cost = get_config_value(cursor, 'revive_cost', 300)

    try:
        # 1. 포인트 잔액 확인
        cursor.execute("SELECT points FROM user_account WHERE user_id=%s", (user_id,))
        current_points = cursor.fetchone()[0]

        if current_points < cost:
            return False, "포인트가 부족합니다!"

        # 2. 포인트 차감 및 로그 기록
        cursor.execute("UPDATE user_account SET points = points - %s WHERE user_id = %s", (cost, user_id))
        cursor.execute("INSERT INTO transaction_log(user_id, transaction_type, amount) VALUES (%s, 'FORCE_PASS', %s)", (user_id, -cost))

        # 3. 현재 식물 정보 조회 (species_id, current_step)
        cursor.execute("SELECT species_id, current_step FROM user_plant WHERE user_plant_id = %s", (user_plant_id,))
        row = cursor.fetchone()
        species_id, current_step = row[0], row[1]

        # 4. 해당 종의 '최대 단계' 조회
        cursor.execute("SELECT MAX(step_order) FROM species_step WHERE species_id = %s", (species_id,))
        max_step = cursor.fetchone()[0]

        # 5. 오답 시도 로그 (부활 사용 표시)
        cursor.execute("INSERT INTO quiz_attempt(user_plant_id, step_id, is_correct, used_continue) VALUES (%s, %s, false, true)", (user_plant_id, step_id))

        # 6. 단계 상승 로직 (졸업 체크)
        if current_step >= max_step:
            # 이미 마지막 단계였으면 졸업 처리
            cursor.execute("UPDATE user_plant SET is_completed = true WHERE user_plant_id = %s", (user_plant_id,))
            msg = f"💸 {cost}P를 사용하여 위기를 넘기고 졸업했습니다! 🎓"
        else:
            # 다음 단계로 이동
            cursor.execute("UPDATE user_plant SET current_step = current_step + 1 WHERE user_plant_id = %s", (user_plant_id,))
            msg = f"💸 {cost}P를 사용하여 위기를 넘겼습니다! 다음 단계로 성장합니다. 🌱"

        # 7. 세션 업데이트 및 커밋
        st.session_state.user['points'] -= cost
        conn.commit()
        return True, msg

    except Exception as e:
        conn.rollback()
        return False, f"오류 발생: {e}"
    finally:
        conn.close()

def apply_reset_option(user_plant_id, step_id):
    """옵션 B: 무료 초기화"""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE user_plant SET current_step = 1 WHERE user_plant_id = %s", (user_plant_id,))
        cursor.execute("INSERT INTO quiz_attempt(user_plant_id, step_id, is_correct) VALUES (%s, %s, false)", (user_plant_id, step_id))
        conn.commit()
        return "🔄 처음부터 다시 시작합니다. (포인트 차감 없음)"
    except Exception as e:
        conn.rollback()
        return f"오류: {e}"
    finally:
        conn.close()

def game_view():
    st.header("🌿 내 식물 키우기")
    
    # --- [효과 처리] 정답 맞췄을 때 꽃비 내리는 효과 ---
    if 'celebrate_msg' not in st.session_state:
        st.session_state['celebrate_msg'] = None

    if st.session_state['celebrate_msg']:
        # 🌸 여기가 꽃비 내리는 부분입니다!
        rain(
            emoji="🌸", 
            font_size=54,
            falling_speed=5,
            animation_length="2s", # 2초 동안 내림
        )
        # 초록색 성공 메시지
        st.success(st.session_state['celebrate_msg'], icon="🎁")
        # 메시지 초기화
        st.session_state['celebrate_msg'] = None
    # -----------------------------------------------------

    user = st.session_state.user
    my_plants = get_user_plants(user['user_id'])
    
    if not my_plants:
        st.warning("키우는 식물이 없습니다. 도감에서 먼저 등록하세요!")
        return

    plant_names = [f"{p[1]} (ID:{p[0]})" for p in my_plants]
    selected_tab = st.selectbox("관리할 식물을 선택하세요", plant_names)
    
    idx = plant_names.index(selected_tab)
    u_plant_id, p_name, cur_step, is_comp, s_id = my_plants[idx]
    
    st.markdown(f"### 🌱 {p_name} (현재: {cur_step}단계)")
    
    if is_comp:
        st.success("🎓 이미 졸업한 식물입니다!")
        st.balloons()
        return

    state_key = f"fail_status_{u_plant_id}"
    if state_key not in st.session_state:
        st.session_state[state_key] = None

    quiz_data = get_current_quiz(s_id, cur_step)
    
    if not quiz_data:
        st.warning("데이터 부족: 퀴즈가 없습니다.")
        return

    step_id, stage_name, q_text, ans_bool, expl = quiz_data

    # 실패 상황 (선택지 화면)
    if st.session_state[state_key] == 'failed_high':
        st.error(f"❌ 틀렸습니다! ({expl})")
        st.warning("🚨 위기 상황! 선택하세요.")
        # [추가된 부분] 화면에 표시할 비용을 DB에서 잠깐 조회해옴
        conn_tmp = get_conn()
        cur_tmp = conn_tmp.cursor()
        current_revive_cost = get_config_value(cur_tmp, 'revive_cost', 300)
        conn_tmp.close()

        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"💸 {current_revive_cost}P 내고 넘어가기", use_container_width=True):
                success, msg = apply_rescue_option(u_plant_id, user['user_id'], step_id)
                if success:
                    st.session_state['celebrate_msg'] = msg
                    st.session_state[state_key] = None
                    st.rerun()
                else:
                    st.error(msg)
        with c2:
            if st.button("🔄 무료로 초기화", use_container_width=True):
                msg = apply_reset_option(u_plant_id, step_id)
                st.info(msg)
                st.session_state[state_key] = None
                st.rerun()
        return

    # 정상 퀴즈 화면
    st.info(f"📍 **{stage_name} 단계** 도전!")
    st.markdown(f"### Q. {q_text}")
    
    with st.form(key=f"q_form_{u_plant_id}_{cur_step}"):
        choice = st.radio("정답은?", ["O", "X"])
        submit = st.form_submit_button("제출", use_container_width=True)
        
        if submit:
            user_ans = True if choice == "O" else False
            
            if user_ans == ans_bool:
                # [정답]
                ok, msg, is_grad = process_correct_answer(u_plant_id, step_id, user['user_id'])
                if ok:
                    # 세션에 메시지 저장 후 리런 -> 위쪽에서 rain() 실행됨
                    st.session_state['celebrate_msg'] = msg
                    st.session_state[state_key] = None
                    st.rerun()
                else:
                    st.error(msg)
            else:
                # [오답]
                if cur_step == 1:
                    msg = apply_step1_penalty(u_plant_id, step_id, user['user_id'])
                    st.error(f"틀렸습니다! ({expl})")
                    st.error(msg)
                    st.session_state[state_key] = None 
                else:
                    st.session_state[state_key] = 'failed_high'
                    st.rerun()
