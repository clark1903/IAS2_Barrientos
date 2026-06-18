USE insightedge_db;

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
    'pbkdf2_sha256$1000000$YRAux09WRdpo$NpYIkbABUXRn3xCzCX4Yq4JlWwPgKwmIO6CKmsFlWmA=',
    NULL,
    0,
    'professor@tip.edu.ph',
    'Professor',
    'User',
    'professor@tip.edu.ph',
    0,
    1,
    NOW(6)
WHERE NOT EXISTS (
    SELECT 1 FROM auth_user WHERE email = 'professor@tip.edu.ph'
);

UPDATE auth_user
SET
    username = 'professor@tip.edu.ph',
    email = 'professor@tip.edu.ph',
    password = 'pbkdf2_sha256$1000000$YRAux09WRdpo$NpYIkbABUXRn3xCzCX4Yq4JlWwPgKwmIO6CKmsFlWmA=',
    first_name = 'Professor',
    last_name = 'User',
    is_active = 1,
    is_staff = 0,
    is_superuser = 0
WHERE username = 'professor'
   OR email IN ('professor@tip.edu.ph', 'professor@insightedge.edu');

INSERT INTO accounts_profile (role, user_id, mfa_enabled, mfa_secret)
SELECT 'Professor', id, 0, ''
FROM auth_user
WHERE email = 'professor@tip.edu.ph'
AND NOT EXISTS (
    SELECT 1 FROM accounts_profile WHERE user_id = auth_user.id
);

UPDATE accounts_profile p
JOIN auth_user u ON p.user_id = u.id
SET p.role = 'Professor'
WHERE u.email = 'professor@tip.edu.ph';

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
    'pbkdf2_sha256$1000000$ISFxzRAwvcUY$IWXopetI86HcmBn5qbN7QiSwBxBGLg+PVBgV9Ji6BoA=',
    NULL,
    0,
    'counselor@tip.edu.ph',
    'Counselor',
    'User',
    'counselor@tip.edu.ph',
    0,
    1,
    NOW(6)
WHERE NOT EXISTS (
    SELECT 1 FROM auth_user WHERE email = 'counselor@tip.edu.ph'
);

UPDATE auth_user
SET
    username = 'counselor@tip.edu.ph',
    email = 'counselor@tip.edu.ph',
    password = 'pbkdf2_sha256$1000000$ISFxzRAwvcUY$IWXopetI86HcmBn5qbN7QiSwBxBGLg+PVBgV9Ji6BoA=',
    first_name = 'Counselor',
    last_name = 'User',
    is_active = 1,
    is_staff = 0,
    is_superuser = 0
WHERE username IN ('counselor', 'council')
   OR email IN ('counselor@tip.edu.ph', 'counselor@insightedge.edu');

INSERT INTO accounts_profile (role, user_id, mfa_enabled, mfa_secret)
SELECT 'Counselor', id, 0, ''
FROM auth_user
WHERE email = 'counselor@tip.edu.ph'
AND NOT EXISTS (
    SELECT 1 FROM accounts_profile WHERE user_id = auth_user.id
);

UPDATE accounts_profile p
JOIN auth_user u ON p.user_id = u.id
SET p.role = 'Counselor'
WHERE u.email = 'counselor@tip.edu.ph';
