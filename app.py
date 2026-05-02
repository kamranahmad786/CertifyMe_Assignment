"""
Qatar Foundation Admin Portal — Flask Backend
=============================================
Covers all user stories US-1.1 → US-2.6.
Database: SQLite (admin_portal.db)
"""

import os
import uuid
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, request, jsonify, session,
    send_from_directory, redirect, url_for
)
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# ─── App setup ──────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='sky', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'qf-admin-secret-key-change-in-production')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # "Remember me"
CORS(app, supports_credentials=True)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'admin_portal.db')


# ─── Database helpers ────────────────────────────────────────────────────────
def get_db():
    """Return a connection with row-factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables if they do not exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS admins (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name   TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS password_resets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id    INTEGER NOT NULL,
            token       TEXT    NOT NULL UNIQUE,
            expires_at  TEXT    NOT NULL,
            used        INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (admin_id) REFERENCES admins(id)
        );

        CREATE TABLE IF NOT EXISTS opportunities (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id            INTEGER NOT NULL,
            name                TEXT    NOT NULL,
            duration            TEXT    NOT NULL,
            start_date          TEXT    NOT NULL,
            description         TEXT    NOT NULL,
            skills              TEXT    NOT NULL,
            category            TEXT    NOT NULL,
            future_opportunities TEXT   NOT NULL,
            max_applicants      INTEGER,
            created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at          TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (admin_id) REFERENCES admins(id)
        );
    """)
    conn.commit()
    conn.close()


init_db()


# ─── Auth decorator ──────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated


# ─── Serve the frontend ─────────────────────────────────────────────────────
@app.route('/')
def serve_index():
    return send_from_directory('sky', 'admin.html')


# ═══════════════════════════════════════════════════════════════════════════
#  TASK 1 — AUTH ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

