# استخدم صورة رسمية للبايثون
FROM python:3.11-slim

# ضبط متغير البيئة لعدم تخزين ملفات pyc
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# إنشاء مجلد التطبيق ونسخ الملفات
WORKDIR /app
COPY . /app/

# تثبيت المتطلبات
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# تحديد البورت (Fly.io يعمل غالبًا على 8080)
EXPOSE 8080

# الأمر الرئيسي لتشغيل التطبيق
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
