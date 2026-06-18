# InsightEdge

InsightEdge is an academic early-risk detection and reporting system built with Django, MySQL/MariaDB, Bootstrap 5, and Chart.js. It supports role-based access (Admin / Professor / Counselor) and a rule-based risk scoring logic.

## Prerequisites

- Python 3.11+
- XAMPP MySQL/MariaDB running on `127.0.0.1:3306`
- A MySQL database named `insightedge_db`

## Setup (Windows / PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Set-up:

deactivate
cd "C:\Users\Clark Barrientos\Downloads\WEBSYS2-2 Final Project-20260609T051144Z-3-001\WEBSYS2-2 Final Project"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
pip install --force-reinstall -r requirements.txt
py manage.py migrate
py manage.py runserver
Create a `.env` file in the project root based on `.env.example`.

## Database

Start XAMPP, then start **MySQL**. If the database does not exist yet, create it in phpMyAdmin:

```sql
CREATE DATABASE insightedge_db;
```

The project defaults to the usual XAMPP MySQL login:

```env
MYSQL_DATABASE=insightedge_db
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
```

If your MySQL root account has a password, set it in `.env`.

Then run the Django setup:

```powershell
python manage.py migrate --fake-initial
python manage.py seed_users
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Default Accounts

These are local development accounts only. Change their passwords before using the system in a real school environment.

| Role | Email | Password | Access |
| --- | --- | --- | --- |
| Admin | `admin@tip.edu.ph` | `admin@123` | System dashboard, Django admin, users, students, reports |
| Admin | `mcgbarrientos@tip.edu.ph` | `@ClarkPogi2026` | System dashboard, Django admin, users, students, reports |
| Professor | `professor@tip.edu.ph` | `professor@123` | Professor dashboard, student records, report submission |
| Counselor | `counselor@tip.edu.ph` | `counselor@123` | Counselor dashboard, case review, interventions |

The current project does not implement a Student login role. Students are protected records managed by Admin, Professor, and Counselor users.


## Test Accounts

Admin
Email: admin@tip.edu.ph
Password: admin@123

Your Admin
Email: mcgbarrientos@tip.edu.ph
Password: @ClarkPogi2026


Professor
Email: professor@tip.edu.ph
Password: professor@123


Counselor
Email: counselor@tip.edu.ph
Password: counselor@123

## Security Features

InsightEdge includes the following security controls for the Information Assurance and Security 2 requirement. These controls are implemented in the Django application code and configuration.

### 1. Authentication Using Institutional Email

The login system uses email-based authentication instead of plain usernames. The authentication backend accepts only accounts with the `@tip.edu.ph` domain.

Purpose:
- Prevents non-institutional email accounts from accessing the system.
- Makes each account easier to associate with a real organization identity.
- Reduces accidental account creation using personal or unrelated email domains.

Implementation:
- `accounts.auth_backends.EmailBackend` checks the email domain.
- `accounts.forms.EmailAuthenticationForm` validates that the login email ends with `@tip.edu.ph`.
- Passwords are verified through Django's secure password-checking system.

### 2. Password Hashing

Passwords are not stored as readable text in the database. Django stores password hashes using PBKDF2 with SHA-256.

Purpose:
- Protects user passwords if the database is viewed or leaked.
- Prevents administrators from seeing a user's real password.
- Supports password reset without exposing the original password.

Important note:
- A password can be changed, but it cannot be recovered from the database because only the hash is stored.

### 3. Role-Based Access Control

The system uses role-based access control for Admin, Professor, and Counselor users.

Role permissions:
- Admin can access the admin dashboard and Django admin site.
- Professor can manage student academic records and submit reports.
- Counselor can review reports, update case status, and record interventions.

Purpose:
- Enforces least privilege.
- Prevents users from accessing pages outside their assigned responsibility.
- Separates academic reporting work from counseling/case management work.

Implementation:
- Roles are stored in `accounts.Profile.role`.
- Function views use `@role_required(...)`.
- Class-based views use `RoleRequiredMixin`.
- Admin profiles are synchronized with Django's `is_staff` flag for Django admin access.

### 4. Multi-Step Login Verification

After a valid email and password login, the system sends a six-digit verification code before completing the session.

Purpose:
- Adds a second verification step after password authentication.
- Reduces the risk from a stolen password.
- Verifies that the login attempt can receive the generated code.

Implementation:
- `LoginView` stores a pending login user in the session.
- `_send_email_otp()` generates a random six-digit code.
- The code is stored as a secure hash, not as plain text.
- Codes expire after 10 minutes.
- `MFAVerifyView` completes login only after a valid code is entered.

Local development behavior:
- When `DJANGO_DEBUG=1` or email credentials are not configured, the code is printed in the terminal instead of sending a real email.

### 5. Login Rate Limiting

The system limits repeated POST requests to sensitive authentication routes.

Protected routes:
- `/login/`
- `/mfa/verify/`
- `/mfa/resend/`

Purpose:
- Slows down brute-force password guessing.
- Reduces repeated OTP guessing attempts.
- Helps protect the application from simple automated login abuse.

Implementation:
- `accounts.middleware.RateLimitMiddleware` tracks attempts by IP address using Django's cache.
- Excessive attempts receive HTTP `429 Too Many Requests`.
- The response includes a `Retry-After` header.

### 6. Audit Logging

Important user and data actions are recorded in an audit log.

Logged events include:
- Successful login
- Logout
- Failed login attempts
- Student create/update/delete
- Academic record create/update/delete
- Report create/update/delete
- Intervention create/update/delete

Purpose:
- Supports accountability and traceability.
- Helps administrators investigate suspicious activity.
- Provides evidence of who changed sensitive student or case data.

Implementation:
- `accounts.signals` listens for authentication and model events.
- `accounts.audit.log_audit_event()` writes events to `accounts_auditlog`.
- Each record stores actor, action, affected model, object ID, IP address, timestamp, before state, and after state.

### 7. Hash-Protected Audit Records

Each audit log record includes a SHA-256 HMAC hash based on the log contents and the Django secret key.

Purpose:
- Helps detect unauthorized modification of audit records.
- Supports integrity checking for security reviews.
- Makes the audit trail stronger than a normal plain log table.

Implementation:
- `accounts.audit.log_audit_event()` builds a structured payload.
- The payload is signed using HMAC-SHA256.
- The result is stored in the `record_hash` field.

### 8. Immutable Audit Model Behavior

Audit log entries cannot be edited through normal model saving once created.

Purpose:
- Prevents accidental modification of audit evidence.
- Preserves the historical meaning of logged events.

Implementation:
- `AuditLog.save()` raises an error if code tries to edit an existing audit log row.

### 9. CSRF Protection

The system uses Django's built-in Cross-Site Request Forgery protection.

Purpose:
- Prevents another website from silently submitting forms as a logged-in user.
- Protects login, logout, record creation, edits, deletes, and report actions.

Implementation:
- `django.middleware.csrf.CsrfViewMiddleware` is enabled.
- Templates use `{% csrf_token %}` in forms.
- `CSRF_COOKIE_HTTPONLY=True` prevents JavaScript from reading the CSRF cookie.

### 10. Secure Session Configuration

The system uses safer session behavior for authenticated users.

Configured protections:
- `SESSION_COOKIE_HTTPONLY=True`
- `SESSION_COOKIE_AGE=1800`
- `SESSION_EXPIRE_AT_BROWSER_CLOSE=True`
- `SESSION_SAVE_EVERY_REQUEST=True`

Purpose:
- Prevents JavaScript from reading session cookies.
- Automatically expires inactive sessions after 30 minutes.
- Ends sessions when the browser closes.
- Refreshes the timeout only while the user is actively using the system.

### 11. Clickjacking Protection

The system denies loading its pages inside frames.

Purpose:
- Prevents clickjacking attacks where an attacker hides the system inside another page.

Implementation:
- `X_FRAME_OPTIONS="DENY"`
- The Content Security Policy also uses `frame-ancestors 'none'`.

### 12. Browser Security Headers

The application sends additional browser security headers.

Headers:
- `Content-Security-Policy`
- `Permissions-Policy`
- `Cross-Origin-Opener-Policy`
- `Referrer-Policy`
- `X-Frame-Options`
- `X-Content-Type-Options`

Purpose:
- Limits where scripts, styles, fonts, images, forms, and frames can load from.
- Blocks access to browser features such as camera, microphone, geolocation, and payment APIs.
- Reduces information leakage through referrer data.
- Helps isolate the application from cross-origin browser risks.

Implementation:
- `accounts.middleware.SecurityHeadersMiddleware` adds project-specific headers.
- `django.middleware.security.SecurityMiddleware` adds Django security protections.

### 13. Protected Upload and File Handling Boundaries

The project stores uploaded/generated media under the configured `MEDIA_ROOT` and serves it only in development mode when `DEBUG=True`.

Purpose:
- Keeps uploaded files separate from source code.
- Avoids exposing development file serving behavior in production.

Implementation:
- `MEDIA_ROOT = BASE_DIR / "media"`
- `MEDIA_URL = "media/"`
- `insightedge.urls` serves media only when `settings.DEBUG` is enabled.

### 14. Environment-Based Configuration

Sensitive and environment-specific settings are read from `.env`.

Examples:
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- MySQL database credentials
- Email settings
- HTTPS/security cookie settings

Purpose:
- Avoids hard-coding deployment secrets directly in application code.
- Allows local and production settings to differ safely.
- Makes database and email credentials easier to rotate.

### 15. Optional Production HTTPS Hardening

The system includes settings that can be enabled when deployed with HTTPS.

Production recommendations:

```env
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_ALLOWED_HOSTS=your-domain.edu.ph
CSRF_TRUSTED_ORIGINS=https://your-domain.edu.ph
SECURE_SSL_REDIRECT=1
SESSION_COOKIE_SECURE=1
CSRF_COOKIE_SECURE=1
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=1
SECURE_HSTS_PRELOAD=1
```

Purpose:
- Forces HTTPS.
- Sends cookies only through HTTPS.
- Enables HSTS so browsers remember to use HTTPS.
- Restricts hostnames and trusted origins.

Do not enable HTTPS-only settings for local XAMPP testing unless the local site is actually running through HTTPS.

### 16. SQL Injection Resistance

The system is protected against basic SQL injection attempts because login and data access use Django forms and the Django ORM instead of manually combining user input into SQL strings.

Example attack payloads:
- `' OR '1'='1`
- `admin@tip.edu.ph' OR '1'='1`
- `" OR "1"="1`

Purpose:
- Prevents attackers from bypassing login by turning user input into a database condition.
- Keeps submitted form values treated as plain data, not executable SQL.
- Reduces risk from common authentication bypass payloads.

Implementation:
- Login input is validated by `accounts.forms.EmailAuthenticationForm`.
- The authentication backend searches users with `UserModel.objects.get(email__iexact=email)`.
- Django ORM safely parameterizes database queries.
- Password verification uses `user.check_password(password)` instead of SQL password comparison.

Expected behavior:
- SQL injection payloads entered in the login form should fail.
- The system should show the normal invalid login message.
- No dashboard or admin page should be opened unless a real email, password, and verification code are supplied.

Important note:
- This is a defensive demonstration. The project does not include an intentionally vulnerable SQL injection page because the system is designed to protect real student and case data.

## Security Demonstration Guide

Use this guide when presenting or defending the project. Start XAMPP MySQL and the Django server first.

### Start the System

1. Open **XAMPP Control Panel**.
2. Click **Start** beside **MySQL**.
3. Open **VS Code**.
4. Open the project folder:

```text
C:\Users\Clark Barrientos\Downloads\WEBSYS2-2 Final Project-20260609T051144Z-3-001\WEBSYS2-2 Final Project
```

5. Open the VS Code terminal.
6. Run:

```powershell
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

