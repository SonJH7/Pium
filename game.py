import streamlit as st
from db import get_conn

def get_user_plants(user_id):
    """사용자가 키우고 있는 식물 목록 가져오기"""
    conn = get_conn()
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
        # 1. 퀴즈 시도 로그 (정답)
        cursor.execute("INSERT INTO quiz_attempt(user_plant_id, step_id, is_correct) VALUES (%s, %s, true)", (user_plant_id, step_id))
        
        # 2. 보상 지급 (100점)
        reward = 100
        cursor.execute("UPDATE user_account SET points = points + %s WHERE user_id = %s", (reward, user_id))
        cursor.execute("INSERT INTO transaction_log(user_id, transaction_type, amount) VALUES (%s, 'QUIZ_REWARD', %s)", (user_id, reward))
        
        # 3. 단계 상승 로직
        cursor.execute("SELECT MAX(step_order) FROM species_step WHERE species_id = (SELECT species_id FROM species_step WHERE step_id=%s)", (step_id,))
        max_step = cursor.fetchone()[0]
        
        cursor.execute("SELECT step_order FROM species_step WHERE step_id=%s", (step_id,))
        current_ord = cursor.fetchone()[0]
        
        msg = ""
        if current_ord < max_step:
            cursor.execute("UPDATE user_plant SET current_step = current_step + 1 WHERE user_plant_id = %s", (user_plant_id,))
            msg = f"⭕ 정답! 포인트 +{reward}, 다음 단계로 성장했습니다! 🌱"
        else:
            cursor.execute("UPDATE user_plant SET is_completed = true WHERE user_plant_id = %s", (user_plant_id,))
            msg = f"🎉 축하합니다! 식물 졸업! 🎓 포인트 +{reward}"
        
        # 즉시 반영
        st.session_state.user['points'] += reward
        conn.commit()
        return True, msg
    except Exception as e:
        conn.rollback()
        return False, f"오류: {e}"
    finally:
        conn.close()

def apply_step1_penalty(user_plant_id, step_id, user_id):
    """1단계 실패 패널티: 그냥 포인트 차감 (-50)"""
    conn = get_conn()
    cursor = conn.cursor()
    penalty = 50
    
    try:
        # 1. 로그 (오답)
        cursor.execute("INSERT INTO quiz_attempt(user_plant_id, step_id, is_correct) VALUES (%s, %s, false)", (user_plant_id, step_id))
        
        # 2. 포인트 차감 (0 미만으로는 안 내려가게 처리 가능하지만 여기선 그냥 차감)
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
    """옵션 A: 포인트 쓰고 강제 통과 (Pay to Win)"""
    conn = get_conn()
    cursor = conn.cursor()
    cost = 300 # 부활 비용
    
    try:
        # 잔액 확인
        cursor.execute("SELECT points FROM user_account WHERE user_id=%s", (user_id,))
        current_points = cursor.fetchone()[0]
        
        if current_points < cost:
            return False, "포인트가 부족합니다!"

        # 1. 포인트 차감
        cursor.execute("UPDATE user_account SET points = points - %s WHERE user_id = %s", (cost, user_id))
        cursor.execute("INSERT INTO transaction_log(user_id, transaction_type, amount) VALUES (%s, 'FORCE_PASS', %s)", (user_id, -cost))
        
        # 2. 단계 상승 (강제 진화)
        cursor.execute("UPDATE user_plant SET current_step = current_step + 1 WHERE user_plant_id = %s", (user_plant_id,))
        
        # 로그는 '부활 사용'으로 기록
        cursor.execute("INSERT INTO quiz_attempt(user_plant_id, step_id, is_correct, used_continue) VALUES (%s, %s, false, true)", (user_plant_id, step_id))

        st.session_state.user['points'] -= cost
        conn.commit()
        return True, f"💸 {cost}포인트를 써서 위기를 모면했습니다! 다음 단계로 넘어갑니다."
    except Exception as e:
        conn.rollback()
        return False, f"오류: {e}"
    finally:
        conn.close()

