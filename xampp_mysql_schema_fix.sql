USE insightedge_db;

ALTER TABLE accounts_profile
    ADD COLUMN IF NOT EXISTS mfa_enabled tinyint(1) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS mfa_secret varchar(32) NOT NULL DEFAULT '';

ALTER TABLE students_academicrecord
    ADD COLUMN IF NOT EXISTS behavioral_incidents varchar(50) NOT NULL DEFAULT 'None',
    ADD COLUMN IF NOT EXISTS participation varchar(50) NOT NULL DEFAULT 'Good';

ALTER TABLE students_academicrecord
    DROP COLUMN IF EXISTS behavior_flag;

CREATE TABLE IF NOT EXISTS accounts_auditlog (
    id bigint(20) NOT NULL AUTO_INCREMENT,
    action varchar(64) NOT NULL,
    model_name varchar(120) NOT NULL,
    object_pk varchar(64) NOT NULL DEFAULT '',
    ip_address char(39) DEFAULT NULL,
    before_state json NOT NULL,
    after_state json NOT NULL,
    record_hash varchar(64) NOT NULL,
    created_at datetime(6) NOT NULL,
    actor_id int(11) DEFAULT NULL,
    PRIMARY KEY (id),
    KEY accounts_auditlog_actor_id_fk_auth_user_id (actor_id),
    CONSTRAINT accounts_auditlog_actor_id_fk_auth_user_id
        FOREIGN KEY (actor_id) REFERENCES auth_user (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS reports_casecomment (
    id bigint(20) NOT NULL AUTO_INCREMENT,
    message longtext NOT NULL,
    created_at datetime(6) NOT NULL,
    author_id int(11) NOT NULL,
    report_id bigint(20) NOT NULL,
    PRIMARY KEY (id),
    KEY reports_casecomment_author_id_fk_auth_user_id (author_id),
    KEY reports_casecomment_report_id_fk_reports_report_id (report_id),
    CONSTRAINT reports_casecomment_author_id_fk_auth_user_id
        FOREIGN KEY (author_id) REFERENCES auth_user (id),
    CONSTRAINT reports_casecomment_report_id_fk_reports_report_id
        FOREIGN KEY (report_id) REFERENCES reports_report (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO django_migrations (app, name, applied)
SELECT 'accounts', '0002_profile_mfa_fields', NOW(6)
WHERE NOT EXISTS (
    SELECT 1 FROM django_migrations
    WHERE app = 'accounts' AND name = '0002_profile_mfa_fields'
);

INSERT INTO django_migrations (app, name, applied)
SELECT 'accounts', '0003_auditlog', NOW(6)
WHERE NOT EXISTS (
    SELECT 1 FROM django_migrations
    WHERE app = 'accounts' AND name = '0003_auditlog'
);

INSERT INTO django_migrations (app, name, applied)
SELECT 'students', '0002_remove_academicrecord_behavior_flag_and_more', NOW(6)
WHERE NOT EXISTS (
    SELECT 1 FROM django_migrations
    WHERE app = 'students' AND name = '0002_remove_academicrecord_behavior_flag_and_more'
);

INSERT INTO django_migrations (app, name, applied)
SELECT 'reports', '0002_casecomment', NOW(6)
WHERE NOT EXISTS (
    SELECT 1 FROM django_migrations
    WHERE app = 'reports' AND name = '0002_casecomment'
);
