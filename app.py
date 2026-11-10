import os
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-before-deployment")
database_url = os.environ.get("DATABASE_URL", "sqlite:///pfa_school.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please sign in to continue."

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(140), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="teacher")
    active = db.Column(db.Boolean, default=True)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admission_no = db.Column(db.String(40), unique=True, nullable=False)
    full_name = db.Column(db.String(140), nullable=False)
    gender = db.Column(db.String(20))
    date_of_birth = db.Column(db.String(20))
    class_name = db.Column(db.String(80))
    guardian_name = db.Column(db.String(140))
    guardian_phone = db.Column(db.String(40))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_no = db.Column(db.String(40), unique=True, nullable=False)
    full_name = db.Column(db.String(140), nullable=False)
    email = db.Column(db.String(140))
    phone = db.Column(db.String(40))
    subject = db.Column(db.String(100))

class SchoolClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    class_teacher = db.Column(db.String(140))
    room = db.Column(db.String(40))

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    attendance_date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(250))
    student = db.relationship("Student", backref="attendance_records")

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    purpose = db.Column(db.String(100), nullable=False)
    reference = db.Column(db.String(80))
    payment_date = db.Column(db.String(20), default=lambda: date.today().isoformat())
    student = db.relationship("Student", backref="payments")

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    term = db.Column(db.String(40), nullable=False)
    score = db.Column(db.Float, nullable=False)
    student = db.relationship("Student", backref="results")

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator

@app.context_processor
def inject_globals():
    return {"school_name": "Presbyterian Fellowship Academy"}

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form.get("username", "").strip()).first()
        if user and user.active and user.check_password(request.form.get("password", "")):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have signed out.", "success")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html",
        students=Student.query.count(), teachers=Teacher.query.count(),
        classes=SchoolClass.query.count(), payments=db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0)).scalar(),
        recent_students=Student.query.order_by(Student.id.desc()).limit(5).all())

@app.route("/students", methods=["GET", "POST"])
@roles_required("admin", "teacher")
def students():
    if request.method == "POST":
        admission = request.form.get("admission_no", "").strip()
        name = request.form.get("full_name", "").strip()
        if not admission or not name:
            flash("Admission number and full name are required.", "error")
        elif Student.query.filter_by(admission_no=admission).first():
            flash("That admission number already exists.", "error")
        else:
            db.session.add(Student(admission_no=admission, full_name=name,
                gender=request.form.get("gender"), date_of_birth=request.form.get("date_of_birth"),
                class_name=request.form.get("class_name"), guardian_name=request.form.get("guardian_name"),
                guardian_phone=request.form.get("guardian_phone")))
            db.session.commit()
            flash("Student registered successfully.", "success")
            return redirect(url_for("students"))
    records = Student.query.order_by(Student.full_name).all()
    return render_template("students.html", records=records)

@app.route("/students/<int:student_id>/delete", methods=["POST"])
@roles_required("admin")
def delete_student(student_id):
    student = db.get_or_404(Student, student_id)
    Attendance.query.filter_by(student_id=student.id).delete()
    Payment.query.filter_by(student_id=student.id).delete()
    Result.query.filter_by(student_id=student.id).delete()
    db.session.delete(student)
    db.session.commit()
    flash("Student record deleted.", "success")
    return redirect(url_for("students"))

@app.route("/teachers", methods=["GET", "POST"])
@roles_required("admin")
def teachers():
    if request.method == "POST":
        staff_no, name = request.form.get("staff_no", "").strip(), request.form.get("full_name", "").strip()
        if not staff_no or not name:
            flash("Staff number and full name are required.", "error")
        elif Teacher.query.filter_by(staff_no=staff_no).first():
            flash("That staff number already exists.", "error")
        else:
            db.session.add(Teacher(staff_no=staff_no, full_name=name, email=request.form.get("email"),
                phone=request.form.get("phone"), subject=request.form.get("subject")))
            db.session.commit()
            flash("Teacher added successfully.", "success")
            return redirect(url_for("teachers"))
    return render_template("teachers.html", records=Teacher.query.order_by(Teacher.full_name).all())

