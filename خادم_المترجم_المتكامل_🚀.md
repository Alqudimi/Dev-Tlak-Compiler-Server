# خادم المترجم المتكامل 🚀
## نظام شامل لتطوير وتنفيذ المشاريع البرمجية مع دعم الحاويات والتكامل مع GitHub

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18+-61dafb.svg)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)

---

## 📋 نظرة عامة

خادم المترجم المتكامل هو نظام تطوير سحابي متقدم يوفر بيئة تطوير موحدة تدعم جميع لغات البرمجة الحديثة مع ضمان العزل الكامل والأمان بين المشاريع. يجمع النظام بين قوة تقنيات الحاويات ومرونة الحوسبة السحابية لتوفير تجربة تطوير استثنائية.

### ✨ الميزات الرئيسية

- 🌐 **دعم متعدد اللغات**: Python, JavaScript, Java, Go, Rust, PHP, C/C++
- 🐳 **عزل آمن بالحاويات**: كل مشروع في بيئة Docker منفصلة
- 🔗 **تكامل GitHub**: استنساخ ومزامنة المشاريع مباشرة
- 💻 **Terminal تفاعلي**: وصول مباشر لسطر الأوامر عبر WebSocket
- 🎨 **لوحة تحكم حديثة**: واجهة React متجاوبة وسهلة الاستخدام
- 🔐 **أمان متقدم**: JWT authentication وAPI keys
- 📊 **مراقبة شاملة**: Health checks ومقاييس الأداء
- 🚀 **جاهز للنشر**: مُعد للنشر على Render بنقرة واحدة

---

## 🏗️ البنية التقنية

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React UI      │    │   Flask API     │    │   PostgreSQL    │
│   Dashboard     │◄──►│   Server        │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Docker        │
                       │   Containers    │
                       │   (Multi-lang)  │
                       └─────────────────┘
```

### المكونات الأساسية

- **الخادم الخلفي**: Flask + SQLAlchemy + Docker SDK
- **الواجهة الأمامية**: React + Tailwind CSS + shadcn/ui
- **قاعدة البيانات**: PostgreSQL مع دعم المعاملات المعقدة
- **نظام الحاويات**: Docker مع إدارة ذكية للموارد
- **التوثيق**: JWT tokens + API keys
- **المراقبة**: Health checks + Prometheus metrics

---

## 🚀 البدء السريع

### المتطلبات الأساسية

- Python 3.11+
- Node.js 18+
- Docker
- PostgreSQL (للإنتاج)

### التثبيت المحلي

```bash
# 1. استنساخ المستودع
git clone https://github.com/your-username/compiler-server.git
cd compiler-server

# 2. إعداد البيئة الافتراضية
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate     # Windows

# 3. تثبيت الاعتمادات
pip install -r requirements.txt

# 4. إعداد قاعدة البيانات
export DATABASE_URL="sqlite:///app.db"  # للتطوير
python -c "from src.main import app, db; app.app_context().push(); db.create_all()"

# 5. تشغيل الخادم
python src/main.py
```

### تشغيل لوحة التحكم

```bash
# في terminal منفصل
cd compiler-dashboard
npm install
npm run dev
```

الآن يمكنك الوصول إلى:
- **API Server**: http://localhost:5000
- **Dashboard**: http://localhost:5173

---

## 📚 التوثيق

### دلائل شاملة

- 📖 [**الدليل الشامل**](docs/comprehensive_guide.md) - دليل تفصيلي لجميع جوانب النظام
- 🔌 [**توثيق APIs**](docs/api_documentation.md) - مرجع كامل لواجهات برمجة التطبيقات
- 🚀 [**دليل النشر على Render**](docs/render_deployment_guide.md) - خطوات النشر التفصيلية

### مراجع سريعة

- [خطة التنفيذ التفصيلية](detailed_execution_plan.md)
- [تحليل المتطلبات](requirements_analysis.md)
- [قائمة المهام](todo.md)

---

## 🔧 الاستخدام

### إنشاء مشروع جديد

```python
import requests

# تسجيل الدخول
response = requests.post('http://localhost:5000/api/auth/login', json={
    'username': 'your_username',
    'password': 'your_password'
})
token = response.json()['access_token']

# إنشاء مشروع Python
headers = {'Authorization': f'Bearer {token}'}
project = requests.post('http://localhost:5000/api/projects', 
    headers=headers,
    json={
        'name': 'my-python-project',
        'language': 'python',
        'description': 'مشروع Python تجريبي'
    }
).json()

print(f"تم إنشاء المشروع: {project['id']}")
```

### تنفيذ كود

```python
# تنفيذ أمر في المشروع
execution = requests.post('http://localhost:5000/api/execution/run',
    headers=headers,
    json={
        'project_id': project['id'],
        'command': 'python -c "print(\'Hello, World!\')"'
    }
).json()

# الحصول على النتيجة
result = requests.get(f'http://localhost:5000/api/execution/{execution["execution_id"]}',
    headers=headers
).json()

