-- [1. 기존 테이블/뷰 삭제]
DROP VIEW IF EXISTS plant_completion_stats CASCADE;
DROP VIEW IF EXISTS point_distribution CASCADE;
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
create table user_account (
    user_id        serial primary key,
    login_id       varchar(50) not null unique,
    password_hash  varchar(255) not null,
    student_id     varchar(20),
    name           varchar(50),
    department     varchar(100),
    role           varchar(20) not null check (role in ('User','Expert','Content','Admin')),
    points         int not null default 1000 check (points >= 0),
    created_at     timestamp not null default now()
);

-- 2. 도감 - 종
create table plant_species (
    species_id     serial primary key,
    common_name    varchar(100) not null unique,
    category       varchar(20) not null,
    difficulty     smallint,
    sun_level      varchar(20),
    image_url      varchar(255),
    description    text  -- [추가됨] 식물 상세 설명 (긴 글)
);

-- 3. 성장 단계 + 퀴즈
create table species_step (
    step_id        serial primary key,
    species_id     int not null references plant_species(species_id) on delete cascade,
    step_order     int not null,
    stage_name     varchar(20) not null,
    quiz_question  text not null,
    correct_answer boolean not null,
    explanation    text,
    unique (species_id, step_order)
);

-- 4. 사용자가 키우는 식물 인스턴스
create table user_plant (
    user_plant_id   serial primary key,
    user_id         int not null references user_account(user_id) on delete cascade,
    species_id      int not null references plant_species(species_id) on delete cascade,
    current_step    int not null default 1,
    is_completed    boolean not null default false,
    created_at      timestamp not null default now(),
    unique (user_id, species_id)
);

-- 5. 퀴즈 시도 로그
create table quiz_attempt (
    attempt_id      serial primary key,
    user_plant_id   int not null references user_plant(user_plant_id) on delete cascade,
    step_id         int not null references species_step(step_id) on delete cascade,
    is_correct      boolean not null,
    used_continue   boolean not null default false,
    attempted_at    timestamp not null default now()
);

-- 6. 포인트(머니) 트랜잭션 로그
create table transaction_log (
    log_id          bigserial primary key,
    user_id         int not null references user_account(user_id) on delete cascade,
    transaction_type varchar(20) not null,
    amount          int not null,
    logged_at       timestamp not null default now()
);

-- 7. 정보 신청
create table plant_request (
    request_id      serial primary key,
    requester_id    int references user_account(user_id),
    plant_name      varchar(100) not null,
    status          varchar(20) not null default 'PENDING'
                    check (status in ('PENDING','DONE','REJECTED')),
    created_at      timestamp not null default now(),
    processed_by    int references user_account(user_id)
);

-- 8. 전문가 신청
create table expert_application (
    user_id         int primary key references user_account(user_id) on delete cascade,
    request_text    text not null,
    status          varchar(20) not null default 'PENDING'
                    check (status in ('PENDING','APPROVED','REJECTED')),
    decided_by      int references user_account(user_id),
    decided_at      timestamp
);

-- 9. 전문가 팁 (수정됨)
create table expert_tip (
    tip_id          serial primary key,
    expert_id       int not null references user_account(user_id) on delete cascade,
    species_id      int not null references plant_species(species_id) on delete cascade,
    title           varchar(100) not null,
    content         text not null,
    is_hidden       boolean default false, -- [추가됨] 신고/부적절 글 숨김 여부
    created_at      timestamp not null default now()
);

-- 10. 감사 로그 (Audit Log) - [신규 테이블]
create table audit_log (
    log_id      serial primary key,
    admin_id    int references user_account(user_id), -- 누가 (관리자)
    action_type varchar(50) not null,                 -- 무슨 행동을
    target_id   int,                                  -- 대상 ID (식물ID, 팁ID 등)
    details     text,                                 -- 상세 내용
    ip_address  varchar(50),                          -- 접속 IP (선택사항)
    created_at  timestamp default now()               -- 언제
);

-- 11. 게임 설정
create table game_config (
    config_key      varchar(40) primary key,
    config_value    varchar(64) not null
);

-- 12. 인덱스
create index idx_species_name on plant_species(common_name);
create index idx_userplant_user on user_plant(user_id);
create index idx_request_status on plant_request(status);
create index idx_tx_user_time on transaction_log(user_id, logged_at);
create index idx_audit_time on audit_log(created_at); -- 감사 로그 조회용 인덱스

-- 13. 통계용 VIEW
create or replace view plant_completion_stats as
select
  s.species_id,
  s.common_name,
  s.category,
  count(distinct up.user_id) as total_users,
  count(distinct up.user_id) filter (where up.is_completed) as completed_users,
  case
    when count(distinct up.user_id) = 0 then 0
    else round(
      100.0 * count(distinct up.user_id) filter (where up.is_completed)
      / count(distinct up.user_id)
    , 1)
  end as completion_rate
from plant_species s
left join user_plant up on s.species_id = up.species_id
group by s.species_id, s.common_name, s.category;

create or replace view point_distribution as
select
  (points / 1000) * 1000 as bucket_start,
  count(*) as user_count
from user_account
group by bucket_start
order by bucket_start;

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