import streamlit as st
import pandas as pd
from db import get_conn

def login_user(login_id, password):
    """로그인 처리 함수"""
    conn = get_conn()
    cursor = conn.cursor()
    
    # 학번, 이름, 학과 등 정보까지 다 조회
    query = """
        SELECT user_id, login_id, role, points, student_id, name, department 
        FROM user_account 
        WHERE login_id = %s AND password_hash = %s
    """
    cursor.execute(query, (login_id, password))
    user_data = cursor.fetchone()
    
    conn.close()
    
    if user_data:
        # 세션에 저장할 딕셔너리 생성
        return {
            "user_id": user_data[0],
            "login_id": user_data[1],
            "role": user_data[2],
            "points": user_data[3],
            "student_id": user_data[4],
            "name": user_data[5],
            "department": user_data[6]
        }
    else:
        return None

def register_user(login_id, password, student_id, name, department):
    """회원가입 처리 함수"""
    conn = get_conn()
    cursor = conn.cursor()
    
    try:
        # 중복 ID 체크
        cursor.execute("SELECT 1 FROM user_account WHERE login_id = %s", (login_id,))
        if cursor.fetchone():
            return False, "이미 존재하는 ID입니다."
            
        # 신규 회원가입 (기본 role='User', points=1000)
        insert_sql = """
            INSERT INTO user_account(login_id, password_hash, student_id, name, department, role, points)
            VALUES (%s, %s, %s, %s, %s, 'User', 1000)
        """
        cursor.execute(insert_sql, (login_id, password, student_id, name, department))
        conn.commit()
        return True, "회원가입 성공! 로그인해주세요."
        
    except Exception as e:
        conn.rollback()
        return False, f"오류 발생: {e}"
    finally:
        conn.close()

def auth_view():
    """로그인/회원가입 화면 UI"""
    st.header("🔐 로그인 / 회원가입")
    
    tab1, tab2 = st.tabs(["로그인", "회원가입"])
    
    # --- 로그인 탭 ---
    with tab1:
        st.subheader("로그인")
        login_id = st.text_input("아이디", key="login_id_input")
        login_pw = st.text_input("비밀번호", type="password", key="login_pw_input")
        
        if st.button("로그인 실행"):
            user_info = login_user(login_id, login_pw)
            if user_info:
                st.session_state.user = user_info
                st.session_state.show_auth = False # 모달 닫기
                st.success(f"환영합니다, {user_info['name']}님!")
                st.rerun() # 화면 새로고침
            else:
                st.error("아이디 또는 비밀번호가 틀렸습니다.")

    # --- 회원가입 탭 ---
    with tab2:
        st.subheader("회원가입 (학생 정보 입력)")
        new_id = st.text_input("아이디 생성")
        new_pw = st.text_input("비밀번호 설정", type="password")
        
        # 대학생 정보 추가 입력
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("이름 (실명)")
            new_student_id = st.text_input("학번")
        with col2:
            new_dept = st.text_input("학과")

        if st.button("가입하기"):
            if new_id and new_pw and new_name:
                success, msg = register_user(new_id, new_pw, new_student_id, new_name, new_dept)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.warning("아이디, 비번, 이름은 필수입니다.")