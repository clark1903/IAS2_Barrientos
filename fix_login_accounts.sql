USE insightedge_db;

UPDATE auth_user
SET
    username = 'admin',
    email = 'admin@tip.edu.ph',
    password = 'pbkdf2_sha256$1000000$D2GgPE0dSOMJ$ug0foN5BqTjR/r3iK6uzMrQ1ikPlCbC7zvdnuvtA7Lo=',
    is_active = 1,
    is_staff = 1,
    is_superuser = 1
WHERE id = 1;

UPDATE accounts_profile
SET role = 'Admin'
WHERE user_id = 1;

INSERT INTO auth_user (
    password,
    last_login,
    is_superuser,
    username,
    first_name,
    last_name,
    email,
    is_staff,
    is_active,
    date_joined
)
SELECT
    'pbkdf2_sha256$1000000$rX6iQbHMmfKl$gzUu2Rvb23na2iA9/f7Ta3ZOn90iZg2G5Oa7kTp4XA4=',
    NULL,
    1,
    'mcgbarrientos@tip.edu.ph',
    'Clark',
    'Barrientos',
    'mcgbarrientos@tip.edu.ph',
    1,
    1,
    NOW(6)
WHERE NOT EXISTS (
    SELECT 1 FROM auth_user WHERE email = 'mcgbarrientos@tip.edu.ph'
);

UPDATE auth_user
SET
    username = 'mcgbarrientos@tip.edu.ph',
    email = 'mcgbarrientos@tip.edu.ph',
    password = 'pbkdf2_sha256$1000000$rX6iQbHMmfKl$gzUu2Rvb23na2iA9/f7Ta3ZOn90iZg2G5Oa7kTp4XA4=',
    is_active = 1,
    is_staff = 1,
    is_superuser = 1
WHERE email = 'mcgbarrientos@tip.edu.ph';

INSERT INTO accounts_profile (role, user_id, mfa_enabled, mfa_secret)
SELECT 'Admin', id, 0, ''
FROM auth_user
WHERE email = 'mcgbarrientos@tip.edu.ph'
AND NOT EXISTS (
    SELECT 1 FROM accounts_profile WHERE user_id = auth_user.id
);

UPDATE accounts_profile p
JOIN auth_user u ON p.user_id = u.id
SET p.role = 'Admin'
WHERE u.email = 'mcgbarrientos@tip.edu.ph';
