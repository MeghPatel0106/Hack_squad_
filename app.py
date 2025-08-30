from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timezone
import uuid
from blockchain import get_blockchain
from blockchain.realtime_chain import init_realtime_blockchain, get_realtime_blockchain

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SocketIO for real-time communication
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_type = db.Column(db.String(20), default='user')  # 'user' or 'authority'
    tokens = db.Column(db.Integer, default=0)  # Number of hydrogen tokens owned

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Hydrogen Credit model
class HydrogenCredit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    credit_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    production_capacity = db.Column(db.Float, nullable=False)  # MWh
    hydrogen_weight_kg = db.Column(db.Float, nullable=False)  # Weight in kg
    tokens_generated = db.Column(db.Integer, nullable=False)  # 1 kg = 1 token
    renewable_source = db.Column(db.String(50), nullable=False)
    production_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    facility_name = db.Column(db.String(100), nullable=False)
    certification_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price_per_token = db.Column(db.Float, nullable=False)  # Price per token
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected', 'available', 'sold', 'retired'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    verified_at = db.Column(db.DateTime, nullable=True)
    verified_by = db.Column(db.String(100), nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    blockchain_hash = db.Column(db.String(64), nullable=True)
    certificate_id = db.Column(db.String(36), nullable=True)
    sold_at = db.Column(db.DateTime, nullable=True)
    retired_at = db.Column(db.DateTime, nullable=True)

    seller = db.relationship('User', foreign_keys=[seller_id])
    buyer = db.relationship('User', foreign_keys=[buyer_id])

# Transaction model
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    credit_id = db.Column(db.Integer, db.ForeignKey('hydrogen_credit.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'sale', 'retirement'
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    credit = db.relationship('HydrogenCredit')
    seller = db.relationship('User', foreign_keys=[seller_id])
    buyer = db.relationship('User', foreign_keys=[buyer_id])

# Login required decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    
    # Check if user exists in database
    if not user:
        # User doesn't exist in database, clear session and redirect to login
        session.clear()
        flash('User account not found. Please log in again.', 'error')
        return redirect(url_for('login'))
    
    # Get user's credits and transactions (users can both buy and sell)
    # Seller statistics
    total_credits_sold = HydrogenCredit.query.filter_by(seller_id=user.id).count()
    sold_credits = HydrogenCredit.query.filter_by(seller_id=user.id, status='sold').count()
    available_credits = HydrogenCredit.query.filter_by(seller_id=user.id, status='approved').count()
    total_revenue = db.session.query(db.func.sum(Transaction.amount)).filter_by(seller_id=user.id).scalar() or 0
    total_tokens_sold = db.session.query(db.func.sum(HydrogenCredit.tokens_generated)).filter_by(seller_id=user.id, status='sold').scalar() or 0
    
    # Buyer statistics
    total_credits_bought = HydrogenCredit.query.filter_by(buyer_id=user.id).count()
    total_spent = db.session.query(db.func.sum(Transaction.amount)).filter_by(buyer_id=user.id).scalar() or 0
    total_tokens_bought = db.session.query(db.func.sum(HydrogenCredit.tokens_generated)).filter_by(buyer_id=user.id, status='sold').scalar() or 0
    avg_price = db.session.query(db.func.avg(HydrogenCredit.price_per_token)).filter_by(buyer_id=user.id, status='sold').scalar() or 0
    
    # Combined recent transactions (both buying and selling)
    recent_transactions = db.session.query(Transaction).filter(
        (Transaction.seller_id == user.id) | (Transaction.buyer_id == user.id)
    ).order_by(Transaction.created_at.desc()).limit(5).all()
    
    # Platform statistics
    total_platform_credits = HydrogenCredit.query.count()
    total_platform_transactions = Transaction.query.count()
    avg_platform_price = db.session.query(db.func.avg(HydrogenCredit.price_per_token)).scalar() or 0
    active_suppliers = db.session.query(db.func.count(db.distinct(HydrogenCredit.seller_id))).scalar() or 0
    
    # Get user's blockchain certificates
    user_certificates = HydrogenCredit.query.filter_by(seller_id=user.id).all()
    active_certificates = [c for c in user_certificates if c.blockchain_hash and c.status != 'sold']
    retired_certificates = [c for c in user_certificates if c.retired_at is not None]
    
    # Get available verified credits for buyers (all approved credits from other users)
    available_verified_credits = db.session.query(HydrogenCredit, User.username.label('seller_name')).join(
        User, HydrogenCredit.seller_id == User.id
    ).filter(
        HydrogenCredit.status == 'approved',
        HydrogenCredit.seller_id != user.id,  # Exclude user's own credits
        HydrogenCredit.buyer_id.is_(None)  # Only unsold credits
    ).order_by(HydrogenCredit.created_at.desc()).all()
    
    return render_template('dashboard.html', 
                         user=user, 
                         total_credits_sold=total_credits_sold,
                         total_credits_bought=total_credits_bought,
                         sold_credits=sold_credits,
                         available_credits=available_credits,
                         total_revenue=total_revenue,
                         total_spent=total_spent,
                         total_tokens_sold=total_tokens_sold,
                         total_tokens_bought=total_tokens_bought,
                         avg_price=avg_price,
                         recent_transactions=recent_transactions,
                         total_platform_credits=total_platform_credits,
                         total_platform_transactions=total_platform_transactions,
                         avg_platform_price=avg_platform_price,
                         active_suppliers=active_suppliers,
                         user_certificates=user_certificates,
                         active_certificates=active_certificates,
                         retired_certificates=retired_certificates,
                         available_verified_credits=available_verified_credits)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_type'] = user.user_type
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')
        
        # Create new user (default to regular user, not authority)
        user = User(username=username, email=email, user_type='user')
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/seller_panel')
@login_required
def seller_panel():
    user = User.query.get(session['user_id'])
    
    # Check if user exists in database
    if not user:
        # User doesn't exist in database, clear session and redirect to login
        session.clear()
        flash('User account not found. Please log in again.', 'error')
        return redirect(url_for('login'))
    
    # Get seller statistics (any user can sell)
    total_credits = HydrogenCredit.query.filter_by(seller_id=user.id).count()
    total_revenue = db.session.query(db.func.sum(Transaction.amount)).filter_by(seller_id=user.id).scalar() or 0
    total_tokens = db.session.query(db.func.sum(HydrogenCredit.tokens_generated)).filter_by(seller_id=user.id, status='approved').scalar() or 0
    
    # Get recent submissions
    recent_submissions = HydrogenCredit.query.filter_by(seller_id=user.id).order_by(HydrogenCredit.created_at.desc()).limit(5).all()
    
    return render_template('seller_panel.html', 
                         user=user,
                         total_credits=total_credits,
                         total_revenue=total_revenue,
                         total_tokens=total_tokens,
                         recent_submissions=recent_submissions)

@app.route('/submit_production', methods=['POST'])
@login_required
def submit_production():
    try:
        user = User.query.get(session['user_id'])
        
        # Check if user exists in database
        if not user:
            # User doesn't exist in database, clear session and redirect to login
            session.clear()
            flash('User account not found. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        # Get form data
        production_capacity = float(request.form['production_capacity'])
        hydrogen_weight_kg = float(request.form['hydrogen_weight_kg'])
        renewable_source = request.form['renewable_source']
        production_date = datetime.strptime(request.form['production_date'], '%Y-%m-%d').date()
        location = request.form['location']
        facility_name = request.form['facility_name']
        certification_type = request.form['certification_type']
        description = request.form.get('description', '')
        
        # Calculate tokens (1 kg = 1 token)
        tokens_generated = int(hydrogen_weight_kg)
        
        # Calculate price per token based on certification type
        price_mapping = {
            'standard': 2.5,
            'premium': 4.2,
            'ultra': 5.5
        }
        price_per_token = price_mapping.get(certification_type, 2.5)
        
        # Create new hydrogen credit
        new_credit = HydrogenCredit(
            seller_id=user.id,
            production_capacity=production_capacity,
            hydrogen_weight_kg=hydrogen_weight_kg,
            tokens_generated=tokens_generated,
            renewable_source=renewable_source,
            production_date=production_date,
            location=location,
            facility_name=facility_name,
            certification_type=certification_type,
            description=description,
            price_per_token=price_per_token,
            status='pending'
        )
        
        db.session.add(new_credit)
        db.session.commit()
        
        # Issue blockchain certificate
        try:
            blockchain = get_blockchain()
            certificate_data = {
                'seller_id': user.id,
                'facility_name': facility_name,
                'hydrogen_weight_kg': hydrogen_weight_kg,
                'tokens_generated': tokens_generated,
                'renewable_source': renewable_source,
                'production_date': production_date.isoformat(),
                'location': location,
                'certification_type': certification_type,
                'price_per_token': price_per_token
            }
            
            blockchain_hash = blockchain.issue_certificate(certificate_data)
            
            # Update credit with blockchain information
            new_credit.blockchain_hash = blockchain_hash
            new_credit.certificate_id = certificate_data.get('certificate_id', str(uuid.uuid4()))
            db.session.commit()
            
            # Emit real-time blockchain event
            realtime_chain = get_realtime_blockchain()
            if realtime_chain:
                realtime_chain.emit_certificate_issued(certificate_data, blockchain_hash)
            
            flash(f'Production data submitted successfully! {tokens_generated} tokens generated for {hydrogen_weight_kg} kg of {renewable_source} hydrogen. Blockchain certificate issued with hash: {blockchain_hash[:16]}...', 'success')
            
        except Exception as e:
            flash(f'Production data submitted, but blockchain certificate issuance failed: {str(e)}', 'warning')
    
        return redirect(url_for('seller_panel'))
        
    except Exception as e:
        flash(f'Error submitting production data: {str(e)}', 'error')
        return redirect(url_for('seller_panel'))
        
    except Exception as e:
        flash(f'Error submitting production data: {str(e)}', 'error')
        return redirect(url_for('seller_panel'))

@app.route('/buyer_panel')
@login_required
def buyer_panel():
    user = User.query.get(session['user_id'])
    
    # Check if user exists in database
    if not user:
        # User doesn't exist in database, clear session and redirect to login
        session.clear()
        flash('User account not found. Please log in again.', 'error')
        return redirect(url_for('login'))
    
    # Get buyer statistics (any user can buy)
    credits_purchased = HydrogenCredit.query.filter_by(buyer_id=user.id).count()
    total_spent = db.session.query(db.func.sum(Transaction.amount)).filter_by(buyer_id=user.id).scalar() or 0
    tokens_acquired = db.session.query(db.func.sum(HydrogenCredit.tokens_generated)).filter_by(buyer_id=user.id, status='sold').scalar() or 0
    avg_price = db.session.query(db.func.avg(HydrogenCredit.price_per_token)).filter_by(buyer_id=user.id, status='sold').scalar() or 0
    
    # Get all available credits (both pending and approved) - buyers see data instantly
    available_credits = HydrogenCredit.query.filter(
        HydrogenCredit.status.in_(['pending', 'approved'])
    ).order_by(HydrogenCredit.created_at.desc()).all()
    
    # Get purchase history
    purchase_history = Transaction.query.filter_by(buyer_id=user.id).order_by(Transaction.created_at.desc()).limit(5).all()
    
    return render_template('buyer_panel.html', 
                         user=user,
                         credits_purchased=credits_purchased,
                         total_spent=total_spent,
                         tokens_acquired=tokens_acquired,
                         avg_price=avg_price,
                         available_credits=available_credits,
                         purchase_history=purchase_history)

@app.route('/buy_credit', methods=['POST'])
@login_required
def buy_credit():
    try:
        user = User.query.get(session['user_id'])
        
        # Check if user exists in database
        if not user:
            # User doesn't exist in database, clear session and redirect to login
            session.clear()
            flash('User account not found. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        credit_id = request.form['credit_id']
        
        # Get the credit (can be pending or approved)
        credit = HydrogenCredit.query.filter_by(credit_id=credit_id).first()
        if not credit:
            flash('Credit not found.', 'error')
            return redirect(url_for('buyer_panel'))
        
        # Only allow purchase of approved credits
        if credit.status != 'approved':
            flash('This credit is still pending approval and cannot be purchased yet.', 'error')
            return redirect(url_for('buyer_panel'))
        
        # Check if already sold
        if credit.status == 'sold':
            flash('Credit already sold.', 'error')
            return redirect(url_for('buyer_panel'))
        
        # Calculate total amount
        total_amount = credit.tokens_generated * credit.price_per_token
        
        # Check if buyer has enough tokens or money (for now, we'll assume direct purchase)
        # In a real system, you might want to implement a token wallet
        
        # Update credit status
        credit.buyer_id = user.id
        credit.status = 'sold'
        credit.sold_at = datetime.now(timezone.utc)
        
        # Transfer tokens from seller to buyer
        seller = User.query.get(credit.seller_id)
        seller.tokens -= credit.tokens_generated
        user.tokens += credit.tokens_generated
        
        # Create transaction record
        transaction = Transaction(
            credit_id=credit.id,
            seller_id=credit.seller_id,
            buyer_id=user.id,
            transaction_type='sale',
            amount=total_amount
        )
        
        db.session.add(transaction)
        
        # Emit real-time blockchain event for credit purchase
        realtime_chain = get_realtime_blockchain()
        if realtime_chain:
            trade_data = {
                'certificate_id': credit.certificate_id,
                'blockchain_hash': credit.blockchain_hash,
                'seller_id': credit.seller_id,
                'buyer_id': user.id,
                'tokens_amount': credit.tokens_generated,
                'price_per_token': credit.price_per_token,
                'total_amount': total_amount
            }
            realtime_chain.emit_certificate_traded(trade_data)
        
        # Retire blockchain certificate
        if credit.blockchain_hash:
            try:
                blockchain = get_blockchain()
                if blockchain.retire_certificate(credit.blockchain_hash):
                    credit.retired_at = datetime.now(timezone.utc)
                    flash(f'Successfully purchased {credit.tokens_generated} tokens of {credit.renewable_source} hydrogen credits for ${total_amount:.2f}! Blockchain certificate retired.', 'success')
                else:
                    flash(f'Credit purchased but blockchain retirement failed. Please contact support.', 'warning')
            except Exception as e:
                flash(f'Credit purchased but blockchain retirement failed: {str(e)}', 'warning')
        else:
            flash(f'Successfully purchased {credit.tokens_generated} tokens of {credit.renewable_source} hydrogen credits for ${total_amount:.2f}!', 'success')
        
        db.session.commit()
        return redirect(url_for('buyer_panel'))
        
    except Exception as e:
        flash(f'Error purchasing credit: {str(e)}', 'error')
        return redirect(url_for('buyer_panel'))

@app.route('/dashboard_buy_credit', methods=['POST'])
@login_required
def dashboard_buy_credit():
    """Purchase credit directly from dashboard"""
    try:
        user = User.query.get(session['user_id'])
        
        # Check if user exists in database
        if not user:
            session.clear()
            flash('User account not found. Please log in again.', 'error')
            return redirect(url_for('dashboard'))
        
        credit_id = request.form['credit_id']
        
        # Get the credit
        credit = HydrogenCredit.query.filter_by(credit_id=credit_id).first()
        if not credit:
            flash('Credit not found.', 'error')
            return redirect(url_for('dashboard'))
        
        # Only allow purchase of approved credits
        if credit.status != 'approved':
            flash('Only approved credits can be purchased.', 'error')
            return redirect(url_for('dashboard'))
        
        # Check if credit is already sold
        if credit.status == 'sold':
            flash('This credit has already been sold.', 'error')
            return redirect(url_for('dashboard'))
        
        # Calculate total amount
        total_amount = credit.tokens_generated * credit.price_per_token
        
        # Update credit status
        credit.status = 'sold'
        credit.buyer_id = user.id
        credit.sold_at = datetime.now(timezone.utc)
        
        # Transfer tokens from seller to buyer
        seller = User.query.get(credit.seller_id)
        if seller:
            seller.tokens -= credit.tokens_generated
            user.tokens += credit.tokens_generated
        
        # Create transaction record
        transaction = Transaction(
            credit_id=credit.id,
            seller_id=credit.seller_id,
            buyer_id=user.id,
            amount=total_amount,
            transaction_type='sale',
            created_at=datetime.now(timezone.utc)
        )
        
        db.session.add(transaction)
        
        # Emit real-time blockchain event for credit purchase
        realtime_chain = get_realtime_blockchain()
        if realtime_chain:
            trade_data = {
                'certificate_id': credit.certificate_id,
                'blockchain_hash': credit.blockchain_hash,
                'seller_id': credit.seller_id,
                'buyer_id': user.id,
                'tokens_amount': credit.tokens_generated,
                'price_per_token': credit.price_per_token,
                'total_amount': total_amount
            }
            realtime_chain.emit_certificate_traded(trade_data)
        
        # Retire blockchain certificate
        if credit.blockchain_hash:
            try:
                blockchain = get_blockchain()
                if blockchain.retire_certificate(credit.blockchain_hash):
                    credit.retired_at = datetime.now(timezone.utc)
                    flash(f'Successfully purchased {credit.tokens_generated} tokens of {credit.renewable_source} hydrogen credits for ${total_amount:.2f}! Blockchain certificate retired.', 'success')
                else:
                    flash(f'Credit purchased but blockchain retirement failed. Please contact support.', 'warning')
            except Exception as e:
                flash(f'Credit purchased but blockchain retirement failed: {str(e)}', 'warning')
        else:
            flash(f'Successfully purchased {credit.tokens_generated} tokens of {credit.renewable_source} hydrogen credits for ${total_amount:.2f}!', 'success')
        
        db.session.commit()
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash(f'Error purchasing credit: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/retire_credit', methods=['POST'])
@login_required
def retire_credit():
    try:
        user = User.query.get(session['user_id'])
        
        # Check if user exists in database
        if not user:
            # User doesn't exist in database, clear session and redirect to login
            session.clear()
            flash('User account not found. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        credit_id = request.form['credit_id']
        
        # Get the credit (must be owned by the user)
        credit = HydrogenCredit.query.filter_by(credit_id=credit_id, buyer_id=user.id, status='sold').first()
        if not credit:
            flash('Credit not found or not owned by you.', 'error')
            return redirect(url_for('dashboard'))
        
        # Update credit status
        credit.status = 'retired'
        credit.retired_at = datetime.now(timezone.utc)
        
        # Create retirement transaction
        transaction = Transaction(
            credit_id=credit.id,
            seller_id=credit.seller_id,
            buyer_id=user.id,
            transaction_type='retirement',
            amount=0  # No money involved in retirement
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'Successfully retired {credit.production_capacity} MWh of {credit.renewable_source} hydrogen credits!', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash(f'Error retiring credit: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/authority_panel')
@login_required
def authority_panel():
    user = User.query.get(session['user_id'])
    
    # Check if user exists in database
    if not user:
        # User doesn't exist in database, clear session and redirect to login
        session.clear()
        flash('User account not found. Please log in again.', 'error')
        return redirect(url_for('login'))
    
    # Check if user is authority
    if user.user_type != 'authority':
        flash('Access denied. Authority privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get pending requests
    pending_requests = HydrogenCredit.query.filter_by(status='pending').order_by(HydrogenCredit.created_at.asc()).all()
    
    # Get today's statistics
    today = datetime.now().date()
    approved_requests = HydrogenCredit.query.filter(
        HydrogenCredit.status == 'approved',
        db.func.date(HydrogenCredit.verified_at) == today
    ).count()
    
    rejected_requests = HydrogenCredit.query.filter(
        HydrogenCredit.status == 'rejected',
        db.func.date(HydrogenCredit.verified_at) == today
    ).count()
    
    total_verified = HydrogenCredit.query.filter(
        HydrogenCredit.status.in_(['approved', 'rejected'])
    ).count()
    
    # Get recent decisions
    recent_decisions = HydrogenCredit.query.filter(
        HydrogenCredit.status.in_(['approved', 'rejected'])
    ).order_by(HydrogenCredit.verified_at.desc()).limit(10).all()
    
    # Get seller credits count for each pending request
    seller_credits_count = {}
    for request in pending_requests:
        count = HydrogenCredit.query.filter_by(
            seller_id=request.seller_id, 
            status='approved'
        ).count()
        seller_credits_count[request.seller_id] = count
    
    return render_template('authority.html',
                         user=user,
                         pending_requests=pending_requests,
                         approved_requests=approved_requests,
                         rejected_requests=rejected_requests,
                         total_verified=total_verified,
                         recent_decisions=recent_decisions,
                         seller_credits_count=seller_credits_count)

@app.route('/verify_request', methods=['POST'])
@login_required
def verify_request():
    try:
        user = User.query.get(session['user_id'])
        
        # Check if user exists in database
        if not user:
            # User doesn't exist in database, clear session and redirect to login
            session.clear()
            flash('User account not found. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        # Check if user is authority
        if user.user_type != 'authority':
            flash('Access denied. Authority privileges required.', 'error')
            return redirect(url_for('dashboard'))
        
        credit_id = request.form['credit_id']
        action = request.form['action']
        
        # Get the credit
        credit = HydrogenCredit.query.filter_by(credit_id=credit_id, status='pending').first()
        if not credit:
            flash('Credit request not found or already processed.', 'error')
            return redirect(url_for('authority_panel'))
        
        if action == 'approve':
            # Approve the credit
            credit.status = 'approved'
            credit.verified_at = datetime.now(timezone.utc)
            credit.verified_by = user.username
            
            # Give tokens to the seller (1 kg = 1 token)
            seller = User.query.get(credit.seller_id)
            seller.tokens += credit.tokens_generated
            
            flash(f'Successfully approved {credit.hydrogen_weight_kg} kg of {credit.renewable_source} hydrogen! Seller received {credit.tokens_generated} tokens. Credit is now active on the blockchain.', 'success')
            
        elif action == 'reject':
            # Get rejection reason
            rejection_reason = request.form.get('rejection_reason', 'No reason provided')
            
            # Reject the credit
            credit.status = 'rejected'
            credit.verified_at = datetime.now(timezone.utc)
            credit.verified_by = user.username
            credit.rejection_reason = rejection_reason
            
            flash(f'Request rejected: {rejection_reason}', 'error')
            

        
        else:
            flash('Invalid action specified.', 'error')
            return redirect(url_for('authority_panel'))
        
        db.session.commit()
        return redirect(url_for('authority_panel'))
        
    except Exception as e:
        flash(f'Error processing verification: {str(e)}', 'error')
        return redirect(url_for('authority_panel'))



@app.route('/blockchain_dashboard')
@login_required
def blockchain_dashboard():
    user = User.query.get(session['user_id'])
    
    # Check if user exists in database
    if not user:
        # User doesn't exist in database, clear session and redirect to login
        session.clear()
        flash('User account not found. Please log in again.', 'error')
        return redirect(url_for('login'))
    
    try:
        blockchain = get_blockchain()
        chain_info = blockchain.get_chain_info()
        
        # Get user's certificates
        user_certificates = HydrogenCredit.query.filter_by(seller_id=user.id).all()
        user_certificates_data = []
        
        for cert in user_certificates:
            if cert.blockchain_hash:
                is_valid, cert_data = blockchain.verify_certificate(cert.blockchain_hash)
                status = blockchain.get_certificate_status(cert.blockchain_hash)
                user_certificates_data.append({
                    'credit': cert,
                    'blockchain_hash': cert.blockchain_hash,
                    'is_valid': is_valid,
                    'status': status,
                    'certificate_data': cert_data
                })
        
        return render_template('blockchain_dashboard.html',
                             user=user,
                             chain_info=chain_info,
                             user_certificates=user_certificates_data)
                             
    except Exception as e:
        flash(f'Error accessing blockchain dashboard: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/realtime_blockchain')
@login_required
def realtime_blockchain_dashboard():
    user = User.query.get(session['user_id'])
    
    # Check if user exists in database
    if not user:
        # User doesn't exist in database, clear session and redirect to login
        session.clear()
        flash('User account not found. Please log in again.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        realtime_chain = get_realtime_blockchain()
        if realtime_chain:
            live_stats = realtime_chain.get_live_statistics()
            event_history = realtime_chain.get_event_history(limit=50)
        else:
            live_stats = {}
            event_history = []
        
        return render_template('realtime_blockchain.html',
                             user=user,
                             live_stats=live_stats,
                             event_history=event_history)
                             
    except Exception as e:
        flash(f'Error accessing real-time blockchain dashboard: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))



def add_sample_data():
    """Add sample data to the database for demonstration"""
    with app.app_context():
        # Check if sample data already exists
        if User.query.count() > 0:
            return
        
        # Create sample users
        user1 = User(username='solar_farm', email='solar@example.com', user_type='user')
        user1.set_password('password123')
        
        user2 = User(username='wind_farm', email='wind@example.com', user_type='user')
        user2.set_password('password123')
        
        user3 = User(username='industrial_buyer', email='buyer@example.com', user_type='user')
        user3.set_password('password123')
        
        # Create authority user
        authority1 = User(username='authority1', email='authority@example.com', user_type='authority')
        authority1.set_password('password123')
        
        db.session.add_all([user1, user2, user3, authority1])
        db.session.commit()
        
        # Create sample hydrogen credits
        credit1 = HydrogenCredit(
            seller_id=user1.id,
            production_capacity=2.5,  # MWh
            hydrogen_weight_kg=50.0,  # 50 kg hydrogen
            tokens_generated=50,      # 50 tokens (1 kg = 1 token)
            renewable_source='solar',
            production_date=datetime.now().date(),
            location='California',
            facility_name='Solar Farm Alpha',
            certification_type='standard',
            description='High-efficiency solar hydrogen production',
            price_per_token=2.5,      # $2.50 per token
            status='approved',
            verified_at=datetime.now(timezone.utc),
            verified_by='solar_farm'  # Self-verified for demo
        )
        
        credit2 = HydrogenCredit(
            seller_id=user2.id,
            production_capacity=1.8,  # MWh
            hydrogen_weight_kg=36.0,  # 36 kg hydrogen
            tokens_generated=36,      # 36 tokens
            renewable_source='wind',
            production_date=datetime.now().date(),
            location='Texas',
            facility_name='Wind Farm Beta',
            certification_type='premium',
            description='Offshore wind hydrogen production',
            price_per_token=4.2,      # $4.20 per token
            status='pending'
        )
        
        credit3 = HydrogenCredit(
            seller_id=user1.id,
            production_capacity=3.2,  # MWh
            hydrogen_weight_kg=64.0,  # 64 kg hydrogen
            tokens_generated=64,      # 64 tokens
            renewable_source='solar',
            production_date=datetime.now().date(),
            location='Nevada',
            facility_name='Desert Solar Plant',
            certification_type='ultra',
            description='Desert solar hydrogen with advanced storage',
            price_per_token=5.5,      # $5.50 per token
            status='pending'
        )
        
        db.session.add_all([credit1, credit2, credit3])
        db.session.commit()
        
        print("Sample data added successfully!")

# WebSocket event handlers
@socketio.on('connect', namespace='/blockchain')
def handle_connect():
    """Handle WebSocket connection"""
    print(f"🔌 Client connected: {request.sid}")
    emit('connection_status', {'status': 'connected'})

@socketio.on('disconnect', namespace='/blockchain')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print(f"🔌 Client disconnected: {request.sid}")

@socketio.on('join_blockchain', namespace='/blockchain')
def handle_join_blockchain():
    """Handle user joining blockchain room"""
    join_room('blockchain')
    emit('room_joined', {'room': 'blockchain'})
    
    # Get real-time blockchain instance
    realtime_chain = get_realtime_blockchain()
    if realtime_chain:
        # Connect user to real-time system
        user_id = session.get('user_id', 'anonymous')
        realtime_chain.connect_user(str(user_id), request.sid)
        
        # Send current statistics
        stats = realtime_chain.get_live_statistics()
        emit('statistics_update', stats)

@socketio.on('get_statistics', namespace='/blockchain')
def handle_get_statistics():
    """Handle statistics request"""
    realtime_chain = get_realtime_blockchain()
    if realtime_chain:
        stats = realtime_chain.get_live_statistics()
        emit('statistics_update', stats)

@socketio.on('subscribe_events', namespace='/blockchain')
def handle_subscribe_events(data):
    """Handle event subscription"""
    realtime_chain = get_realtime_blockchain()
    if realtime_chain:
        user_id = session.get('user_id', 'anonymous')
        event_types = data.get('event_types', ['all'])
        realtime_chain.subscribe_to_events(str(user_id), event_types)
        emit('subscription_confirmed', {'event_types': event_types})

# Initialize real-time blockchain system
def init_realtime_system():
    """Initialize the real-time blockchain system"""
    with app.app_context():
        # Initialize real-time blockchain
        realtime_chain, event_manager = init_realtime_blockchain(socketio)
        print("🚀 Real-time blockchain system initialized")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        add_sample_data()  # Add sample data for demonstration
        init_realtime_system()  # Initialize real-time system
    
    # Run with SocketIO
    socketio.run(app, debug=True, port=5001, host='0.0.0.0')