7. Open the browser and go to:

```text
http://127.0.0.1:8000/
```

Keep the VS Code terminal open because the local verification code appears there during login.

### Demonstration 1: Institutional Email Authentication

Where to go:
- Login page: `http://127.0.0.1:8000/login/`

What to do:
1. In **Email Address**, type:

```text
user@gmail.com
```

2. In **Password**, type anything.
3. Click **Login**.

Expected result:
- The system rejects the login because only `@tip.edu.ph` accounts are accepted.

What to explain:
- The system restricts access to institutional users only.
- This protects the system from personal or unrelated email accounts.

### Demonstration 2: SQL Injection Login Bypass Attempt

Where to go:
- Login page: `http://127.0.0.1:8000/login/`

What to do:
1. In **Email Address**, type:

```text
' OR '1'='1
```

2. In **Password**, type:

```text
anything
```

3. Click **Login**.

Expected result:
- The login fails.
- The system does not open the dashboard.

Second test:
1. In **Email Address**, type:

```text
admin@tip.edu.ph' OR '1'='1
```

2. In **Password**, type:

```text
anything
```

3. Click **Login**.

Expected result:
- The login still fails.

What to explain:
- The payload is treated as plain text, not as SQL code.
- Django ORM safely handles the database query.
- Authentication still requires the correct email, password, and verification code.

