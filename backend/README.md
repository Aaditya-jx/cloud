Cloud-Based Campus Secure System - Minimal Core
Backend: FastAPI + SQLite (SQLAlchemy)
Frontend: React (create-react-app style)

How to run backend:
1. cd backend
2. python -m venv venv
3. source venv/bin/activate   (or venv\Scripts\activate on Windows)
4. pip install -r requirements.txt
5. uvicorn main:app --reload --port 8000

API endpoints:
POST /token -> login (username/password) returns JWT with role claim
POST /users/register -> register user (role: student|teacher|admin)
GET /attendance/student/{student_id} -> view attendance (student)
POST /attendance/mark -> teacher marks attendance
GET /marks/student/{student_id} -> view marks
POST /marks/upload -> teacher uploads marks

Note: This is a minimal scaffold for development and demonstration.
