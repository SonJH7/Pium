import psycopg2
import os
import streamlit as st
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def get_conn():
    """DB 커넥션을 반환하는 함수"""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
        )
        return conn
    except Exception as e:
        st.error(f"DB 연결 실패: {e}")
        return None

# 테스트용 코드 (이 파일을 직접 실행할 때만 작동)
if __name__ == "__main__":
    conn = get_conn()
    if conn:
        print("✅ DB 연결 성공!")
        conn.close()