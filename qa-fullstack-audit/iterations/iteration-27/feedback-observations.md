# ITERATION 27 FEEDBACK OBSERVATIONS

## 1. Browser Console Observations
- Total console entries intercepted: 7
```text
[warning] cdn.tailwindcss.com should not be used in production. To use Tailwind CSS in production, install it as a PostCSS plugin or use the Tailwind CLI: https://tailwindcss.com/docs/installation
[error] Failed to load resource: the server responded with a status of 401 (UNAUTHORIZED)
[error] Failed to load resource: the server responded with a status of 401 (UNAUTHORIZED)
[error] Failed to load resource: the server responded with a status of 409 (CONFLICT)
[warning] [ApiClient] Request to /auth/login failed: Error: Tài khoản đã bị đăng xuất trên toàn bộ thiết bị do phát hiện đăng nhập đồng thời từ thiết bị khác để bảo vệ an toàn.
    at ApiClient.request (http://127.0.0.1:5000/frontend/assets/js/api.js?v=3.2.6:181:21)
    at async ApiClient.login (http://127.0.0.1:5000/frontend/assets/js/api.js?v=3.2.6:231:17)
    at async loginForm.onsubmit (http://127.0.0.1:5000/frontend/assets/js/views/auth.js?v=3.2.6:775:23)
[error] Failed to load resource: the server responded with a status of 401 (UNAUTHORIZED)
[warning] [ApiClient] Request to /student/courses/1/leave failed: Error: Vui lòng đăng nhập để tiếp tục.
    at ApiClient.request (http://127.0.0.1:5000/frontend/assets/js/api.js?v=3.2.6:181:21)
    at async eval (eval at evaluate (:370:30), <anonymous>:3:29)
    at async <anonymous>:396:30
```

## 2. Network Observations
- Total network requests captured: 166
```text
<- 200 http://127.0.0.1:5000/auth/session
-> GET http://127.0.0.1:5000/auth/runtime-config
-> GET http://127.0.0.1:5000/auth/runtime-config
<- 200 http://127.0.0.1:5000/auth/runtime-config
<- 200 http://127.0.0.1:5000/auth/runtime-config
-> POST http://127.0.0.1:5000/auth/login
<- 409 http://127.0.0.1:5000/auth/login
-> GET http://127.0.0.1:5000/auth/session
<- 200 http://127.0.0.1:5000/auth/session
-> GET http://127.0.0.1:5000/auth/runtime-config
-> GET http://127.0.0.1:5000/auth/runtime-config
<- 200 http://127.0.0.1:5000/auth/runtime-config
<- 200 http://127.0.0.1:5000/auth/runtime-config
-> POST http://127.0.0.1:5000/student/courses/1/leave
<- 401 http://127.0.0.1:5000/student/courses/1/leave
```

## 3. Database State Verification
Verified Enrollment records cannot be deleted or set to inactive by users.
