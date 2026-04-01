from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "jobportal_super_secret_2026"


# --------------- Login Required Decorator-------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# ---------------- HOME ----------------
@app.route('/')
def home():
    return redirect('/login')

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="job_portal"
)
# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']

        cursor = db.cursor()

        # 🔎 Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email already exists!")
            return redirect('/register')

        # ✅ Insert new user
        cursor.execute(
            "INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
            (name, email, password, role)
        )
        db.commit()

        flash("Registration Successful! Please Login.")
        return redirect('/login')

    return render_template('register.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['name'] = user[1]
            session['role'] = user[4]
            return redirect('/dashboard')
        else:
            flash("Invalid Credentials")

    return render_template('login.html')

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
@login_required
def dashboard():
    search = request.args.get('search')

    cursor = db.cursor(dictionary=True)

    if search:
        cursor.execute(
            "SELECT * FROM jobs WHERE title LIKE %s OR company LIKE %s",
            (f"%{search}%", f"%{search}%")
        )
    else:
        cursor.execute("SELECT * FROM jobs")

    jobs = cursor.fetchall()

    return render_template('dashboard.html', jobs=jobs)

# ---------------- ADD JOB ----------------
@app.route('/add_job', methods=['GET','POST'])
def add_job():
    if session.get('role') not in ['admin','employer']:
        return redirect('/dashboard')

    if request.method == 'POST':
        title = request.form['title']
        company = request.form['company']
        location = request.form['location']
        salary = request.form['salary']
        description = request.form['description']

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO jobs (title,company,location,salary,description,employer_id) VALUES (%s,%s,%s,%s,%s,%s)",
            (title,company,location,salary,description,session['user_id'])
        )
        db.commit()
        flash("Job Added Successfully!")
        return redirect('/dashboard')

    return render_template('add_job.html')

# ---------------- EDIT JOB ----------------
@app.route('/edit_job/<int:id>', methods=['GET', 'POST'])
def edit_job(id):
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        title = request.form['title']
        company = request.form['company']
        location = request.form['location']
        salary = request.form['salary']
        description = request.form['description']

        cursor.execute("""
            UPDATE jobs 
            SET title=%s, company=%s, location=%s, salary=%s, description=%s 
            WHERE id=%s
        """, (title, company, location, salary, description, id))
        db.commit()

        return redirect('/dashboard')

    # 🔥 Important Part (GET request)
    cursor.execute("SELECT * FROM jobs WHERE id=%s", (id,))
    job = cursor.fetchone()

    return render_template('edit_job.html', job=job)

# ---------------- DELETE JOB ----------------
@app.route('/delete_job/<int:id>')
def delete_job(id):
    cursor = db.cursor()
    cursor.execute("DELETE FROM jobs WHERE id=%s",(id,))
    db.commit()
    flash("Job Deleted Successfully!")
    return redirect('/dashboard')

# ---------------- APPLY JOB ----------------
@app.route('/apply/<int:id>')
def apply(id):
    if session.get('role') != 'jobseeker':
        return redirect('/dashboard')

    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO applications (user_id,job_id) VALUES (%s,%s)",
        (session['user_id'],id)
    )
    db.commit()
    flash("Applied Successfully!")
    return redirect('/dashboard')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)