def apply_reset_option(user_plant_id, step_id):
    """옵션 B: 무료 초기화 (1단계로)"""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        # 1. 단계 초기화
        cursor.execute("UPDATE user_plant SET current_step = 1 WHERE user_plant_id = %s", (user_plant_id,))
        
        # 2. 로그 기록
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
    
    user = st.session_state.user
    my_plants = get_user_plants(user['user_id'])
    
    if not my_plants:
        st.warning("키우는 식물이 없습니다. 도감에서 먼저 등록하세요!")
        return

    # 식물 탭 선택
    plant_names = [f"{p[1]} (ID:{p[0]})" for p in my_plants]
    selected_tab = st.selectbox("관리할 식물을 선택하세요", plant_names)
    
    idx = plant_names.index(selected_tab)
    u_plant_id, p_name, cur_step, is_comp, s_id = my_plants[idx]
    
    # 식물 상태 표시
    st.markdown(f"### 🌱 {p_name} (현재: {cur_step}단계)")
    
    if is_comp:
        st.success("🎓 이미 졸업한 식물입니다!")
        st.balloons()
        return

    # --- 실패 상태 관리 (세션 스테이트) ---
    # 키: fail_status_{user_plant_id} -> 값: None, 'failed_step1', 'failed_high'
    state_key = f"fail_status_{u_plant_id}"
    if state_key not in st.session_state:
        st.session_state[state_key] = None

    # 현재 퀴즈 가져오기
    quiz_data = get_current_quiz(s_id, cur_step)
    
    if not quiz_data:
        st.warning("데이터 부족: 퀴즈가 없습니다.")
        return

    step_id, stage_name, q_text, ans_bool, expl = quiz_data

    # 1. [상황 A] 이미 틀려서 선택지가 뜬 경우 (2단계 이상 실패 시)
    if st.session_state[state_key] == 'failed_high':
        st.error(f"❌ 틀렸습니다! ({expl})")
        st.warning("🚨 위기 상황! 선택하세요.")
        
        c1, c2 = st.columns(2)
        with c1:
            # 옵션 1: 돈 쓰고 넘어가기
            cost = 300
            if st.button(f"💸 {cost}P 내고 다음 단계로 가기", use_container_width=True):
                success, msg = apply_rescue_option(u_plant_id, user['user_id'], step_id)
                if success:
                    st.success(msg)
                    st.session_state[state_key] = None # 상태 초기화
                    st.rerun()
                else:
                    st.error(msg)
        
        with c2:
            # 옵션 2: 무료 초기화
            if st.button("🔄 무료로 처음(1단계)으로 돌아가기", use_container_width=True):
                msg = apply_reset_option(u_plant_id, step_id)
                st.info(msg)
                st.session_state[state_key] = None # 상태 초기화
                st.rerun()
        return # 선택지 화면일 때는 아래 퀴즈 안 보여줌

    # 2. [상황 B] 정상적인 퀴즈 풀기 화면
    st.info(f"📍 **{stage_name} 단계** 도전!")
    st.write(f"Q. {q_text}")
    
    with st.form(key=f"q_form_{u_plant_id}_{cur_step}"):
        choice = st.radio("정답은?", ["O", "X"])
        submit = st.form_submit_button("제출")
        
        if submit:
            user_ans = True if choice == "O" else False
            
            if user_ans == ans_bool:
                # 정답
                ok, msg = process_correct_answer(u_plant_id, step_id, user['user_id'])
                if ok:
                    st.success(msg)
                    st.session_state[state_key] = None
                    st.rerun()
                else:
                    st.error(msg)
            else:
                # 오답
                if cur_step == 1:
                    # 1단계는 묻지도 따지지도 않고 차감
                    msg = apply_step1_penalty(u_plant_id, step_id, user['user_id'])
                    st.error(f"틀렸습니다! ({expl})")
                    st.error(msg)
                    # 1단계 실패는 상태 변경 불필요 (그냥 차감되고 끝)
                    st.session_state[state_key] = None 
                else:
                    # 2단계 이상은 선택지 화면으로 전환
                    st.session_state[state_key] = 'failed_high'
                    st.rerun()