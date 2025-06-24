# دليل النشر على منصة Render
## خادم المترجم المتكامل

**الهدف:** نشر خادم المترجم المتكامل على منصة Render مع جميع المكونات والخدمات

---

## جدول المحتويات

1. [متطلبات ما قبل النشر](#متطلبات-ما-قبل-النشر)
2. [إعداد المستودع](#إعداد-المستودع)
3. [إعداد قاعدة البيانات](#إعداد-قاعدة-البيانات)
4. [نشر الخادم الخلفي](#نشر-الخادم-الخلفي)
5. [نشر لوحة التحكم](#نشر-لوحة-التحكم)
6. [إعداد متغيرات البيئة](#إعداد-متغيرات-البيئة)
7. [اختبار النشر](#اختبار-النشر)
8. [المراقبة والصيانة](#المراقبة-والصيانة)
9. [استكشاف الأخطاء](#استكشاف-الأخطاء)

---

## متطلبات ما قبل النشر

### 1. حساب Render
- إنشاء حساب على [render.com](https://render.com)
- التحقق من البريد الإلكتروني
- ربط حساب GitHub (اختياري لكن مُوصى به)

### 2. مستودع GitHub
- إنشاء مستودع جديد على GitHub
- رفع جميع ملفات المشروع
- التأكد من وجود جميع الملفات المطلوبة:
  - `requirements.txt`
  - `Dockerfile`
  - `render.yaml`
  - `gunicorn.conf.py`
  - جميع ملفات الكود المصدري

### 3. إعدادات Docker
- التأكد من تثبيت Docker على الخادم المحلي للاختبار
- اختبار بناء الصور المحلية قبل النشر
- التحقق من صحة جميع ملفات Dockerfile

---

## إعداد المستودع

### 1. هيكل المستودع
```
compiler-server/
├── src/
│   ├── main.py
│   ├── models/
│   ├── routes/
│   └── utils/
├── compiler-dashboard/
│   ├── src/
│   ├── public/
│   └── package.json
├── dockerfiles/
├── docs/
├── requirements.txt
├── Dockerfile
├── render.yaml
├── gunicorn.conf.py
└── README.md
```

### 2. ملف .gitignore
```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
logs/
*.db
*.sqlite
*.sqlite3
```

### 3. ملف README.md
```markdown
# Compiler Server

A comprehensive cloud-based development environment supporting multiple programming languages with container isolation and GitHub integration.

## Features
- Multi-language support (Python, JavaScript, Java, Go, Rust, PHP, C/C++)
- Docker container isolation
- GitHub integration
- Interactive terminal access
- Modern React dashboard
- RESTful APIs
- JWT authentication

## Deployment
This project is configured for deployment on Render platform using the included `render.yaml` configuration.

## Local Development
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the server: `python src/main.py`
4. Access the dashboard: `cd compiler-dashboard && npm run dev`
```

---

## إعداد قاعدة البيانات

### 1. إنشاء قاعدة بيانات PostgreSQL على Render

1. تسجيل الدخول إلى لوحة تحكم Render
2. النقر على "New +" واختيار "PostgreSQL"
3. إعداد قاعدة البيانات:
   - **Name:** `compiler-server-db`
   - **Database Name:** `compiler_server`
   - **User:** `compiler_user`
   - **Region:** اختيار المنطقة الأقرب
   - **Plan:** Starter (مجاني) أو حسب الحاجة

4. انتظار إنشاء قاعدة البيانات والحصول على معلومات الاتصال

### 2. الحصول على سلسلة الاتصال
بعد إنشاء قاعدة البيانات، ستحصل على:
- **Internal Database URL:** للاستخدام داخل Render
- **External Database URL:** للاستخدام من خارج Render

مثال على سلسلة الاتصال:
```
postgresql://compiler_user:password@dpg-xxxxx-a.oregon-postgres.render.com/compiler_server
```

---

## نشر الخادم الخلفي

### 1. إنشاء Web Service جديد

1. في لوحة تحكم Render، النقر على "New +" واختيار "Web Service"
2. ربط مستودع GitHub أو رفع الكود مباشرة
3. إعداد الخدمة:
   - **Name:** `compiler-server-api`
   - **Environment:** `Python 3`
   - **Build Command:** 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     gunicorn --config gunicorn.conf.py src.main:app
     ```

### 2. إعداد متغيرات البيئة

في قسم Environment Variables، إضافة:

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False

# Security Keys (استخدم مولد كلمات مرور قوية)
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Database (استخدم Internal Database URL من قاعدة البيانات)
DATABASE_URL=postgresql://compiler_user:password@dpg-xxxxx-a.oregon-postgres.render.com/compiler_server

# CORS Configuration
CORS_ORIGINS=https://compiler-server-dashboard.onrender.com

# Container Limits
MAX_CONTAINERS_PER_USER=10
CONTAINER_MEMORY_LIMIT=512m
CONTAINER_CPU_LIMIT=1

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

### 3. إعدادات متقدمة

- **Health Check Path:** `/health`
- **Auto-Deploy:** تفعيل للنشر التلقائي عند تحديث الكود
- **Plan:** اختيار الخطة المناسبة (Starter للاختبار)

---

## نشر لوحة التحكم

### 1. إنشاء Static Site جديد

1. النقر على "New +" واختيار "Static Site"
2. ربط نفس مستودع GitHub
3. إعداد الموقع:
   - **Name:** `compiler-server-dashboard`
   - **Build Command:**
     ```bash
     cd compiler-dashboard && npm install && npm run build
     ```
   - **Publish Directory:** `compiler-dashboard/dist`

### 2. إعداد متغيرات البيئة للواجهة الأمامية

```bash
# API Configuration
VITE_API_BASE_URL=https://compiler-server-api.onrender.com/api
```

### 3. إعدادات إضافية

- **Auto-Deploy:** تفعيل
- **Custom Domain:** (اختياري) ربط نطاق مخصص

---

## إعداد متغيرات البيئة

### متغيرات الخادم الخلفي

| المتغير | الوصف | مثال |
|---------|--------|-------|
| `FLASK_ENV` | بيئة Flask | `production` |
| `SECRET_KEY` | مفتاح التشفير الرئيسي | `your-secret-key` |
| `JWT_SECRET_KEY` | مفتاح JWT | `your-jwt-key` |
| `DATABASE_URL` | رابط قاعدة البيانات | `postgresql://...` |
| `CORS_ORIGINS` | النطاقات المسموحة | `https://your-frontend.com` |
| `MAX_CONTAINERS_PER_USER` | حد الحاويات لكل مستخدم | `10` |
| `CONTAINER_MEMORY_LIMIT` | حد الذاكرة للحاوية | `512m` |
| `RATE_LIMIT_REQUESTS` | حد الطلبات | `100` |

### متغيرات الواجهة الأمامية

| المتغير | الوصف | مثال |
|---------|--------|-------|
| `VITE_API_BASE_URL` | رابط API الخلفي | `https://api.example.com/api` |

---

## اختبار النشر

### 1. اختبار الخادم الخلفي

```bash
# اختبار Health Check
curl https://compiler-server-api.onrender.com/health

# اختبار تسجيل مستخدم جديد
curl -X POST https://compiler-server-api.onrender.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123",
    "email": "test@example.com"
  }'

# اختبار تسجيل الدخول
curl -X POST https://compiler-server-api.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

### 2. اختبار الواجهة الأمامية

1. فتح رابط لوحة التحكم في المتصفح
2. اختبار تسجيل الدخول
3. التحقق من عمل جميع الصفحات
4. اختبار إنشاء مشروع جديد

### 3. اختبار التكامل

```python
import requests

# اختبار سير العمل الكامل
base_url = "https://compiler-server-api.onrender.com/api"

# تسجيل الدخول
login_response = requests.post(f"{base_url}/auth/login", json={
    "username": "testuser",
    "password": "testpass123"
})

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# إنشاء مشروع
project_response = requests.post(f"{base_url}/projects", 
    headers=headers,
    json={
        "name": "test-project",
        "language": "python",
        "description": "Test project"
    }
)

print("Project created:", project_response.json())
```

---

## المراقبة والصيانة

### 1. مراقبة الأداء

- **Render Dashboard:** مراقبة استخدام الموارد والأداء
- **Health Checks:** فحص دوري لصحة النظام
- **Logs:** مراجعة سجلات النظام بانتظام

### 2. النسخ الاحتياطي

```bash
# نسخ احتياطي لقاعدة البيانات (يدوي)
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# جدولة النسخ الاحتياطي (باستخدام cron job خارجي)
0 2 * * * pg_dump $DATABASE_URL > /backups/db_$(date +\%Y\%m\%d).sql
```

### 3. التحديثات

1. تحديث الكود في مستودع GitHub
2. النشر التلقائي سيتم تفعيله
3. مراقبة عملية النشر في لوحة تحكم Render
4. اختبار النظام بعد التحديث

---

## استكشاف الأخطاء

### مشاكل شائعة وحلولها

#### 1. فشل بناء التطبيق
```bash
# التحقق من ملف requirements.txt
pip install -r requirements.txt

# التحقق من إصدار Python
python --version

# اختبار بناء Docker محلياً
docker build -t compiler-server .
```

#### 2. مشاكل قاعدة البيانات
```bash
# اختبار الاتصال بقاعدة البيانات
psql $DATABASE_URL -c "SELECT version();"

# التحقق من الجداول
psql $DATABASE_URL -c "\dt"
```

#### 3. مشاكل CORS
```python
# التأكد من إعداد CORS في Flask
from flask_cors import CORS
CORS(app, origins=["https://your-frontend-domain.com"])
```

#### 4. مشاكل متغيرات البيئة
```bash
# التحقق من متغيرات البيئة في Render
echo $DATABASE_URL
echo $SECRET_KEY
```

### سجلات النظام

```bash
# عرض سجلات الخادم الخلفي
# في لوحة تحكم Render: Service > Logs

# عرض سجلات قاعدة البيانات
# في لوحة تحكم Render: Database > Logs
```

### اختبار الاتصال

```python
# اختبار شامل للنظام
import requests
import time

def test_system_health():
    base_url = "https://compiler-server-api.onrender.com"
    
    # اختبار Health Check
    health_response = requests.get(f"{base_url}/health")
    print(f"Health Check: {health_response.status_code}")
    
    # اختبار API
    api_response = requests.get(f"{base_url}/api/auth/verify-token")
    print(f"API Status: {api_response.status_code}")
    
    return health_response.status_code == 200

if __name__ == "__main__":
    if test_system_health():
        print("✅ النظام يعمل بشكل طبيعي")
    else:
        print("❌ يوجد مشكلة في النظام")
```

---

## خلاصة النشر

بعد اتباع هذا الدليل، ستحصل على:

1. **خادم خلفي** يعمل على `https://compiler-server-api.onrender.com`
2. **لوحة تحكم** تعمل على `https://compiler-server-dashboard.onrender.com`
3. **قاعدة بيانات PostgreSQL** مُدارة بالكامل
4. **مراقبة تلقائية** وإشعارات الأخطاء
5. **نشر تلقائي** عند تحديث الكود

النظام الآن جاهز للاستخدام الإنتاجي مع دعم كامل لجميع الميزات المطلوبة.

