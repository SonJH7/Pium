# 🌱 **Pium: 대학생 인터랙티브 식물 키우기 & 도감 시스템**

### **Gamified Plant Encyclopedia + Growth Simulation using PostgreSQL & Streamlit**

📌 배포 주소: **[https://pium001.streamlit.app/](https://pium001.streamlit.app/)**

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

---

# 2. 🌟 **프로젝트 특징 (Key Features)**

이 프로젝트는 단순 CRUD가 아니라 **데이터베이스 강의의 모든 핵심 요소를 실제 서비스 수준으로 구현**했다는 점에서 높은 평가가 가능함.

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

# 3. 🧩 **사용자 역할(RBAC)** — *요구사항 100% 충족*

(Project Introduction에서 역할별 기능 설명 요구 ✔ )
(Proposal Report 역할도 모두 반영 ✔ )

### 👤 **1) User (일반 사용자)**

* 도감 검색/필터/정렬
* 식물 심기 (`user_plant`)
* 단계별 OX 퀴즈 풀이
* 포인트 획득/차감
* 2단계 이상 실패 시

  * 포인트 결제(continue) 또는
  * 무료 초기화(reset)
* 전문가 신청 (`expert_application INSERT`)
* 전문가 팁 조회 + 팁 신고

---

### 🎓 **2) Expert (전문가)**

* User 기능 모두 포함
* 전문가 팁 작성 (`expert_tip INSERT`)
* 팁 수정/삭제 (UPDATE/DELETE)

---

### 📝 **3) Content Manager (콘텐츠 관리자)**

* 도감 식물 CRUD
* 퀴즈 단계 CRUD
* 팁 신고 관리: 숨김/복구
* 경제 파라미터 설정 (`game_config`)
* 모든 조작 `audit_log` 기록

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

Proposal Report의 스키마 요구사항과 완전 일치함 ✔ 

> 📌 아래는 요약된 ER 구조(README용).
> 실제 보고서에는 그림 형태 ERD 포함 권장.

### 핵심 엔티티

* `user_account`
* `plant_species`
* `species_step`
* `user_plant`
* `quiz_attempt`
* `transaction_log`
* `expert_tip`, `tip_report`
* `plant_request`, `expert_application`
* `audit_log`
* `game_config`

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

# 8. 🎮 **주요 화면 구성 (Streamlit)**

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

---
