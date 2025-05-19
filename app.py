# أبدأ هنا باستيراد مكتبات Flask المطلوبة لبناء الموقع
from flask import Flask, render_template, request, redirect, url_for, flash, abort  # أستخدم هذه لبناء الصفحات ومعالجة الطلبات والتنقل والتنبيه
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user  # لإدارة تسجيل الدخول والخروج والتحقق من الجلسة
import mysql.connector  # أحتاجها لربط البايثون مع قاعدة بيانات MySQL
from werkzeug.security import generate_password_hash, check_password_hash  # لتشفير وفحص كلمات المرور
from functools import wraps  # حتى أصنع ديكور للتحكم في صلاحية الأدمن فقط
import requests  # ضرورية لجلب نتائج البحث من Google

# هنا أهيئ التطبيق نفسه وأحدد كلمة السر للجلسات (سرية)
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# أضبط LoginManager وأربطه بالتطبيق، لكي يدير جلسات المستخدمين
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # لو المستخدم مش مسجل يدخل صفحة login

# هذه متغيرات ربط Google API للبحث في المواقع القانونية
API_KEY = "AIzaSyBQxztOoFO3LCQX-K-Wxx7GRQlGAxS-EDc"
CX = "35c66c2b2e6544fc6"

# دالة اتصال بقاعدة البيانات - أستدعيها كل ما أحتاج أتعامل مع الداتا
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',  # غالبًا يبقى localhost لأن قاعدة البيانات على جهازي
        user='root',       # اسم المستخدم غالبًا root
        password='',       # عادة بدون كلمة سر، لو عندي أضيفها هنا
        database='law_directory'  # اسم قاعدة البيانات اللي أنشأتها
    )

# هنا أبني كلاس مستخدم متوافق مع Flask-Login
class User(UserMixin):
    def __init__(self, id, username, password, email, is_admin):
        self.id = id  # رقم المستخدم (مفتاح رئيسي)
        self.username = username  # اسم المستخدم
        self.password = password  # كلمة السر (مشفرة)
        self.email = email        # البريد الإلكتروني
        self.is_admin = is_admin  # هل هذا المستخدم أدمن أم لا

# دالة تحميل المستخدم للجلسة من قاعدة البيانات
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()  # أفتح الاتصال بقاعدة البيانات
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))  # أبحث عن المستخدم بالرقم
    user = cursor.fetchone()
    conn.close()  # أغلق الاتصال بعد ما أخلص
    if user:
        return User(user['id'], user['username'], user['password'], user['email'], user['is_admin'])  # أرجع كائن المستخدم
    return None  # إذا لم يوجد يرجع لا شيء

# ديكور بسيط - يستخدم لفحص صلاحية الأدمن في أي صفحة أضعه عليها
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):  # إذا مش أدمن أو مش مسجل
            abort(403)  # أظهر صفحة ممنوع الدخول
        return f(*args, **kwargs)  # لو تحقق الشرط ينفذ الصفحة
    return decorated_function

# الصفحة الرئيسية - تظهر أول ما يدخل الموقع
@app.route('/')
def home():
    return render_template('index.html')  # أعرض صفحة index.html

# صفحة "حول" للتعريف بالموقع
@app.route('/about')
def about():
    return render_template('about.html')  # أعرض صفحة about.html

# صفحة الملف الشخصي - تظهر بيانات المستخدم (يجب تسجيل الدخول)
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)  # أرسل بيانات المستخدم للصفحة

# صفحة التسجيل للمستخدمين الجدد
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':  # لو المستخدم ضغط تسجيل
        username = request.form['username']  # أقرأ الاسم
        email = request.form['email']        # أقرأ البريد
        password = generate_password_hash(request.form['password'])  # أشفر كلمة المرور
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                (username, password, email)
            )  # أضيف البيانات للجدول
            conn.commit()  # أحفظ التغييرات
            flash("تم التسجيل بنجاح! يمكنك الآن تسجيل الدخول.", "success")
            return redirect(url_for('login'))  # أنقله لصفحة الدخول بعد التسجيل
        except mysql.connector.Error as err:
            flash("اسم المستخدم أو البريد الإلكتروني مستخدم بالفعل!", "danger")  # لو البيانات مكررة
        finally:
            conn.close()  # أغلق الاتصال بأي حال
    return render_template('register.html')  # لو GET أعرض صفحة التسجيل فقط