### Demonstration 3: Correct Login With Verification Code

Where to go:
- Login page: `http://127.0.0.1:8000/login/`

What to do:
1. Enter:

```text
Email: admin@tip.edu.ph
Password: admin@123
```

2. Click **Login**.
3. Look at the VS Code terminal.
4. Copy the six-digit verification code printed in the terminal.
5. Paste the code into the verification page.
6. Click the verification button.

Expected result:
- The system opens the Admin dashboard.

What to explain:
- The system uses multi-step verification.
- A password alone is not enough to complete login.
- The verification code expires after 10 minutes.

### Demonstration 4: Role-Based Access Control

Where to go:
- Login page: `http://127.0.0.1:8000/login/`

What to do as Professor:
1. Log out if currently logged in.
2. Log in using:

```text
Email: professor@tip.edu.ph
Password: professor@123
```

3. Enter the verification code from the VS Code terminal.
4. The system should open the Professor dashboard.
5. Try to manually visit:

```text
http://127.0.0.1:8000/dashboard/counselor/
```

Expected result:
- The Professor should not be allowed to access the Counselor dashboard.

What to do as Counselor:
1. Log out.
2. Log in using:

```text
Email: counselor@tip.edu.ph
Password: counselor@123
```

3. Enter the verification code from the VS Code terminal.
4. The system should open the Counselor dashboard.

