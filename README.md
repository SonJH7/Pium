# 🌱 **Pium: 대학생 인터랙티브 식물 키우기 & 도감 시스템**

### **Gamified Plant Encyclopedia + Growth Simulation using PostgreSQL & Streamlit**
부산대학교 **Databases** 강의의 프로그래밍 프로젝트로 구현한  
**식물 도감 + 퀴즈 기반 가상 재배 시뮬레이션 DB 애플리케이션**입니다.

📌 배포 주소: **[https://pium001.streamlit.app/](https://pium001.streamlit.app/)**

## 👥 팀 정보 (Team Members)

- **이름 (Name)**: 박소영, 손정훈  
- **학과 (Department)**: 정보컴퓨터공학부 (인공지능전공, 컴퓨터공학전공)  
- **학번 (Student ID)**: 202355625, 202355545  

---

# 1. 📘 **프로젝트 소개 (Project Overview)**

**Pium**은 대학생을 위한 **게이미피케이션 기반 식물 도감 + 식물 성장 시뮬레이터**입니다.
사용자는 실제 식물처럼 정보를 검색하고 학습하며, 가상 식물을 ‘정원’에 심어 **OX 퀴즈를 통과하며 성장**시킵니다.

모든 게임 데이터는 **PostgreSQL** 기반으로 관리하며 다음을 포함합니다:

* 사용자 정보(학번/학과/역할)
* 도감 식물 정보
* 성장 단계 + 단계별 퀴즈
* 사용자별 식물 성장 기록
* 포인트(머니) 시스템 + 트랜잭션 로그
* 전문가 팁 + 신고/감사 로그 시스템
* 콘텐츠 관리자·관리자에 의한 심사/관리 기능

Project Proposal 요구사항(Topic, 역할, 기능, 스키마) ✔
Project Introduction 요구 SQL 기능(DML·View·Authorization·Transaction·Index) ✔

## 🏗 기술 스택 및 구조 (Tech Stack & Architecture)

### Tech Stack

- **Frontend / App Framework**: [Streamlit](https://streamlit.io/)
- **Database**: PostgreSQL
- **DB API**: `psycopg2`
- **Configuration**: `.env` + `python-dotenv`
- **Data Handling**: `pandas`
- **UI 효과**: `streamlit-extras` (꽃비 애니메이션 등)

---

# 2. 🌟 **프로젝트 특징 (Key Features)**

이 프로젝트는 단순 CRUD가 아니라 **데이터베이스 강의의 모든 핵심 요소를 실제 서비스 수준으로 구현**했다는 점에서 높은 평가가 가능함.

### 디렉터리 구조 

```bash
.
├── app.py               # 메인 진입점 (라우팅 및 공통 레이아웃)
├── auth.py              # 로그인 / 회원가입
├── plant.py             # 도감 검색 및 식물 신청
├── game.py              # 식물 키우기 게임 로직 (퀴즈, 포인트, 단계 전이)
├── expert.py            # 전문가 팁 작성/관리
├── content_mgr.py       # 콘텐츠 관리자 페이지 (식물/퀴즈/경제/신고/감사로그)
├── admin.py             # 시스템 관리자 페이지 (통계, 권한 관리)
├── db.py                # DB 커넥션 관리 (.env / Streamlit secrets)
├── create_tables.sql    # 전체 스키마, 인덱스, 뷰, 기초 데이터, 권한 설정
├── requirements.txt     # 파이썬 라이브러리 의존성
└── .env                 # 로컬 개발용 DB 설정 (git에는 올리지 않는 파일)
```
### ✔ 실제 구현된 기능들

| 기능               | SQL 기능                       | 설명                            |
| ---------------- | ---------------------------- | ----------------------------- |
| 도감 검색·필터·정렬      | LIKE, ORDER BY, WHERE, Index | 이름 검색, 난이도/광량 필터, 정렬          |
| 식물 심기            | INSERT, UNIQUE 제약            | 유저가 도감의 식물을 정원에 추가            |
| 성장 퀴즈            | SELECT JOIN, Subquery        | 단계별 퀴즈, 정답 판별                 |
| O/X 퀴즈 트랜잭션 처리   | Transaction(Commit/Rollback) | 정답→포인트 지급+단계상승 일괄 처리          |
| 오답 처리            | Transaction                  | 1단계 패널티, 2단계 이상 "부활/초기화" 선택   |
| 전문가 팁 작성/수정/삭제   | INSERT/UPDATE/DELETE         | 전문가가 팁 작성 및 관리                |
| 팁 신고             | INSERT + FK                  | User → Content 관리자에게 신고 전달    |
| 팁 숨김/복구          | UPDATE                       | Content가 신고 검토 후 처리           |
| 감사 로그(Audit Log) | INSERT                       | Content/Admin의 모든 중요한 조작 기록   |
| 경제 파라미터 관리       | UPDATE game_config           | revive_cost, quiz_reward 등 변경 |
| 관리자 통계           | VIEW, GROUP BY, HAVING       | 식물별 완주율, 포인트 분포, 학과별 활동 통계    |
| 권한 관리            | UPDATE + Authorization       | 전문가 승인, role 변경               |

---

# 3. 🧩 **사용자 역할(RBAC)** 

(Project Introduction에서 역할별 기능 설명 요구 ✔ )
(Proposal Report 역할도 모두 반영 ✔ )

### 👤 **1) User (일반 사용자)**

- 식물 도감 검색, 필터, 정렬
- 원하는 식물을 선택해 “내 정원”에 심기
- O/X 퀴즈를 풀며 성장 단계 진행
- 오답 시:
  - 1단계: 포인트 패널티만 적용
  - 2단계 이상:  
    - 포인트를 지불하여 **강제 통과**  
    - 또는 **1단계로 무료 초기화**
- 식물 추가 요청(없는 식물 신청)
- 전문가 팁 읽기 및 부적절한 팁 신고

---

### 🎓 **2) Expert (전문가)**

- 일반 사용자 기능 모두 이용 가능
- 특정 식물에 대한 **전문가 팁 작성**
- 자신이 작성한 팁 목록 조회, 내용 수정 및 삭제

---

### 📝 **3) Content Manager (콘텐츠 관리자)**

- 새로운 식물 등록 및 정보 수정
- 식물별 성장 단계 및 퀴즈 데이터(질문/정답/해설) CRUD
- 게임 경제 파라미터 설정 (`revive_cost`, `quiz_reward` 등)
- 일반 사용자가 신청한 **식물 추가 요청 처리**
- 전문가 팁 신고 목록 확인, 팁 숨김/복구 처리
- 모든 주요 변경은 **감사 로그(audit_log)**에 기록

---

### 🛡️ **4) Admin (시스템 관리자)**

* 전문가 신청 승인/거절
* 회원 권한 변경(User↔Expert↔Content↔Admin)
* 통계 대시보드:

  * `plant_completion_stats` (종별 졸업률)
  * `point_distribution` (포인트 분포)
  * `active_department_stats` (학과별 활동/평균포인트)
* 최근 활동/트랜잭션 로그 조회

---

# 4. 🧠 **주요 SQL 기능 활용 (학습 내용 완전 충족)**

(Project Introduction 4페이지 요구사항 ✔ )

### ✔ **DML (INSERT / UPDATE / DELETE)**

* 퀴즈 시도 insert
* 포인트 지급/차감 update
* 팁 수정/삭제
* 콘텐츠 CRUD

### ✔ **SFW, JOIN, ORDER BY, GROUP BY, HAVING**

* 도감 검색, 정렬
* 관리자 통계(완주율, 포인트 분포, 학과별 통계)

### ✔ **Subquery**

```sql
SELECT MAX(step_order)
FROM species_step
WHERE species_id = (SELECT species_id FROM species_step WHERE step_id = %s)
```

### ✔ **Transaction (Commit / Rollback)**

* 정답 처리
* 부활 처리(FORCE_PASS)
* 초기화(reset)
* 신고 처리(hide/unhide)
  → 기능 단위 ACID 보장

### ✔ **View 활용**

* `plant_completion_stats`
* `point_distribution`
* `active_department_stats`

### ✔ **Authorization**

* 앱 레벨 RBAC(User/Expert/Content/Admin)
* DB 레벨 role 생성: `app_admin`, `app_readonly`

### ✔ **Index (권장 요구사항 충족)**

* `idx_species_name`
* `idx_userplant_user`
* `idx_request_status`
* `idx_tx_user_time`

---

# 5. 🗃️ **데이터베이스 스키마 (최종 ERD)**

<img width="751" height="787" alt="스크린샷 2025-12-07 062501" src="https://github.com/user-attachments/assets/f5a8a429-5f5a-476e-b46a-5c88ee6542f7" />

> 📌 아래는 요약된 ER 구조(README용).

### 주요 테이블

* `user_account`

  * 로그인 정보, 학번, 이름, 학과, 역할(`User/Expert/Content/Admin`), 포인트, 생성일 등
  * `CHECK(points >= 0)`, `UNIQUE(login_id)` 제약 포함

* `plant_species`

  * 도감의 식물 종 정보(이름, 카테고리, 난이도, 일조량, 설명, 이미지 URL 등)

* `species_step`

  * 종별 성장 단계 템플릿 (단계 순서, 단계 이름, 퀴즈 질문/정답/해설)
  * `UNIQUE(species_id, step_order)`로 1종 내 단계 순서 유일성 보장

* `user_plant`

  * 사용자가 실제로 키우는 식물 인스턴스
  * 유저-식물 쌍에 대해 `UNIQUE(user_id, species_id)`
  * 현재 단계, 완주 여부, 생성일

* `quiz_attempt`

  * 각 퀴즈 시도에 대한 로그 (정답 여부, 이어하기 사용 여부, 시도 시각)

* `transaction_log`

  * 포인트 변동 내역 (퀴즈 보상, 패널티, 강제 통과 등), 시각

* `plant_request`

  * 유저가 신청한 “도감에 없는 식물” 요청 목록 (대기/완료/반려 상태)

* `expert_application`

  * 전문가 등급 신청 내역 및 승인/거절 상태

* `expert_tip`

  * 전문가의 식물별 팁, 숨김 여부(`is_hidden`) 포함

* `tip_report`

  * 일반 사용자의 팁 신고 내역(어떤 팁, 신고자, 사유, 신고 시각)

* `game_config`

  * 게임 파라미터 (`revive_cost`, `quiz_reward` 등) 키-값 형태 저장

* `audit_log`

  * 콘텐츠 관리자/관리자에 의한 주요 작업 로그
    (액션 타입, 대상 ID, 상세 내용, 시각 등)

### 인덱스 & 뷰

* **Indexes**

  * `idx_species_name` (`plant_species.common_name`)
  * `idx_userplant_user` (`user_plant.user_id`)
  * `idx_request_status` (`plant_request.status`)
  * `idx_tx_user_time` (`transaction_log.user_id, logged_at`)

* **Views**

  * `plant_completion_stats`

    * 종별 전체 사용자 수, 완주자 수, 완주율(%) 집계
  * `point_distribution`

    * 포인트 구간별 유저 수 (예: 0~999, 1000~1999 …)
  * `active_department_stats`

    * 학과별 활성 사용자 수와 평균 포인트, `HAVING` 절 사용


### 제약조건

* PK: 모든 테이블 serial/bigserial
* FK: 대부분 ON DELETE CASCADE
* UNIQUE(user_id, species_id)
* CHECK(points >= 0)
* CHECK(role IN …)
* CHECK(status IN …)

### Authorization

* Admin만 role 변경 가능
* Content만 plant/step/quiz CRUD 가능
* Expert만 tip CUD
* User는 read/search only

---

# 6. 📊 **통계 및 시각화 (View 기반)**

Admin 페이지에서 조회

### ✔ 식물별 졸업률 (plant_completion_stats)

* GROUP BY + FILTER + CASE
* Streamlit bar chart 시각화

### ✔ 포인트 분포 (point_distribution)

* 0~999 / 1000~1999 / 2000~2999 buckets
* bar chart 가능

### ✔ 학과별 활동 통계 (active_department_stats)

* GROUP BY department
* HAVING COUNT(user_id) ≥ 1

---

# 7. 🧪 **트랜잭션 예시 (핵심 구현)**

### ✔ 정답 처리

```sql
BEGIN;
INSERT INTO quiz_attempt ...;
UPDATE user_account SET points = points + reward;
INSERT INTO transaction_log ...;
UPDATE user_plant SET current_step = current_step + 1;
COMMIT;
```

### ✔ 부활 처리

```sql
BEGIN;
SELECT points FROM user_account FOR UPDATE;
UPDATE user_account SET points = points - revive_cost;
INSERT INTO transaction_log ...;
UPDATE user_plant SET current_step = current_step + 1;
COMMIT;
```

→ **원자성 + 동시성 제어** 완전 충족.

---

# 8. 🎮 **주요 화면 구성 및 📖 사용 방법**

### ✔ 홈 / 도감 검색

* 상세 필터(난이도, 정렬)
* 팁 조회 + 신고
* 없는 식물 요청

### ✔ 내 식물 키우기

* 단계별 OX 퀴즈
* 꽃비 애니메이션 효과
* 부활/초기화 선택

### ✔ 전문가 페이지

* 팁 작성
* 내가 쓴 팁 관리(수정/삭제)

### ✔ 콘텐츠 관리자

* 식물 CRUD
* 퀴즈 CRUD
* 취약 팁 신고 처리
* 경제 설정 관리
* 감사 로그 조회

### ✔ 시스템 관리자

* 통계 그래프
* 권한 관리
* 사용자 검색

### 1. 로그인 / 회원가입

1. 상단 우측의 **“로그인 / 회원가입”** 버튼 클릭
2. 탭에서

   * 기존 계정 로그인 또는
   * 새 계정 생성 (아이디, 비밀번호, 이름, 학번, 학과 입력)
3. 로그인 후, 상단에 **역할 배지 + 포인트 + 학과/학번** 표시

### 2. 도감 검색 & 식물 신청

* 상단 메뉴: **🏠 홈 / 도감** 진입
* 이름/난이도/정렬 기준을 선택하여 검색
* 결과가 없으면:

  * 로그인 상태에서 “식물 등록 신청” 폼으로 **plant_request** 생성
  * 콘텐츠 관리자가 검토 후 실제 도감에 추가

### 3. 내 식물 키우기 (게임)

* 메뉴에서 **🌿 내 식물 키우기** 선택
* 도감 화면에서 “키우기 시작” 버튼을 누르면 `user_plant`에 등록
* 게임 화면:

  * 현재 성장 단계와 퀴즈가 표시됨
  * O/X 선택 → 제출
  * 정답:

    * 포인트 +100
    * 다음 단계로 전이 또는 완주 처리
    * 축하 꽃비 애니메이션
  * 오답:

    * 1단계: 포인트 50 차감
    * 2단계 이상:

      * 포인트 300 사용해 **강제 통과**
      * 혹은 **무료 초기화**로 1단계부터 다시 진행

### 4. 전문가 팁

* 전문가로 승급된 사용자는 **🎓 전문가: 팁 작성** 메뉴 이용
* 특정 식물을 선택하고 팁 제목/내용을 입력해 등록
* 자신의 팁 목록을 조회하고, 내용 수정 및 삭제 가능
* 일반 사용자는 도감 상세 화면에서 해당 식물의 전문가 팁을 열람할 수 있고,
  부적절한 팁은 신고할 수 있습니다.

### 5. 콘텐츠 관리

* 콘텐츠 관리자/관리자는 **📝 콘텐츠 관리 (식물/경제)** 메뉴 사용

기능 요약:

* 식물 신청 내역 처리 (승인/반려)
* 새로운 식물 추가, 기존 식물 정보 수정, 삭제
* 성장 단계 및 퀴즈 추가/수정
* 이어하기 비용 / 퀴즈 보상 등 경제 파라미터 조정
* 전문가 팁 신고 처리 및 숨김/복구
* 감사 로그(Audit Log) 조회

### 6. 시스템 관리

* 시스템 관리자(Admin)는 **⚙️ 시스템 관리 (계정/로그)** 메뉴 사용

기능 요약:

* `plant_completion_stats` 뷰를 활용한 **식물별 완주율 통계**
* 최근 포인트 트랜잭션 로그 모니터링
* 전문가 신청 승인/거절 및 전체 사용자 역할 변경

---
