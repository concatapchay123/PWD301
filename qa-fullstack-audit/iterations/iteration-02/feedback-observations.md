# ITERATION 02 FEEDBACK OBSERVATIONS

## 1. Browser Console Observations
- Total console entries intercepted: 9
```text
[warning] cdn.tailwindcss.com should not be used in production. To use Tailwind CSS in production, install it as a PostCSS plugin or use the Tailwind CLI: https://tailwindcss.com/docs/installation
[error] Failed to load resource: the server responded with a status of 401 (UNAUTHORIZED)
[error] Failed to load resource: the server responded with a status of 401 (UNAUTHORIZED)
[warning] [ApiClient] Request to /auth/login failed: Error: Email hoặc mật khẩu không chính xác.
    at ApiClient.request (http://127.0.0.1:5000/frontend/assets/js/api.js?v=3.2.6:181:21)
    at async ApiClient.login (http://127.0.0.1:5000/frontend/assets/js/api.js?v=3.2.6:231:17)
    at async loginForm.onsubmit (http://127.0.0.1:5000/frontend/assets/js/views/auth.js?v=3.2.6:775:23)
[error] Failed to load resource: the server responded with a status of 401 (UNAUTHORIZED)
[error] Failed to load resource: the server responded with a status of 401 (UNAUTHORIZED)
[error] Failed to load resource: the server responded with a status of 401 (UNAUTHORIZED)
[warning] cdn.tailwindcss.com should not be used in production. To use Tailwind CSS in production, install it as a PostCSS plugin or use the Tailwind CLI: https://tailwindcss.com/docs/installation
[error] Failed to load resource: the server responded with a status of 401 (UNAUTHORIZED)
```

## 2. Network Observations
- Total network requests captured: 161
```text
-> POST http://127.0.0.1:5000/auth/login
<- 200 http://127.0.0.1:5000/auth/login (POST)
-> GET http://127.0.0.1:5000/auth/notifications?role=STUDENT
-> GET http://127.0.0.1:5000/student/dashboard
<- 200 http://127.0.0.1:5000/auth/notifications?role=STUDENT (GET)
<- 200 http://127.0.0.1:5000/student/dashboard (GET)
-> GET http://127.0.0.1:5000/student/recommendations?limit=2
-> GET http://127.0.0.1:5000/api/courses/fdef62ea-fe13-4273-827c-563ac0617a99/thumbnail
<- 200 http://127.0.0.1:5000/student/recommendations?limit=2 (GET)
<- 200 http://127.0.0.1:5000/api/courses/fdef62ea-fe13-4273-827c-563ac0617a99/thumbnail (GET)
-> GET http://127.0.0.1:5000/api/events/stream
<- 200 http://127.0.0.1:5000/api/events/stream (GET)
-> GET http://127.0.0.1:5000/auth/profile
-> GET http://127.0.0.1:5000/auth/preferences
<- 200 http://127.0.0.1:5000/auth/preferences (GET)
```

## 3. Database State Verification
User auth_version increment verified in MSSQL AuthSession records.
