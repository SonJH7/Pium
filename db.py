import psycopg2
import os
import streamlit as st
from dotenv import load_dotenv

# 로컬 환경일 때만 .env 로드
load_dotenv()

def get_conn():
    """
    DB 연결 함수
    1순위: Streamlit Cloud Secrets (배포 환경)
    2순위: 로컬 .env 파일 (개발 환경)
    """
    try:
        # 1. Streamlit Cloud 배포 환경인지 확인
        if "db" in st.secrets:
            db_config = st.secrets["db"]
            return psycopg2.connect(
                dbname=db_config["DB_NAME"],
                user=db_config["DB_USER"],
                password=db_config["DB_PASSWORD"],
                host=db_config["DB_HOST"],
                port=int(db_config["DB_PORT"])
            )
        
        # 2. 로컬 환경 (.env)
        else:
            return psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
            )
    except Exception as e:
        # 연결 실패 시 에러 로그
        st.error(f"DB 연결 실패: {e}")
        return None

# 테스트용 코드 (이 파일을 직접 실행할 때만 작동)
if __name__ == "__main__":
    conn = get_conn()
    if conn:
        print("✅ DB 연결 성공!")
        conn.close()