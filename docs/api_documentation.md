# توثيق واجهات برمجة التطبيقات (API Documentation)
## خادم المترجم المتكامل

**الإصدار:** 1.0  
**URL الأساسي:** `https://your-server.onrender.com/api`  
**البروتوكول:** HTTPS  
**تنسيق البيانات:** JSON

---

## جدول المحتويات

1. [مقدمة](#مقدمة)
2. [التوثيق والأمان](#التوثيق-والأمان)
3. [APIs إدارة المستخدمين](#apis-إدارة-المستخدمين)
4. [APIs إدارة المشاريع](#apis-إدارة-المشاريع)
5. [APIs تنفيذ الأكواد](#apis-تنفيذ-الأكواد)
6. [APIs إدارة الحاويات](#apis-إدارة-الحاويات)
7. [APIs التكامل مع GitHub](#apis-التكامل-مع-github)
8. [APIs Terminal التفاعلي](#apis-terminal-التفاعلي)
9. [APIs المراقبة والصحة](#apis-المراقبة-والصحة)
10. [أمثلة الاستخدام](#أمثلة-الاستخدام)
11. [رموز الأخطاء](#رموز-الأخطاء)

---

## مقدمة

توفر واجهات برمجة التطبيقات لخادم المترجم المتكامل وصولاً شاملاً لجميع وظائف النظام من خلال نقاط وصول موحدة ومعيارية. تم تصميم هذه الواجهات وفقاً لمعايير REST API مع دعم كامل لبروتوكولات الأمان الحديثة وتنسيقات البيانات المعيارية.

جميع الطلبات والاستجابات تستخدم تنسيق JSON، مع دعم كامل لترميز UTF-8 للنصوص متعددة اللغات. يتطلب النظام استخدام HTTPS لجميع الاتصالات لضمان أمان البيانات أثناء النقل.

---

## التوثيق والأمان

### أنواع التوثيق المدعومة

يدعم النظام نوعين رئيسيين من التوثيق:

#### 1. JWT Token Authentication
```http
Authorization: Bearer <jwt_token>
```

#### 2. API Key Authentication
```http
X-API-Key: <api_key>
```

### الحصول على JWT Token

#### تسجيل الدخول
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**الاستجابة:**
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "your_username",
    "email": "user@example.com"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### تسجيل مستخدم جديد
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "new_username",
  "password": "secure_password",
  "email": "user@example.com"
}
```

#### تجديد Token
```http
POST /api/auth/refresh
Authorization: Bearer <refresh_token>
```

---

## APIs إدارة المستخدمين

### الحصول على معلومات المستخدم الحالي
```http
GET /api/auth/profile
Authorization: Bearer <jwt_token>
```

**الاستجابة:**
```json
{
  "id": 1,
  "username": "user123",
  "email": "user@example.com",
  "created_at": "2025-06-24T10:00:00Z",
  "last_login": "2025-06-24T15:30:00Z"
}
```

### تحديث معلومات المستخدم
```http
PUT /api/auth/profile
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "email": "newemail@example.com",
  "password": "new_password"
}
```

### إعادة توليد API Key
```http
POST /api/auth/api-key/regenerate
Authorization: Bearer <jwt_token>
```

**الاستجابة:**
```json
{
  "message": "API key regenerated successfully",
  "api_key": "new_api_key_here"
}
```

---

## APIs إدارة المشاريع

### إنشاء مشروع جديد
```http
POST /api/projects
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "my-python-project",
  "description": "A sample Python project",
  "language": "python",
  "github_url": "https://github.com/user/repo.git"
}
```

**الاستجابة:**
```json
{
  "id": 123,
  "name": "my-python-project",
  "description": "A sample Python project",
  "language": "python",
  "github_url": "https://github.com/user/repo.git",
  "container_id": "container_abc123",
  "container_status": "creating",
  "created_at": "2025-06-24T16:00:00Z",
  "updated_at": "2025-06-24T16:00:00Z"
}
```

### الحصول على قائمة المشاريع
```http
GET /api/projects
Authorization: Bearer <jwt_token>
```

**المعاملات الاختيارية:**
- `page`: رقم الصفحة (افتراضي: 1)
- `per_page`: عدد العناصر في الصفحة (افتراضي: 10)
- `language`: فلترة حسب اللغة

### الحصول على تفاصيل مشروع محدد
```http
GET /api/projects/{project_id}
Authorization: Bearer <jwt_token>
```

### تحديث مشروع
```http
PUT /api/projects/{project_id}
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "updated-project-name",
  "description": "Updated description"
}
```

### حذف مشروع
```http
DELETE /api/projects/{project_id}
Authorization: Bearer <jwt_token>
```

---

## APIs تنفيذ الأكواد

### تنفيذ أمر في مشروع
```http
POST /api/execution/run
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "project_id": 123,
  "command": "python main.py",
  "timeout": 30
}
```

**الاستجابة:**
```json
{
  "execution_id": "exec_456",
  "project_id": 123,
  "command": "python main.py",
  "status": "running",
  "started_at": "2025-06-24T16:05:00Z"
}
```

### الحصول على نتيجة التنفيذ
```http
GET /api/execution/{execution_id}
Authorization: Bearer <jwt_token>
```

**الاستجابة:**
```json
{
  "execution_id": "exec_456",
  "project_id": 123,
  "command": "python main.py",
  "status": "completed",
  "exit_code": 0,
  "stdout": "Hello, World!\n",
  "stderr": "",
  "started_at": "2025-06-24T16:05:00Z",
  "completed_at": "2025-06-24T16:05:02Z",
  "duration": 2.1
}
```

### الحصول على سجل التنفيذ لمشروع
```http
GET /api/execution/history/{project_id}
Authorization: Bearer <jwt_token>
```

---

## APIs إدارة الحاويات

### الحصول على قائمة الحاويات
```http
GET /api/containers
Authorization: Bearer <jwt_token>
```

**الاستجابة:**
```json
{
  "containers": [
    {
      "id": "container_abc123",
      "name": "my-python-project",
      "status": "running",
      "language": "python",
      "created_at": "2025-06-24T16:00:00Z",
      "resource_usage": {
        "cpu_percent": 15.5,
        "memory_usage": "128MB",
        "memory_limit": "512MB"
      }
    }
  ],
  "total": 1
}
```

### الحصول على تفاصيل حاوية
```http
GET /api/containers/{container_id}
Authorization: Bearer <jwt_token>
```

### بدء تشغيل حاوية
```http
POST /api/containers/{container_id}/start
Authorization: Bearer <jwt_token>
```

### إيقاف حاوية
```http
POST /api/containers/{container_id}/stop
Authorization: Bearer <jwt_token>
```

### إعادة تشغيل حاوية
```http
POST /api/containers/{container_id}/restart
Authorization: Bearer <jwt_token>
```

### حذف حاوية
```http
DELETE /api/containers/{container_id}
Authorization: Bearer <jwt_token>
```

### الحصول على معلومات النظام
```http
GET /api/containers/system-info
Authorization: Bearer <jwt_token>
```

---

## APIs التكامل مع GitHub

### ربط حساب GitHub
```http
POST /api/github/connect
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "access_token": "github_access_token"
}
```

### استنساخ مستودع من GitHub
```http
POST /api/github/clone
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "repository_url": "https://github.com/user/repo.git",
  "project_name": "cloned-project",
  "language": "python"
}
```

### الحصول على قائمة المستودعات
```http
GET /api/github/repositories
Authorization: Bearer <jwt_token>
```

### مزامنة مشروع مع GitHub
```http
POST /api/github/sync/{project_id}
Authorization: Bearer <jwt_token>
```

### دفع التغييرات إلى GitHub
```http
POST /api/github/push/{project_id}
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "commit_message": "Update project files",
  "branch": "main"
}
```

---

## APIs Terminal التفاعلي

### إنشاء جلسة Terminal
```http
POST /api/terminal/create
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "project_id": 123
}
```

**الاستجابة:**
```json
{
  "session_id": "term_session_789",
  "container_id": "container_abc123",
  "project_id": 123,
  "websocket_url": "/api/terminal/connect/term_session_789",
  "status": "created"
}
```

### الحصول على حالة جلسة Terminal
```http
GET /api/terminal/{session_id}/status
Authorization: Bearer <jwt_token>
```

### إغلاق جلسة Terminal
```http
DELETE /api/terminal/{session_id}
Authorization: Bearer <jwt_token>
```

### WebSocket للتفاعل مع Terminal
```javascript
// اتصال WebSocket
const socket = io('/terminal', {
  auth: {
    token: 'your_jwt_token'
  }
});

// الانضمام لجلسة
socket.emit('join_session', {
  session_id: 'term_session_789'
});

// تنفيذ أمر
socket.emit('execute_command', {
  session_id: 'term_session_789',
  command: 'ls -la'
});

// استقبال المخرجات
socket.on('output', (data) => {
  console.log(data.data);
});
```

---

## APIs المراقبة والصحة

### فحص صحة النظام
```http
GET /health
```

**الاستجابة:**
```json
{
  "status": "healthy",
  "timestamp": 1719244800,
  "checks": {
    "database": "healthy",
    "docker": "healthy",
    "system": {
      "cpu_percent": 25.5,
      "memory_percent": 45.2,
      "disk_percent": 30.1,
      "status": "healthy"
    }
  }
}
```

### فحص الجاهزية
```http
GET /health/ready
```

### فحص الحيوية
```http
GET /health/live
```

### مقاييس النظام
```http
GET /metrics
```

---

## أمثلة الاستخدام

### مثال شامل: إنشاء مشروع Python وتنفيذ كود

```python
import requests
import json

# إعدادات الاتصال
BASE_URL = "https://your-server.onrender.com/api"
headers = {
    "Content-Type": "application/json"
}

# 1. تسجيل الدخول
login_data = {
    "username": "your_username",
    "password": "your_password"
}

response = requests.post(f"{BASE_URL}/auth/login", 
                        headers=headers, 
                        data=json.dumps(login_data))
auth_data = response.json()
token = auth_data["access_token"]

# إضافة التوكن للهيدر
headers["Authorization"] = f"Bearer {token}"

# 2. إنشاء مشروع جديد
project_data = {
    "name": "hello-world-python",
    "description": "A simple Python hello world project",
    "language": "python"
}

response = requests.post(f"{BASE_URL}/projects", 
                        headers=headers, 
                        data=json.dumps(project_data))
project = response.json()
project_id = project["id"]

print(f"تم إنشاء المشروع بنجاح: {project_id}")

# 3. انتظار إنشاء الحاوية
import time
while True:
    response = requests.get(f"{BASE_URL}/projects/{project_id}", headers=headers)
    project_status = response.json()
    if project_status["container_status"] == "running":
        break
    time.sleep(2)

print("الحاوية جاهزة للاستخدام")

# 4. تنفيذ كود Python
execution_data = {
    "project_id": project_id,
    "command": "python -c \"print('Hello, World!')\"",
    "timeout": 30
}

response = requests.post(f"{BASE_URL}/execution/run", 
                        headers=headers, 
                        data=json.dumps(execution_data))
execution = response.json()
execution_id = execution["execution_id"]

# 5. انتظار انتهاء التنفيذ والحصول على النتيجة
while True:
    response = requests.get(f"{BASE_URL}/execution/{execution_id}", headers=headers)
    result = response.json()
    if result["status"] == "completed":
        print(f"المخرجات: {result['stdout']}")
        print(f"الأخطاء: {result['stderr']}")
        print(f"رمز الخروج: {result['exit_code']}")
        break
    time.sleep(1)
```

---

## رموز الأخطاء

### رموز الحالة HTTP

| الرمز | الوصف | المعنى |
|-------|--------|---------|
| 200 | OK | الطلب نجح |
| 201 | Created | تم إنشاء المورد بنجاح |
| 400 | Bad Request | خطأ في بيانات الطلب |
| 401 | Unauthorized | مطلوب توثيق |
| 403 | Forbidden | غير مخول للوصول |
| 404 | Not Found | المورد غير موجود |
| 409 | Conflict | تعارض في البيانات |
| 429 | Too Many Requests | تجاوز حد الطلبات |
| 500 | Internal Server Error | خطأ في الخادم |
| 503 | Service Unavailable | الخدمة غير متاحة |

### رموز الأخطاء المخصصة

```json
{
  "error": "CONTAINER_NOT_FOUND",
  "message": "Container with ID 'abc123' not found",
  "code": 1001,
  "timestamp": "2025-06-24T16:00:00Z"
}
```

| الرمز | الوصف |
|-------|--------|
| 1001 | CONTAINER_NOT_FOUND |
| 1002 | CONTAINER_CREATION_FAILED |
| 1003 | EXECUTION_TIMEOUT |
| 1004 | INVALID_LANGUAGE |
| 1005 | PROJECT_NOT_FOUND |
| 1006 | GITHUB_CONNECTION_FAILED |
| 1007 | TERMINAL_SESSION_EXPIRED |
| 1008 | RESOURCE_LIMIT_EXCEEDED |