print(f"المخرجات: {result['stdout']}")
```

---

## 🌐 النشر على Render

### نشر بنقرة واحدة

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/your-username/compiler-server)

### النشر اليدوي

1. **إنشاء قاعدة بيانات PostgreSQL**
   ```
   Name: compiler-server-db
   Plan: Starter (Free)
   ```

2. **نشر الخادم الخلفي**
   ```
   Type: Web Service
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn --config gunicorn.conf.py src.main:app
   ```

3. **نشر لوحة التحكم**
   ```
   Type: Static Site
   Build Command: cd compiler-dashboard && npm install && npm run build
   Publish Directory: compiler-dashboard/dist
   ```

للتفاصيل الكاملة، راجع [دليل النشر](docs/render_deployment_guide.md).

---

## 🔐 الأمان

### ميزات الأمان المدمجة

- **تشفير البيانات**: جميع البيانات مشفرة أثناء النقل والتخزين
- **عزل الحاويات**: كل مشروع معزول تماماً عن الآخرين
- **التوثيق المتعدد**: JWT tokens + API keys
- **حدود الموارد**: قيود صارمة على استخدام CPU والذاكرة
- **مراقبة الأنشطة**: تسجيل شامل لجميع العمليات
- **Rate Limiting**: حماية من الاستخدام المفرط

### أفضل الممارسات

```python
# استخدام متغيرات البيئة للمفاتيح الحساسة
import os
SECRET_KEY = os.environ.get('SECRET_KEY')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')

# تطبيق HTTPS في الإنتاج
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
```

---

## 📊 المراقبة والصيانة

### Health Checks

```bash
# فحص صحة النظام
curl https://your-app.onrender.com/health

# مقاييس النظام
curl https://your-app.onrender.com/metrics
```

### المراقبة المستمرة

- **Uptime monitoring**: فحص دوري للخدمة
- **Resource monitoring**: مراقبة استخدام الموارد
- **Error tracking**: تتبع الأخطاء والاستثناءات
- **Performance metrics**: مقاييس الأداء والاستجابة

---

## 🤝 المساهمة

نرحب بمساهماتكم! يرجى اتباع الخطوات التالية:

1. Fork المستودع
2. إنشاء branch جديد (`git checkout -b feature/amazing-feature`)
3. Commit التغييرات (`git commit -m 'Add amazing feature'`)
4. Push إلى Branch (`git push origin feature/amazing-feature`)
5. فتح Pull Request

### إرشادات المساهمة

- اتبع معايير PEP 8 للكود Python
- أضف اختبارات للميزات الجديدة
- حدث التوثيق عند الحاجة
- تأكد من نجاح جميع الاختبارات

---

## 📝 الترخيص

هذا المشروع مرخص تحت رخصة MIT - راجع ملف [LICENSE](LICENSE) للتفاصيل.

---

## 🆘 الدعم

### الحصول على المساعدة

- 📧 **البريد الإلكتروني**: support@compiler-server.com
- 💬 **Discord**: [انضم لخادمنا](https://discord.gg/compiler-server)
- 📚 **التوثيق**: [docs.compiler-server.com](https://docs.compiler-server.com)
- 🐛 **تقرير الأخطاء**: [GitHub Issues](https://github.com/your-username/compiler-server/issues)

### الأسئلة الشائعة

**س: هل يمكنني إضافة دعم للغة برمجة جديدة؟**
ج: نعم! أضف Dockerfile جديد في مجلد `dockerfiles/` وحدث نظام إدارة الحاويات.

**س: كيف يمكنني زيادة حدود الموارد للحاويات؟**
ج: حدث متغيرات البيئة `CONTAINER_MEMORY_LIMIT` و `CONTAINER_CPU_LIMIT`.

**س: هل النظام يدعم التوسع الأفقي؟**
ج: نعم، يمكن تشغيل عدة نسخ من الخادم مع موازن أحمال.

---

## 🎯 خارطة الطريق

### الإصدار 1.1 (قريباً)
- [ ] دعم Kubernetes
- [ ] تكامل مع GitLab
- [ ] محرر كود مدمج
- [ ] دعم Jupyter Notebooks

### الإصدار 1.2
- [ ] CI/CD Pipeline مدمج
- [ ] دعم قواعد البيانات متعددة
- [ ] نظام إشعارات متقدم
- [ ] تحليلات الاستخدام

### الإصدار 2.0
- [ ] دعم الذكاء الاصطناعي
- [ ] تكامل مع خدمات السحابة
- [ ] نظام فريق العمل
- [ ] API GraphQL

---

## 📈 الإحصائيات

- ⭐ **GitHub Stars**: 0 (مشروع جديد!)
- 🍴 **Forks**: 0
- 🐛 **Issues**: 0
- 📦 **Releases**: v1.0.0
- 👥 **Contributors**: 1

---

## 🙏 شكر وتقدير

- **Flask Team** - إطار العمل الرائع
- **React Team** - مكتبة UI المتقدمة
- **Docker** - تقنية الحاويات المذهلة
- **Render** - منصة النشر السهلة
- **shadcn/ui** - مكونات UI الجميلة

---

<div align="center">

**صُنع بـ ❤️ بواسطة [Manus AI](https://github.com/manus-ai)**

[⬆ العودة للأعلى](#خادم-المترجم-المتكامل-)

</div>

