from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from db import init_db, get_all_students, get_user, create_user, create_student, delete_student, get_all_courses, create_course, enroll_student, get_student_courses
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Passwords must match")])
    role = SelectField('Role', choices=[('student', 'Student'), ('teacher', 'Teacher'), ('admin', 'Admin')], default='student', validators=[DataRequired()])
    submit = SubmitField('Register')

# Initialize DB on start (upgrades schema)
# init_db()  # Moved to __main__ to avoid import error

@app.route('/')
def index():
    students = get_all_students()
    courses = get_all_courses()
    return render_template('index.html', students=students, courses=courses)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        user = get_user(username, password)
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3] if len(user) > 3 else 'student'
            flash('Login successful!', 'success')
            return redirect('/dashboard')
        flash('Invalid credentials. Check username/password.', 'error')
    return render_template('login.html', form=form)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')
    students = get_all_students()
    enrolled_courses = []
    if 'user_id' in session:
        enrolled_courses = get_student_courses(session['user_id'])
    return render_template('dashboard.html', students=students, enrolled_courses=enrolled_courses, username=session['username'], role=session.get('role', 'student'))

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        if create_student(name, email):
            flash('Student added successfully!', 'success')
            return redirect('/dashboard')
        flash('Error: Invalid or duplicate email', 'error')
    return render_template('add.html')


@app.route('/delete/<int:id>')
def delete(id):
    delete_student(id)
    flash('Student deleted!', 'success')
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect('/') 

@app.route('/courses', methods=['GET', 'POST'])
def courses():
    if request.method == 'POST':
        name = request.form['name'].strip()
        if create_course(name, session.get('user_id')):
            flash('Course created successfully!', 'success')
        else:
            flash('Course name already exists', 'error')
        return redirect('/courses')
    
    courses = get_all_courses()
    enrolled = []
    enrolled_ids = []
    if 'user_id' in session:
        enrolled = get_student_courses(session['user_id'])
        enrolled_ids = [c[0] for c in enrolled]
        courses = [(c, c[0] in enrolled_ids) for c in courses]
    return render_template('courses.html', courses=courses, enrolled_ids=enrolled_ids)

@app.route('/enroll/<int:course_id>')
def enroll(course_id):
    if 'user_id' not in session:
        flash('Please login to enroll', 'error')
        return redirect('/login')
    if enroll_student(session['user_id'], course_id):
        flash('Successfully enrolled in course!', 'success')
    else:
        flash('Already enrolled or error', 'error')
    return redirect('/courses')

@app.route('/enroll-multiple', methods=['POST'])
def enroll_multiple():
    if 'user_id' not in session:
        flash('Please login to enroll', 'error')
        return redirect('/login')
    course_ids = request.form.getlist('course_ids')
    if not course_ids:
        flash('No courses selected', 'error')
        return redirect('/courses')
    success_count = 0
    for cid in course_ids:
        if enroll_student(session['user_id'], int(cid)):
            success_count += 1
    if success_count:
        flash(f'Successfully enrolled in {success_count} course(s)!', 'success')
    else:
        flash('Already enrolled in selected courses or error occurred', 'error')
    return redirect('/courses')

# Removed duplicate / route - index() handles /

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data
        password = form.password.data
        role = form.role.data
        if create_user(username, email, password, role):
            # Auto-login new user
            user = get_user(username, password)
            if user:
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[3] if len(user) > 3 else 'student'
            flash('Registration successful! Welcome to dashboard.', 'success')
            return redirect('/dashboard')
        else:
            flash('Registration failed: Username or email already exists, or invalid data.', 'error')
    return render_template('register.html', form=form)

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000, debug=True)
