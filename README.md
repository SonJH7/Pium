# 🌱 Pium: 대학생 인터랙티브 식물 키우기 & 도감 시스템

👉 배포 주소: https://pium001.streamlit.app/

**Pium**는 대학생을 위한 게이미피케이션(Gamification) 기반의 식물 도감 및 키우기 플랫폼입니다.
사용자는 식물 도감을 검색하고, 자신의 '가상 정원'에 식물을 등록하여 퀴즈를 풀며 성장시킬 수 있습니다.
**PostgreSQL**을 활용하여 사용자, 식물, 성장 단계, 포인트 트랜잭션 등 복잡한 데이터 관계를 체계적으로 관리합니다.

-----

## 🛠 기술 스택 (Tech Stack)

  * **Language**: Python 3.9+
  * **Frontend**: Streamlit
  * **Database**: PostgreSQL
  * **DB Driver**: `psycopg2-binary`
  * **Tools**: VS Code, DBeaver (or pgAdmin4), Git

-----

## 📂 프로젝트 구조 (File Structure)

이 프로젝트는 기능별로 모듈화되어 있으며, MVC 패턴과 유사한 구조를 따릅니다.

| 파일명 | 설명 | 비고 |
| :--- | :--- | :--- |
| **`app.py`** | **메인 실행 파일**. 전체 페이지 라우팅 및 세션 관리 | Entry Point |
| **`db.py`** | PostgreSQL 데이터베이스 연결 설정 및 커넥션 풀 관리 | DB Connection |
| **`auth.py`** | 회원가입(학번/학과 포함) 및 로그인 처리 | Authentication |
| **`plant.py`** | 식물 도감 검색(`LIKE` 검색), 상세 조회, 내 식물 등록 | Search & Register |
| **`game.py`** | **핵심 로직**. 퀴즈 풀이, 포인트 지급, 단계 성장을 **트랜잭션**으로 처리 | Game Logic (ACID) |
| **`expert.py`** | 전문가 전용 페이지. 재배 팁(Tip) 작성 및 조회 | Expert Feature |
| **`admin.py`** | 관리자 대시보드. 통계(View 활용), 회원 승인, **식물/퀴즈 데이터 관리(CRUD)** | Admin Dashboard |
| `create_tables.sql` | DB 스키마 생성(DDL) 및 기초 데이터(DML) 스크립트 | SQL Script |
| `.env` | DB 접속 정보(비밀번호 등)를 저장하는 환경 변수 파일 | **보안 주의** |
| `requirements.txt` | 프로젝트 의존성 라이브러리 목록 | Dependency |

-----

## 🚀 설치 및 실행 가이드 (Installation & Setup)

이 프로젝트를 로컬 환경에서 실행하기 위한 단계별 가이드입니다.

### 1\. 환경 준비 (Prerequisites)

  * Python이 설치되어 있어야 합니다.
  * PostgreSQL이 설치되어 있고 실행 중이어야 합니다.

### 2\. 프로젝트 세팅 (Terminal)

프로젝트 폴더(`plant_project`)로 이동한 후 아래 명령어를 순서대로 입력하세요.

**Windows (PowerShell)**

```powershell
# 1. 가상환경 생성
python -m venv venv

# 2. 가상환경 활성화
.\venv\Scripts\activate

# 3. 필수 라이브러리 설치
pip install -r requirements.txt
```

*(참고: Mac/Linux 사용자는 `source venv/bin/activate` 로 활성화)*

### 3\. 데이터베이스 구축 (PostgreSQL)

1.  **pgAdmin4** 또는 **DBeaver**를 실행합니다.
2.  새로운 데이터베이스 \*\*`plantdb`\*\*를 생성합니다.
    ```sql
    CREATE DATABASE plantdb;
    ```
3.  프로젝트 폴더 내 **`create_tables.sql`** 파일의 내용을 복사합니다.
4.  DB 툴의 'Query Tool'을 열고 붙여넣은 뒤 **실행(Run)** 합니다.
      * *테이블 생성, 뷰(View) 생성, 기초 데이터 입력이 한 번에 처리됩니다.*

### 4\. 환경 변수 설정 (.env)

