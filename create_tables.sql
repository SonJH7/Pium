-- [1. 기존 테이블/뷰 삭제]
DROP VIEW IF EXISTS plant_completion_stats CASCADE;
DROP VIEW IF EXISTS point_distribution CASCADE;
DROP TABLE IF EXISTS tip_report CASCADE;       
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS audit_log cascade;        
DROP TABLE IF EXISTS quiz_attempt CASCADE;
DROP TABLE IF EXISTS user_plant CASCADE;
DROP TABLE IF EXISTS expert_tip CASCADE;
DROP TABLE IF EXISTS transaction_log CASCADE;
DROP TABLE IF EXISTS plant_request CASCADE;
DROP TABLE IF EXISTS expert_application CASCADE;
DROP TABLE IF EXISTS game_config CASCADE;
DROP TABLE IF EXISTS species_step CASCADE;
DROP TABLE IF EXISTS plant_species CASCADE;
DROP TABLE IF EXISTS user_account CASCADE;

-- [2. 테이블 생성]
-- 1. 사용자 계정
CREATE TABLE user_account (
    user_id        SERIAL PRIMARY KEY,
    login_id       VARCHAR(50) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    student_id     VARCHAR(20),
    name           VARCHAR(50),
    department     VARCHAR(100),
    role           VARCHAR(20) NOT NULL CHECK (role IN ('User','Expert','Content','Admin')),
    points         INT NOT NULL DEFAULT 1000 CHECK (points >= 0),
    expert_request TEXT,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 2. 도감 - 종 (설명 컬럼 포함)
CREATE TABLE plant_species (
    species_id     SERIAL PRIMARY KEY,
    common_name    VARCHAR(100) NOT NULL UNIQUE,
    scientific_name VARCHAR(150),
    category       VARCHAR(20) NOT NULL,
    difficulty     SMALLINT,
    sun_level      VARCHAR(20),
    image_url      VARCHAR(255),
    description    TEXT  -- [추가됨]
);

-- 3. 성장 단계 + 퀴즈
CREATE TABLE species_step (
    step_id        SERIAL PRIMARY KEY,
    species_id     INT NOT NULL REFERENCES plant_species(species_id) ON DELETE CASCADE,
    step_order     INT NOT NULL,
    stage_name     VARCHAR(20) NOT NULL,
    quiz_question  TEXT NOT NULL,
    correct_answer BOOLEAN NOT NULL,
    explanation    TEXT,
    UNIQUE (species_id, step_order)
);

-- 4. 사용자가 키우는 식물 인스턴스
CREATE TABLE user_plant (
    user_plant_id   SERIAL PRIMARY KEY,
    user_id         INT NOT NULL REFERENCES user_account(user_id) ON DELETE CASCADE,
    species_id      INT NOT NULL REFERENCES plant_species(species_id) ON DELETE CASCADE,
    current_step    INT NOT NULL DEFAULT 1,
    is_completed    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, species_id)
);

