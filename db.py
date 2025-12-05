import psycopg2
import os
import streamlit as st
from dotenv import load_dotenv

# 로컬 환경일 때 .env 로드
load_dotenv()

def get_conn():
    """
    DB 연결 함수
    1순위: 로컬 .env 파일 확인 (개발 환경)
    2순위: Streamlit Cloud Secrets (배포 환경)
    """
    conn = None
    try:
        # 1. 로컬 환경 (.env) 우선 시도
        # .env 파일이 있고, 그 안에 DB_HOST 변수가 있을 때 실행됨
        if os.getenv("DB_HOST"):
            return psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT", "5432"))
            )
        
        # 2. 로컬 설정이 없으면 Streamlit Cloud Secrets 시도
        # 배포된 환경에서는 .env가 없으므로 이쪽으로 넘어옴
        elif "db" in st.secrets:
            db_config = st.secrets["db"]
            return psycopg2.connect(
                dbname=db_config["DB_NAME"],
                user=db_config["DB_USER"],
                password=db_config["DB_PASSWORD"],
                host=db_config["DB_HOST"],
                port=int(db_config["DB_PORT"])
            )

    except Exception as e:
        st.error(f"DB 연결 실패: {e}")
        return None

# 테스트용 코드
if __name__ == "__main__":
    conn = get_conn()
    if conn:
        print("✅ DB 연결 성공!")
        conn.close()