# ── US-1.1  Admin Sign Up ────────────────────────────────────────────────
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json(force=True)
    full_name = (data.get('full_name') or '').strip()
    email     = (data.get('email') or '').strip().lower()
    password  = (data.get('password') or '')
    confirm   = (data.get('confirm_password') or '')

    # --- Validations ---
    errors = []
    if not full_name:
        errors.append('Full name is required.')
    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        errors.append('A valid email address is required.')
    if not password or len(password) < 8:
        errors.append('Password must be at least 8 characters.')
    if password != confirm:
        errors.append('Passwords do not match.')

    if errors:
        return jsonify({'success': False, 'message': ' '.join(errors)}), 400

    # --- Check duplicate ---
    conn = get_db()
    existing = conn.execute('SELECT id FROM admins WHERE email = ?', (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'success': False, 'message': 'An account with this email already exists.'}), 409

    # --- Save ---
    hashed = generate_password_hash(password)
    conn.execute(
        'INSERT INTO admins (full_name, email, password) VALUES (?, ?, ?)',
        (full_name, email, hashed)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Account created successfully!'}), 201


# ── US-1.2  Admin Login ─────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(force=True)
    email      = (data.get('email') or '').strip().lower()
    password   = (data.get('password') or '')
    remember   = data.get('remember', False)

    if not email or not password:
        return jsonify({'success': False, 'message': 'Invalid email or password.'}), 401

    conn = get_db()
    admin = conn.execute('SELECT * FROM admins WHERE email = ?', (email,)).fetchone()
    conn.close()

    if not admin or not check_password_hash(admin['password'], password):
        return jsonify({'success': False, 'message': 'Invalid email or password.'}), 401

    # --- Create session ---
    session.permanent = bool(remember)
    session['admin_id']   = admin['id']
    session['admin_name'] = admin['full_name']
    session['admin_email'] = admin['email']

    return jsonify({
        'success': True,
        'message': 'Login successful!',
        'admin': {
            'id': admin['id'],
            'full_name': admin['full_name'],
            'email': admin['email']
        }
    })


# ── US-1.3  Forgot Password ─────────────────────────────────────────────
@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data  = request.get_json(force=True)
    email = (data.get('email') or '').strip().lower()

    # Always return the same message (privacy)
    success_msg = 'If this email is registered, a password reset link has been sent.'

    if not email:
        return jsonify({'success': True, 'message': success_msg})

    conn  = get_db()
    admin = conn.execute('SELECT id FROM admins WHERE email = ?', (email,)).fetchone()

    if admin:
        token      = str(uuid.uuid4())
        expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        conn.execute(
            'INSERT INTO password_resets (admin_id, token, expires_at) VALUES (?, ?, ?)',
            (admin['id'], token, expires_at)
        )
        conn.commit()

        # Log the reset link internally (no email sending required)
        reset_link = f"http://localhost:5000/reset-password?token={token}"
        print(f"[PASSWORD RESET] Admin ID {admin['id']} — {reset_link}  (expires {expires_at})")

    conn.close()
    return jsonify({'success': True, 'message': success_msg})


# ── Verify Reset Token (for completeness) ────────────────────────────────
@app.route('/api/verify-reset-token', methods=['POST'])
def verify_reset_token():
    data  = request.get_json(force=True)
    token = (data.get('token') or '').strip()

    if not token:
        return jsonify({'success': False, 'message': 'Token is required.'}), 400

    conn  = get_db()
    reset = conn.execute(
        'SELECT * FROM password_resets WHERE token = ? AND used = 0', (token,)
    ).fetchone()
    conn.close()

    if not reset:
        return jsonify({'success': False, 'message': 'Invalid or expired reset link.'}), 400

    if datetime.fromisoformat(reset['expires_at']) < datetime.utcnow():
        return jsonify({'success': False, 'message': 'This reset link has expired. Please request a new one.'}), 400

    return jsonify({'success': True, 'message': 'Token is valid.'})


# ── Logout ────────────────────────────────────────────────────────────────
@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully.'})


# ── Session check ─────────────────────────────────────────────────────────
@app.route('/api/me', methods=['GET'])
def me():
    if 'admin_id' in session:
        return jsonify({
            'success': True,
            'admin': {
                'id': session['admin_id'],
                'full_name': session['admin_name'],
                'email': session['admin_email']
            }
        })
    return jsonify({'success': False}), 401


# ═══════════════════════════════════════════════════════════════════════════
#  TASK 2 — OPPORTUNITY MANAGEMENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

# ── US-2.1  View All Opportunities (for the logged-in admin) ─────────────
@app.route('/api/opportunities', methods=['GET'])
@login_required
def get_opportunities():
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM opportunities WHERE admin_id = ? ORDER BY created_at DESC',
        (session['admin_id'],)
    ).fetchall()
    conn.close()

    opportunities = []
    for r in rows:
        opportunities.append({
            'id':                   r['id'],
            'name':                 r['name'],
            'duration':             r['duration'],
            'start_date':           r['start_date'],
            'description':          r['description'],
            'skills':               r['skills'].split(',') if r['skills'] else [],
            'category':             r['category'],
            'future_opportunities': r['future_opportunities'],
            'max_applicants':       r['max_applicants'],
            'created_at':           r['created_at'],
            'updated_at':           r['updated_at']
        })

    return jsonify({'success': True, 'opportunities': opportunities})