@app.route("/classes", methods=["GET", "POST"])
@roles_required("admin", "teacher")
def classes():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name and not SchoolClass.query.filter_by(name=name).first():
            db.session.add(SchoolClass(name=name, class_teacher=request.form.get("class_teacher"), room=request.form.get("room")))
            db.session.commit()
            flash("Class created.", "success")
            return redirect(url_for("classes"))
        flash("Enter a class name that is not already in use.", "error")
    return render_template("classes.html", records=SchoolClass.query.order_by(SchoolClass.name).all())

@app.route("/attendance", methods=["GET", "POST"])
@roles_required("admin", "teacher")
def attendance():
    learners = Student.query.order_by(Student.full_name).all()
    if request.method == "POST":
        sid = request.form.get("student_id")
        if sid and db.session.get(Student, int(sid)):
            db.session.add(Attendance(student_id=int(sid), attendance_date=request.form.get("attendance_date") or date.today().isoformat(),
                status=request.form.get("status"), note=request.form.get("note")))
            db.session.commit()
            flash("Attendance saved.", "success")
            return redirect(url_for("attendance"))
        flash("Select a valid student.", "error")
    records = Attendance.query.order_by(Attendance.id.desc()).limit(50).all()
    return render_template("attendance.html", learners=learners, records=records, today=date.today().isoformat())

@app.route("/fees", methods=["GET", "POST"])
@roles_required("admin", "accountant")
def fees():
    learners = Student.query.order_by(Student.full_name).all()
    if request.method == "POST":
        sid = request.form.get("student_id")
        try:
            amount = float(request.form.get("amount", "0"))
            if not sid or not db.session.get(Student, int(sid)) or amount <= 0:
                raise ValueError()
            db.session.add(Payment(student_id=int(sid), amount=amount, purpose=request.form.get("purpose", "School fees"),
                reference=request.form.get("reference"), payment_date=request.form.get("payment_date") or date.today().isoformat()))
            db.session.commit()
            flash("Payment recorded.", "success")
            return redirect(url_for("fees"))
        except (ValueError, TypeError):
            flash("Enter a valid student and payment amount.", "error")
    records = Payment.query.order_by(Payment.id.desc()).limit(100).all()
    return render_template("fees.html", learners=learners, records=records, today=date.today().isoformat())

@app.route("/results", methods=["GET", "POST"])
@roles_required("admin", "teacher")
def results():
    learners = Student.query.order_by(Student.full_name).all()
    if request.method == "POST":
        try:
            sid, score = int(request.form.get("student_id")), float(request.form.get("score"))
            if not db.session.get(Student, sid) or score < 0 or score > 100:
                raise ValueError()
            db.session.add(Result(student_id=sid, subject=request.form.get("subject"), term=request.form.get("term"), score=score))
            db.session.commit()
            flash("Result saved.", "success")
            return redirect(url_for("results"))
        except (ValueError, TypeError):
            flash("Check the student and enter a score from 0 to 100.", "error")
    records = Result.query.order_by(Result.id.desc()).limit(100).all()
    return render_template("results.html", learners=learners, records=records)

@app.route("/users", methods=["GET", "POST"])
@roles_required("admin")
def users():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        name = request.form.get("full_name", "").strip()
        role = request.form.get("role", "teacher")
        if not username or not name or len(password) < 10 or role not in {"admin","teacher","accountant","parent","student"}:
            flash("Complete all fields. Password must be at least 10 characters.", "error")
        elif User.query.filter_by(username=username).first():
            flash("Username already exists.", "error")
        else:
            user = User(username=username, full_name=name, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("User account created.", "success")
            return redirect(url_for("users"))
    return render_template("users.html", records=User.query.order_by(User.username).all())

@app.errorhandler(403)
def forbidden(_):
    return render_template("message.html", title="Access restricted", message="Your account does not have permission to open this section."), 403

@app.errorhandler(404)
def not_found(_):
    return render_template("message.html", title="Page not found", message="The page you requested could not be found."), 404

def initialize():
    with app.app_context():
        db.create_all()
        admin_name = os.environ.get("ADMIN_USERNAME", "admin")
        admin_password = os.environ.get("ADMIN_PASSWORD")
        if not User.query.filter_by(username=admin_name).first():
            if not admin_password:
                admin_password = "ChangeThisNow123!"
                print("IMPORTANT: Temporary admin login: admin / ChangeThisNow123! Change it immediately.")
            admin = User(username=admin_name, full_name="School Administrator", role="admin")
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()

initialize()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
