from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'adsrwanda_ultra_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///adsrwanda.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(days=7)

db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(20), nullable=False) # 'buyer' or 'seller'

# Initialize database
with app.app_context():
    db.create_all()

# --- ROUTES ---

@app.route('/')
def index():
    # We pass an empty dictionary for categories so the template doesn't crash
    # Once we have a Listing table, we'll fetch them here
    return render_template('index.html', categories={'all_ads': []})

@app.route('/auth')
def auth():
    return render_template('auth.html')

@app.route('/register', methods=['POST'])
def register():
    phone = request.form.get('country_code') + request.form.get('phone')
    full_name = request.form.get('full_name')
    password = request.form.get('password')
    user_type = request.form.get('user_type')

    if User.query.filter_by(phone_number=phone).first():
        return "Phone number already registered."

    new_user = User(
        full_name=full_name,
        phone_number=phone,
        password_hash=generate_password_hash(password),
        user_type=user_type
    )
    
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('auth'))

@app.route('/login', methods=['POST'])
def login():
    try:
        # Combine country code and phone number
        country_code = request.form.get('country_code', '')
        phone_input = request.form.get('phone', '')
        phone = country_code + phone_input
        
        password = request.form.get('password')
        
        # Look up the user
        user_record = User.query.filter_by(phone_number=phone).first()

        # Verify password
        if user_record and check_password_hash(user_record.password_hash, password):
            session.permanent = True
            session['user_id'] = user_record.id
            session['user_type'] = user_record.user_type
            
            # Show a success pop-up
            flash(f"Welcome back, {user_record.full_name}!", "success")
            
            if user_record.user_type == 'seller':
                return redirect(url_for('dashboard'))
            return redirect(url_for('index'))
        
        # If login fails, show an error pop-up and stay on the auth page
        flash("Invalid phone number or password. Please try again.", "error")
        return redirect(url_for('auth'))

    except Exception as e:
        # In case of database or connection issues
        flash("An unexpected error occurred. Please try again later.", "error")
        return redirect(url_for('auth'))

@app.route('/dashboard')
def dashboard():
    # 1. Security Check
    if 'user_id' not in session or session.get('user_type') != 'seller':
        return redirect(url_for('auth'))
    
    # 2. Get the Actual User from the Database
    db_user = User.query.get(session['user_id'])
    
    # 3. Package the data for Jinja2 (this fixes the UndefinedError)
    user_data = {
        "name": db_user.full_name,
        "stats": {
            "views": "0",
            "active_ads": 0,
            "messages": 0
        },
        "listings": [] # Empty for now until we build the Listings table
    }
    
    return render_template('dashboard.html', user=user_data)

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "message")
    return redirect(url_for('auth'))

if __name__ == '__main__':
    app.run(debug=True)