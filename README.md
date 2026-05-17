# ⚡ TaskFlow — Team Task Manager

A full-stack team task management web app with role-based access control, built with Django REST Framework and a single-page vanilla JS frontend.

---

## 🚀 Live Demo

> **Deploy URL:** *(add your Railway URL here after deployment)*

---

## ✨ Features

### Authentication
- JWT-based signup and login
- Persistent sessions via localStorage
- Secure token refresh

### Projects
- Create and manage multiple projects
- Progress tracking (completed / total tasks)
- Member list with avatars

### Team Management
- Invite users to projects by username
- Role-based access: **Admin** vs **Member**
- Owner can promote/demote members or remove them

### Task Management
- Create tasks with title, description, priority, status, assignee, due date
- Kanban board view (To Do / In Progress / In Review / Done)
- List view with sorting
- Overdue badge for past-due tasks
- Inline status updates

### Dashboard
- Stats: total projects, tasks, completed, overdue
- Recent activity feed

### Role-Based Access Control (RBAC)

| Action | Owner | Admin | Member |
|--------|-------|-------|--------|
| Create project | ✅ | — | — |
| Delete project | ✅ | ❌ | ❌ |
| Add/remove members | ✅ | ✅ | ❌ |
| Change member roles | ✅ | ❌ | ❌ |
| Create/edit tasks | ✅ | ✅ | ❌ |
| Delete tasks | ✅ | ✅ | ❌ |
| Update own task status | ✅ | ✅ | ✅ (own tasks only) |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2, Django REST Framework |
| Auth | JWT (djangorestframework-simplejwt) |
| Database | SQLite (Railway-compatible) |
| CORS | django-cors-headers |
| Static files | WhiteNoise |
| Frontend | Vanilla JS + HTML/CSS (served by Django) |
| Deployment | Railway (Gunicorn + Nixpacks) |

---

## 📡 REST API Reference

### Auth
```
POST /api/auth/register/   { username, email, password, first_name, last_name }
POST /api/auth/login/      { username, password }
GET  /api/auth/me/         → current user info
GET  /api/users/           → all users (for member search)
GET  /api/dashboard/       → stats + recent tasks
```

### Projects
```
GET    /api/projects/                          → list user's projects
POST   /api/projects/                          → create project
GET    /api/projects/{id}/                     → project detail
PATCH  /api/projects/{id}/                     → update project
DELETE /api/projects/{id}/                     → delete project (owner only)
GET    /api/projects/{id}/tasks/               → project tasks
POST   /api/projects/{id}/add_member/          → { user_id, role }
DELETE /api/projects/{id}/remove_member/{uid}/ → remove member
PATCH  /api/projects/{id}/update_member/{uid}/ → { role }
```

### Tasks
```
GET    /api/tasks/         → list (filter: ?project=ID&status=X&mine=1)
POST   /api/tasks/         → create task
GET    /api/tasks/{id}/    → task detail
PATCH  /api/tasks/{id}/    → update task (partial)
DELETE /api/tasks/{id}/    → delete task (admin only)
```

---

## 🏠 Local Development

### Prerequisites
- Python 3.11+
- pip

### Setup

```bash
git clone <your-repo-url>
cd taskflow/backend

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

Open **http://localhost:8000** in your browser.

### Create a superuser (optional)

```bash
python manage.py createsuperuser
# Access Django admin at http://localhost:8000/admin/
```

---

## 🚂 Deploy to Railway

### One-click deploy

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
3. Select your repo, choose the `backend/` directory
4. Add environment variables:
   ```
   SECRET_KEY=<generate a random 50-char string>
   DEBUG=False
   ```
5. Railway auto-detects Python, installs deps, runs migrations, and starts Gunicorn
6. Click **Generate Domain** to get your live URL

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key | ✅ Yes |
| `DEBUG` | Set to `False` in production | ✅ Yes |
| `PORT` | Auto-set by Railway | Auto |

---

## 📁 Project Structure

```
taskflow/
└── backend/
    ├── config/
    │   ├── settings.py       # Django settings
    │   ├── urls.py           # Root URL routing
    │   └── wsgi.py
    ├── api/
    │   ├── models.py         # Project, Task, ProjectMember
    │   ├── serializers.py    # DRF serializers
    │   ├── views.py          # All API views + viewsets
    │   ├── urls.py           # API URL routing
    │   └── permissions.py    # RBAC permission classes
    ├── templates/
    │   └── index.html        # Full SPA frontend
    ├── static/               # Static assets
    ├── requirements.txt
    ├── Procfile              # Gunicorn start command
    ├── railway.json          # Railway config
    └── nixpacks.toml         # Build config
```

---

## 🎥 Demo Video Script (suggested)

1. Show signup → login flow (2 users)
2. Create a project as User A (Admin)
3. Add User B as member
4. Create tasks, assign to User B
5. Show Kanban board with tasks in different columns
6. Login as User B → show they can only update status of their own tasks
7. Show dashboard stats
8. Show overdue task badge

---

## 📝 Notes

- **SQLite** is used for simplicity. Railway persists the volume between deploys by default. For production at scale, swap in PostgreSQL via Railway's Postgres plugin and update `DATABASES` in settings.
- Passwords have no complexity requirements (removed validators) for ease of demo — add validators back before going to production.
- JWT tokens expire in 7 days (access) and 30 days (refresh).
