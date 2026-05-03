# 📘 Qatar Foundation — Admin Portal (CertifyMe Intern Assessment)

🌐 **Live Demo:** [https://certifyme-assignment-47d0.onrender.com](https://certifyme-assignment-47d0.onrender.com)  
**Repository:** [https://github.com/kamranahmad786/CertifyMe_Assignment](https://github.com/kamranahmad786/CertifyMe_Assignment)  
**Original Repo:** [https://github.com/Neerajvs32/Test1](https://github.com/Neerajvs32/Test1)

---

## 🏢 Project Overview

This is the **Qatar Foundation Admin Portal** built as part of the CertifyMe Full Stack Intern Assessment. The repository contained a pre-built Admin UI. I built the **complete Flask backend** to power all the frontend functionality — including authentication, session management, and full CRUD opportunity management with a SQLite database.

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3, Flask |
| **Database** | SQLite |
| **Auth** | Werkzeug password hashing, Flask sessions |
| **WSGI Server** | Gunicorn (production) |
| **Frontend** | Pre-built Admin UI (HTML, CSS, JS) — unchanged |

---

## 📁 Project Structure

```
Test1-main/
├── app.py                 # Flask backend — all API routes
├── requirements.txt       # Python dependencies
├── render.yaml            # Render.com deployment config
├── .gitignore
├── README.md
└── sky/
    ├── admin.html          # Admin UI (unchanged layout)
    ├── admin.css           # Styles (unchanged)
    └── admin.js            # Frontend JS (wired to backend APIs)
```

---

## 🚀 How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/kamranahmad786/CertifyMe_Assignment.git
cd CertifyMe_Assignment
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the server
```bash
python app.py
```

### 4. Open in browser
```
http://localhost:5000
```

---

## 🔌 Backend API Endpoints Built

### Authentication APIs

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/signup` | Register a new admin account |
| `POST` | `/api/login` | Login with email & password |
| `POST` | `/api/logout` | Clear session and logout |
| `POST` | `/api/forgot-password` | Request password reset (token logged internally) |
| `POST` | `/api/verify-reset-token` | Verify if a reset token is valid |
| `GET` | `/api/me` | Check current session / logged-in admin |

### Opportunity Management APIs

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/opportunities` | Fetch all opportunities for the logged-in admin |
| `POST` | `/api/opportunities` | Create a new opportunity |
| `PUT` | `/api/opportunities/<id>` | Update an existing opportunity |
| `DELETE` | `/api/opportunities/<id>` | Delete an opportunity (ownership verified) |

---

## 🗄️ Database Schema (SQLite)

### `admins` table
| Column | Type | Details |
|---|---|---|
| id | INTEGER | Primary Key, Auto Increment |
| full_name | TEXT | NOT NULL |
| email | TEXT | NOT NULL, UNIQUE |
| password | TEXT | Hashed with Werkzeug |
| created_at | TEXT | Auto-generated timestamp |

### `password_resets` table
| Column | Type | Details |
|---|---|---|
| id | INTEGER | Primary Key |
| admin_id | INTEGER | Foreign Key → admins |
| token | TEXT | UUID, UNIQUE |
| expires_at | TEXT | 1 hour from creation |
| used | INTEGER | 0 = unused, 1 = used |

### `opportunities` table
| Column | Type | Details |
|---|---|---|
| id | INTEGER | Primary Key |
| admin_id | INTEGER | Foreign Key → admins |
| name | TEXT | Opportunity name |
| duration | TEXT | e.g., "6 Months" |
| start_date | TEXT | Date string |
| description | TEXT | Full description |
| skills | TEXT | Comma-separated |
| category | TEXT | Technology/Business/Design/Marketing/Data Science/Other |
| future_opportunities | TEXT | Career paths description |
| max_applicants | INTEGER | Optional |
| created_at | TEXT | Auto timestamp |
| updated_at | TEXT | Auto timestamp |

---

## ✅ Completed User Stories

### Task 1 — Authentication (Day 1)

| Story | Title | Status | What Was Built |
|---|---|---|---|
| **US-1.1** | Admin Sign Up | ✅ Done | Full validation (name, email, password ≥8 chars, confirm match), duplicate email check, bcrypt-hashed password storage, redirect to login |
| **US-1.2** | Admin Login | ✅ Done | Email + password auth via `/api/login`, session-based auth, Remember Me extends session to 30 days, generic error message on failure |
| **US-1.3** | Forgot Password | ✅ Done | Same success message always shown (privacy), UUID reset token generated and logged internally, token expires after 1 hour |

### Task 2 — Opportunity Management (Day 2)

| Story | Title | Status | What Was Built |
|---|---|---|---|
| **US-2.1** | View All Opportunities | ✅ Done | `GET /api/opportunities` returns only the logged-in admin's data, empty state message shown when no opportunities exist, all hardcoded cards removed from HTML |
| **US-2.2** | Add New Opportunity | ✅ Done | `POST /api/opportunities` with full validation of all required fields, saved to DB linked to admin, card appears instantly without refresh |
| **US-2.3** | Persist After Login | ✅ Done | Data stored in SQLite, fetched on login via API, admin isolation enforced (can't see other admin's data) |
| **US-2.4** | View Details | ✅ Done | "View Details" button opens modal with all fields: name, duration, start date, description, skills, category, future opportunities, max applicants |
| **US-2.5** | Edit Opportunity | ✅ Done | "Edit" button opens pre-filled form modal, same validations applied, `PUT /api/opportunities/<id>` updates only that record, changes reflected instantly |
| **US-2.6** | Delete Opportunity | ✅ Done | "Delete" button shows `confirm()` dialog, `DELETE /api/opportunities/<id>` removes from DB, ownership verified server-side, card removed from UI instantly |

---

## 🔒 Security Features

- **Password Hashing** — Werkzeug `generate_password_hash` / `check_password_hash` (bcrypt-compatible)
- **Session-Based Auth** — Flask sessions with configurable lifetime
- **Generic Login Errors** — "Invalid email or password" (never reveals which field is wrong)
- **Privacy-Safe Forgot Password** — Same response whether email exists or not
- **Token Expiry** — Password reset tokens expire after 1 hour
- **Ownership Enforcement** — Admin can only view/edit/delete their own opportunities
- **XSS Prevention** — `escapeHtml()` used on all dynamic content rendering

---

## 🌐 Deployment

The app is deployed and live on **Render.com** (free tier).

🔗 **Live URL:** [https://certifyme-assignment-47d0.onrender.com](https://certifyme-assignment-47d0.onrender.com)

**Files added for deployment:**
- `render.yaml` — Render service configuration
- `gunicorn` — Added to `requirements.txt` as production WSGI server

**Deploy steps:**
1. Go to [render.com](https://render.com) → Sign up with GitHub
2. New + → Web Service → Select this repo
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
5. Add env variable: `SECRET_KEY` → Generate
6. Click "Create Web Service"

---

## 👤 Author

**Mohammad Kamran Ahmad**  
📧 mohammadkamranahmad786@gmail.com  
🔗 [GitHub](https://github.com/kamranahmad786)
