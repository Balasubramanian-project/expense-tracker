from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from models import db
from models.user import User

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@auth_bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Validation
        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html', name=name, email=email)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', name=name, email=email)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html', name=name, email=email)

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address is already registered.', 'danger')
            return render_template('register.html', name=name, email=email)

        # Create new user
        new_user = User(name=name, email=email)
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('login.html', email=email)

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session.clear()
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            flash(f'Welcome back, {user.name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = g.user
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()

        if not name:
            flash('Name cannot be empty.', 'danger')
            return redirect(url_for('auth.profile'))

        user.name = name

        if current_password or new_password:
            if not user.check_password(current_password):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('auth.profile'))
            if len(new_password) < 6:
                flash('New password must be at least 6 characters long.', 'danger')
                return redirect(url_for('auth.profile'))
            user.set_password(new_password)

        try:
            db.session.commit()
            session['user_name'] = user.name
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile.', 'danger')

        return redirect(url_for('auth.profile'))

    return render_template('profile.html', user=user)
