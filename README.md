# Birthday Tracker

A Flask-powered web application that stores people’s names, birthdays, and ages, then sends an email reminder when a birthday is approaching.  
Built with **Flask, HTML, CSS, and JavaScript** as part of my portfolio.

---

## Features
- Add, edit, and delete birthdays
- Email notifications when a birthday is near
- Admin login system
- Modular templates with a clean UI

---

## Project Structure
```
project/
│── static/
│   ├── js/
│   │   └── main.js
│   ├── style/
│   │   └── style.css
│   └── images/
│
│── templates/
│   ├── add.html
│   ├── base.html
│   ├── edit.html
│   ├── index.html
│   ├── login.html
│   └── login_base.html
│
│── app.py
│── birthdays.db     # (ignored in repo)
│── wsgi.py
│── requirements.txt
│── .gitignore
└── .env (ignored in repo)
```

---

## Setup & Installation

1. Clone the repo
   ```bash
   git clone https://github.com/jbellizia/birthday-tracker.git
   cd birthday-tracker
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # Mac/Linux
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file
   ```ini
   MAIL_USERNAME=your_email
   MAIL_PASSWORD=your_password
   SECRET_KEY=your_secret_key
   MY_EMAIL=your_email
   DATABASE_PATH=birthdays.db
   ADMIN_PASSWORD=admin_password
   ```

5. Run the app locally
   ```bash
   python app.py
   ```
   Visit http://localhost:5002 in your browser.

---

## Tech Stack
- Backend: Flask (Python)
- Frontend: HTML, CSS, JavaScript
- Database: SQLite
- Deployment: Nginx + Gunicorn (server), Flask (local)

---

## Author
**James Bellizia**  
- [GitHub Profile](https://github.com/jbellizia)

---

## Notes
- `.env`, `venv/`, and `birthdays.db` are ignored and should not be committed to the repository.