# ── US-2.2  Add a New Opportunity ────────────────────────────────────────
@app.route('/api/opportunities', methods=['POST'])
@login_required
def create_opportunity():
    data = request.get_json(force=True)

    name        = (data.get('name') or '').strip()
    duration    = (data.get('duration') or '').strip()
    start_date  = (data.get('start_date') or '').strip()
    description = (data.get('description') or '').strip()
    skills_raw  = (data.get('skills') or '').strip() if isinstance(data.get('skills'), str) else ','.join(data.get('skills', []))
    category    = (data.get('category') or '').strip()
    future_opp  = (data.get('future_opportunities') or '').strip()
    max_app     = data.get('max_applicants')

    # --- Validate required fields ---
    if not all([name, duration, start_date, description, skills_raw, category, future_opp]):
        return jsonify({'success': False, 'message': 'All required fields must be filled.'}), 400

    # Parse max_applicants
    max_applicants = None
    if max_app:
        try:
            max_applicants = int(max_app)
        except (ValueError, TypeError):
            pass

    conn = get_db()
    cursor = conn.execute(
        '''INSERT INTO opportunities
           (admin_id, name, duration, start_date, description, skills, category, future_opportunities, max_applicants)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (session['admin_id'], name, duration, start_date, description,
         skills_raw, category, future_opp, max_applicants)
    )
    opp_id = cursor.lastrowid
    conn.commit()

    # Return the newly created opportunity
    row = conn.execute('SELECT * FROM opportunities WHERE id = ?', (opp_id,)).fetchone()
    conn.close()

    return jsonify({
        'success': True,
        'message': 'Opportunity created successfully!',
        'opportunity': {
            'id':                   row['id'],
            'name':                 row['name'],
            'duration':             row['duration'],
            'start_date':           row['start_date'],
            'description':          row['description'],
            'skills':               row['skills'].split(',') if row['skills'] else [],
            'category':             row['category'],
            'future_opportunities': row['future_opportunities'],
            'max_applicants':       row['max_applicants'],
            'created_at':           row['created_at'],
            'updated_at':           row['updated_at']
        }
    }), 201


# ── US-2.5  Edit an Opportunity ──────────────────────────────────────────
@app.route('/api/opportunities/<int:opp_id>', methods=['PUT'])
@login_required
def update_opportunity(opp_id):
    conn = get_db()

    # Verify ownership
    existing = conn.execute(
        'SELECT * FROM opportunities WHERE id = ? AND admin_id = ?',
        (opp_id, session['admin_id'])
    ).fetchone()

    if not existing:
        conn.close()
        return jsonify({'success': False, 'message': 'Opportunity not found.'}), 404

    data = request.get_json(force=True)

    name        = (data.get('name') or '').strip()
    duration    = (data.get('duration') or '').strip()
    start_date  = (data.get('start_date') or '').strip()
    description = (data.get('description') or '').strip()
    skills_raw  = (data.get('skills') or '').strip() if isinstance(data.get('skills'), str) else ','.join(data.get('skills', []))
    category    = (data.get('category') or '').strip()
    future_opp  = (data.get('future_opportunities') or '').strip()
    max_app     = data.get('max_applicants')

    if not all([name, duration, start_date, description, skills_raw, category, future_opp]):
        conn.close()
        return jsonify({'success': False, 'message': 'All required fields must be filled.'}), 400

    max_applicants = None
    if max_app:
        try:
            max_applicants = int(max_app)
        except (ValueError, TypeError):
            pass

    conn.execute(
        '''UPDATE opportunities
           SET name=?, duration=?, start_date=?, description=?, skills=?,
               category=?, future_opportunities=?, max_applicants=?,
               updated_at=datetime('now')
           WHERE id=? AND admin_id=?''',
        (name, duration, start_date, description, skills_raw, category,
         future_opp, max_applicants, opp_id, session['admin_id'])
    )
    conn.commit()

    row = conn.execute('SELECT * FROM opportunities WHERE id = ?', (opp_id,)).fetchone()
    conn.close()

    return jsonify({
        'success': True,
        'message': 'Opportunity updated successfully!',
        'opportunity': {
            'id':                   row['id'],
            'name':                 row['name'],
            'duration':             row['duration'],
            'start_date':           row['start_date'],
            'description':          row['description'],
            'skills':               row['skills'].split(',') if row['skills'] else [],
            'category':             row['category'],
            'future_opportunities': row['future_opportunities'],
            'max_applicants':       row['max_applicants'],
            'created_at':           row['created_at'],
            'updated_at':           row['updated_at']
        }
    })


# ── US-2.6  Delete an Opportunity ────────────────────────────────────────
@app.route('/api/opportunities/<int:opp_id>', methods=['DELETE'])
@login_required
def delete_opportunity(opp_id):
    conn = get_db()

    existing = conn.execute(
        'SELECT id FROM opportunities WHERE id = ? AND admin_id = ?',
        (opp_id, session['admin_id'])
    ).fetchone()

    if not existing:
        conn.close()
        return jsonify({'success': False, 'message': 'Opportunity not found.'}), 404

    conn.execute('DELETE FROM opportunities WHERE id = ? AND admin_id = ?',
                 (opp_id, session['admin_id']))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Opportunity deleted successfully!'})


# ─── Run ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5000)