-- 5. 퀴즈 시도 로그
CREATE TABLE quiz_attempt (
    attempt_id      SERIAL PRIMARY KEY,
    user_plant_id   INT NOT NULL REFERENCES user_plant(user_plant_id) ON DELETE CASCADE,
    step_id         INT NOT NULL REFERENCES species_step(step_id) ON DELETE CASCADE,
    is_correct      BOOLEAN NOT NULL,
    used_continue   BOOLEAN NOT NULL DEFAULT FALSE,
    attempted_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 6. 포인트(머니) 트랜잭션 로그
CREATE TABLE transaction_log (
    log_id          BIGSERIAL PRIMARY KEY,
    user_id         INT NOT NULL REFERENCES user_account(user_id) ON DELETE CASCADE,
    transaction_type VARCHAR(20) NOT NULL,
    amount          INT NOT NULL,
    logged_at       TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 7. 정보 신청
CREATE TABLE plant_request (
    request_id      SERIAL PRIMARY KEY,
    requester_id    INT REFERENCES user_account(user_id),
    plant_name      VARCHAR(100) NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','DONE','REJECTED')),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    processed_by    INT REFERENCES user_account(user_id)
);

-- 8. 전문가 신청
CREATE TABLE expert_application (
    user_id         INT PRIMARY KEY REFERENCES user_account(user_id) ON DELETE CASCADE,
    request_text    TEXT NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','APPROVED','REJECTED')),
    decided_by      INT REFERENCES user_account(user_id),
    decided_at      TIMESTAMP
);

-- 9. 전문가 팁 (숨김 기능 포함)
CREATE TABLE expert_tip (
    tip_id          SERIAL PRIMARY KEY,
    expert_id       INT NOT NULL REFERENCES user_account(user_id) ON DELETE CASCADE,
    species_id      INT NOT NULL REFERENCES plant_species(species_id) ON DELETE CASCADE,
    step_id         INT REFERENCES species_step(step_id),
    title           VARCHAR(100) NOT NULL,
    content         TEXT NOT NULL,
    is_hidden       BOOLEAN DEFAULT FALSE, -- [추가됨]
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 10. [추가] 팁 신고 내역 (expert_tip 뒤에 위치해야 함)
CREATE TABLE tip_report (
    report_id       SERIAL PRIMARY KEY,
    tip_id          INT NOT NULL REFERENCES expert_tip(tip_id) ON DELETE CASCADE,
    reporter_id     INT NOT NULL REFERENCES user_account(user_id) ON DELETE CASCADE,
    reason          TEXT NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 11. 게임 설정
CREATE TABLE game_config (
    config_key      VARCHAR(40) PRIMARY KEY,
    config_value    VARCHAR(64) NOT NULL
);

-- 12. [추가] 감사 로그 (Audit Log)
CREATE TABLE audit_log (
    log_id          SERIAL PRIMARY KEY,
    admin_id        INT REFERENCES user_account(user_id),
    action_type     VARCHAR(50) NOT NULL,
    target_id       INT,
    details         TEXT,
    ip_address      VARCHAR(50),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 13. 인덱스
CREATE INDEX idx_species_name ON plant_species(common_name);
CREATE INDEX idx_userplant_user ON user_plant(user_id);
CREATE INDEX idx_request_status ON plant_request(status);
CREATE INDEX idx_tx_user_time ON transaction_log(user_id, logged_at);

-- 14. 통계용 VIEW
CREATE OR REPLACE VIEW plant_completion_stats AS
SELECT
  s.species_id,
  s.common_name,
  s.category,
  COUNT(DISTINCT up.user_id) AS total_users,
  COUNT(DISTINCT up.user_id) FILTER (WHERE up.is_completed) AS completed_users,
  CASE
    WHEN COUNT(DISTINCT up.user_id) = 0 THEN 0
    ELSE ROUND(
      100.0 * COUNT(DISTINCT up.user_id) FILTER (WHERE up.is_completed)
      / COUNT(DISTINCT up.user_id)
    , 1)
  END AS completion_rate
FROM plant_species s
LEFT JOIN user_plant up ON s.species_id = up.species_id
GROUP BY s.species_id, s.common_name, s.category;

CREATE OR REPLACE VIEW point_distribution AS
SELECT
  (points / 1000) * 1000 AS bucket_start,
  COUNT(*) AS user_count
FROM user_account
GROUP BY bucket_start
ORDER BY bucket_start;

-- [4. 기초 데이터 입력]
INSERT INTO user_account(login_id, password_hash, student_id, name, department, role, points) VALUES
('admin',   '1234', '999999999', '관리자',   '대학본부',       'Admin', 99999),
('user1',   '1234', '202312345', '김철수',   '컴퓨터공학과',   'User',  1000),
('expert1', '1234', '202011111', '박박사',   '식물의학전공',   'Expert', 2000),
('content', '1234', '99990001', '콘텐츠 관리자',     '교육운영팀',     'Content', 0);

INSERT INTO game_config(config_key, config_value) VALUES
('revive_cost', '300'),
('quiz_reward', '100');

INSERT INTO plant_species(common_name, category, difficulty, sun_level, image_url) VALUES
('몬스테라', 'leaf', 2, 'Mid', 'https://i.namu.wiki/i/ddIQpxcFo4JYdcinRHH9BCVawzyBK7QiqkvNbz_ELjl62GvRcpaJimIOfxiAlxYTYaBIUIOC_iTCF1IlNOIB1A.webp');

INSERT INTO species_step(species_id, step_order, stage_name, quiz_question, correct_answer, explanation) VALUES
(1, 1, 'Seed',   '몬스테라는 직사광선을 아주 좋아한다 (O/X)?', FALSE, '잎이 탈 수 있으니 간접광이 좋습니다.'),
(1, 2, 'Sprout', '몬스테라는 물을 줄 때 흙이 마른 것을 확인해야 한다 (O/X)?', TRUE, '과습에 주의해야 합니다.');