Expected result:
- Each role sees the dashboard and functions intended for that role.

What to explain:
- Role-based access control enforces least privilege.
- Users cannot freely access pages outside their role.

### Demonstration 5: Login Rate Limiting

Where to go:
- Login page: `http://127.0.0.1:8000/login/`

What to do:
1. Enter a wrong email or wrong password.
2. Click **Login** repeatedly more than five times within a few minutes.

Expected result:
- The system responds with:

```text
Too many requests. Please wait a few minutes and try again.
```

What to explain:
- The system slows repeated login attempts.
- This helps defend against brute-force password guessing.

### Demonstration 6: Audit Logs in Django Admin

Where to go:
- Django admin: `http://127.0.0.1:8000/admin/`

What to do:
1. Log in using:

```text
Email: admin@tip.edu.ph
Password: admin@123
```

2. Complete the verification code step if requested.
3. Open:

```text
http://127.0.0.1:8000/admin/
```

4. Look for **Audit logs** under the Accounts section.
5. Open an audit log record.

Expected result:
- The system shows recorded events such as login, logout, failed login, student changes, report changes, or intervention changes.

What to explain:
- Audit logs support accountability.
- The record shows who performed an action, when it happened, what model was affected, and the IP address.
- The `record_hash` helps support integrity checking.

### Demonstration 7: Password Hashing in phpMyAdmin

Where to go:
- phpMyAdmin: `http://localhost/phpmyadmin/`

What to do:
1. Open **phpMyAdmin**.
2. Click the database:

```text
insightedge_db
```

3. Click the table:

```text
auth_user
```

4. Click **Browse**.
5. Look at the `password` column.

Expected result:
- Passwords are not readable.
- Passwords appear as hashed values starting with something like:

```text
pbkdf2_sha256$
```

What to explain:
- Django stores password hashes, not actual passwords.
- Even the database administrator cannot read the original password from the table.

### Demonstration 8: CSRF Protection

Where to go:
- Any form inside the system, such as Add Student or Logout.

What to show:
1. Log in as Admin or Professor.
2. Open a page with a form.
3. Explain that Django forms include a hidden CSRF token.

Optional browser check:
1. Right-click the page.
2. Click **View Page Source** or **Inspect**.
3. Search for:

```text
csrfmiddlewaretoken
```

Expected result:
- A CSRF token is present in POST forms.

What to explain:
- CSRF protection prevents another website from submitting actions as the logged-in user.

### Demonstration 9: Browser Security Headers

Where to go:
- Any page in the system, such as `http://127.0.0.1:8000/`

What to do in the browser:
1. Press **F12** to open Developer Tools.
2. Click the **Network** tab.
3. Refresh the page.
4. Click the first request, usually `127.0.0.1` or `login/`.
5. Open the **Headers** section.
6. Look for response headers such as:

```text
Content-Security-Policy
Permissions-Policy
Cross-Origin-Opener-Policy
Referrer-Policy
X-Frame-Options
X-Content-Type-Options
```

Expected result:
- The security headers are visible in the browser response.

What to explain:
- These headers instruct the browser to block risky behavior.
- They help reduce script injection, clickjacking, browser feature abuse, and information leakage.

### Demonstration 10: Session Expiration

Where to go:
- Any page after login.

What to do:
1. Log in successfully.
2. Explain that the session is configured to expire after 30 minutes.
3. Close the browser and reopen it.

Expected result:
- The session should not be treated as permanent.
- The system is configured to end sessions when the browser closes.

What to explain:
- Session expiration reduces risk from unattended computers.
- This is important for systems that handle student and case information.

## Security Limitations and Recommendations

These are important to mention honestly in a security-focused project defense:

- The default accounts are for demonstration only and must be changed before real deployment.
- Local development prints verification codes in the terminal; production should configure real SMTP credentials.
- XAMPP MariaDB is acceptable for local testing, but production should use a maintained database server with backups and restricted database users.
- The application protects access to student records, but server-level controls such as operating system permissions, database backups, firewall rules, and HTTPS certificates must also be configured outside Django.
- Audit hashes help detect tampering, but a full enterprise-grade audit system would also export logs to separate storage where normal application administrators cannot edit them.

## Notes

- AI report generation requires `google-generativeai` and a valid `GEMINI_API_KEY`.
- New accounts created from the signup page require admin approval before they can log in.