프로젝트 루트 경로에 `.env` 파일을 생성하고 본인의 DB 정보를 입력하세요.

```ini
DB_NAME=plantdb
DB_USER=postgres
DB_PASSWORD=본인의_DB_비밀번호_입력
DB_HOST=localhost
DB_PORT=5432
```

### 5\. DB 연결 테스트

터미널에서 아래 명령어로 DB 연결이 정상적인지 확인합니다.

```bash
python db.py
# 출력: "✅ DB 연결 성공!" 이 뜨면 완료
```

### 6\. 애플리케이션 실행

```bash
streamlit run app.py
```

브라우저가 자동으로 열리며 앱이 시작됩니다. (http://localhost:8501)

-----

## ✨ 주요 기능 및 특징 (Key Features)

### 1\. 사용자 관리 (User Management)

  * **회원가입**: 대학생 맞춤형 정보(학번, 학과, 이름)를 입력받아 저장합니다.
  * **RBAC (역할 기반 접근 제어)**:
      * `User`: 일반 학생 (도감 검색, 게임 플레이)
      * `Expert`: 식물 전문가 (재배 팁 작성)
      * `Admin`: 관리자 (통계 확인, 권한 승인, 데이터 관리)

### 2\. 식물 도감 및 등록 (Search & Register)

  * **검색**: 식물 이름으로 DB를 조회(`LIKE %keyword%`)하여 결과를 카드 형태로 보여줍니다.
  * **이미지**: 외부 URL을 활용하여 식물 사진을 시각적으로 제공합니다.
  * **등록**: 마음에 드는 식물을 '내 정원'(`user_plant` 테이블)에 등록합니다. (중복 등록 방지)

### 3\. 게이미피케이션 & 트랜잭션 (Game & Transaction)

  * **단계별 성장**: Seed → Sprout → ... → Fruit 단계로 성장합니다.
  * **퀴즈 시스템**: 각 단계에 맞는 OX 퀴즈를 풉니다.
  * **트랜잭션(ACID)**: 정답 시 `[포인트 지급 + 로그 기록 + 식물 단계 상승]`이 하나의 트랜잭션으로 처리되어 데이터 무결성을 보장합니다.
  * **실패 페널티**:
      * 1단계 실패: 포인트 즉시 차감.
      * 2단계 이상 실패: **포인트를 써서 부활(Pass)** 하거나 **처음부터 다시하기(Reset)** 중 선택.

### 4\. 전문가 및 관리자 시스템 (Expert & Admin)

  * **전문가 신청**: 일반 유저가 신청서를 제출하면 관리자가 심사 후 승인합니다.
  * **데이터 관리**: 관리자 페이지에서 **새로운 식물과 퀴즈를 폼(Form)으로 쉽게 등록/수정**할 수 있습니다.
  * **통계 대시보드**: SQL View(`plant_completion_stats`)를 활용하여 식물별 졸업률 등을 시각화합니다.

-----

## 📊 데이터베이스 스키마 다이어그램 (ERD)

*(보고서에 포함된 ERD 그림이 있다면 여기에 이미지 링크를 넣으면 좋습니다)*

  * **User\_Account** (1) : (N) **User\_Plant**
  * **Plant\_Species** (1) : (N) **User\_Plant**
  * **Plant\_Species** (1) : (N) **Species\_Step** (퀴즈 정보)
  * **User\_Account** (1) : (N) **Transaction\_Log** (포인트 내역)

-----

## 👨‍💻 개발자 (Developer)

  * **이름**: 손정훈
  * **소속**: 부산대학교 정보컴퓨터공학부 (23학번)
  * **연락처**: (sjunh02@naver.com)

  * **이름**: 박소영
  * **소속**: 부산대학교 정보컴퓨터공학부 (23학번)
  * **연락처**: (kye625@naver.com)

-----

### 📝 과제 수행 후기 / 노트

  * Streamlit의 `session_state`를 활용하여 로그인 상태를 유지했습니다.
  * `try-except-rollback` 구문을 사용하여 DB 트랜잭션 안전성을 확보했습니다.
  * SQL `View`를 활용하여 복잡한 통계 쿼리를 단순화했습니다.