# صفحة تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # لو ضغط تسجيل الدخول
        username = request.form['username']  # أقرأ الاسم
        password = request.form['password']  # أقرأ كلمة المرور
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))  # أبحث عن المستخدم
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):  # لو كلمة السر صحيحة
            user_obj = User(user['id'], user['username'], user['password'], user['email'], user['is_admin'])
            login_user(user_obj)  # أسجل دخوله
            flash("تم تسجيل الدخول بنجاح!", "success")
            return redirect(url_for('home'))  # أنقله للرئيسية
        else:
            flash("بيانات الدخول غير صحيحة!", "danger")  # لو خطأ في البيانات
    return render_template('login.html')  # أعرض صفحة الدخول دائمًا

# تسجيل الخروج
@app.route('/logout')
@login_required
def logout():
    logout_user()  # أخرج المستخدم من الجلسة
    flash("تم تسجيل الخروج بنجاح.", "info")
    return redirect(url_for('login'))  # أرجعه لصفحة الدخول

# دالة لحفظ سجل البحث للمستخدم الحالي
def save_search_log(query):
    if current_user.is_authenticated:  # فقط إذا المستخدم مسجل
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO search_log (user_id, query) VALUES (%s, %s)", (current_user.id, query)
        )  # أضيف العملية للجدول
        conn.commit()
        conn.close()

# صفحة البحث، تستقبل الكلمة من المستخدم وتبحث في المواقع القانونية عبر Google API
@app.route('/search')
def search():
    query = request.args.get('q', '')  # أقرأ كلمة البحث من الرابط
    if not query:
        flash("يرجى إدخال كلمة بحث.", "warning")
        return redirect(url_for('home'))  # لو لم يكتب بحث يرجعه للرئيسية

    # هنا أضيق البحث على مواقع القوانين الرسمية فقط
    law_sites = "(site:moj.gov.iq OR site:iraqja.iq OR site:parliament.iq OR site:icrc.org OR site:un.org OR site:treaties.un.org OR site:icc-cpi.int)"
    full_query = f"{query} {law_sites}"

    # أستدعي Google API وأحصل على النتائج
    url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={CX}&q={full_query}&num=8"
    response = requests.get(url)
    items = response.json().get('items', [])

    save_search_log(query)  # أحفظ عملية البحث في الجدول

    results = []  # قائمة لنتائج البحث
    for item in items:  # أمشي على كل نتيجة وأجهزها للعرض
        results.append({
            "title": item.get('title', ''),
            "link": item.get('link', ''),
            "snippet": item.get('snippet', '')
        })
    return render_template('search_results.html', results=results, query=query)  # أعرض النتائج للمستخدم

# لوحة تحكم الأدمن - تعرض المستخدمين وسجل البحث الأخير
@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")  # أجيب كل المستخدمين
    users = cursor.fetchall()
    cursor.execute("SELECT * FROM search_log ORDER BY search_time DESC LIMIT 20")  # أجيب آخر 20 عملية بحث
    search_logs = cursor.fetchall()
    conn.close()
    return render_template('admin_dashboard.html', users=users, search_logs=search_logs)  # أعرضهم في الصفحة

# صفحة الإحصائيات - تعرض للأدمن فقط عدد عمليات البحث وأشهر الكلمات
@app.route('/admin/stats')
@admin_required
def admin_stats():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as total_searches FROM search_log")  # كم عملية بحث تمت
    total = cursor.fetchone()["total_searches"]
    cursor.execute("SELECT query, COUNT(*) as times FROM search_log GROUP BY query ORDER BY times DESC LIMIT 10")  # أشهر عمليات البحث
    top_queries = cursor.fetchall()
    conn.close()
    return render_template('admin_stats.html', total=total, top_queries=top_queries)  # أعرضها في الصفحة

# هذه نهاية الكود، كل شيء هنا جاهز للعرض على أي جهاز
if __name__ == '__main__':
    app.run(debug=True)  # أشغل الموقع في وضع التطوير
