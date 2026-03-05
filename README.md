# Python Tools

A lightweight web app with server-side Python utilities — upload a file, process it, download the result.

Built with Flask. Deployable on Render.

---

## Tools

| Tool | Status |
|---|---|
| PDF Text Extractor | ✅ Ready |
| File to PDF Converter | 🔜 Coming soon |

---

---

### Run locally

```bash
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

---

### Deploy to Render (free)

1. Push this folder to a GitHub repository
2. Go to https://render.com → New → Web Service
3. Connect your GitHub repo
4. Set:
   - Environment: Python 3
   - Build command: pip install -r requirements.txt
   - Start command: gunicorn app:app
5. Deploy → your app goes live at a .onrender.com URL
6. To go offline: Dashboard → Suspend Service
7. To go back online: Dashboard → Resume Service

---

### Project structure

python-tools/
├── app.py               # Flask backend + PDF extraction logic
├── requirements.txt     # Python dependencies
├── Procfile             # For Render deployment
└── templates/
    ├── base.html        # Shared layout (header, nav, styles)
    ├── index.html       # Home page with tools grid
    ├── extractor.html   # PDF extractor tool page
    ├── whatisit.html    # About page
    └── contact.html     # Contact page

---

### Adding a new tool

1. Add a route in app.py
2. Create a template in templates/
3. Make the card clickable in index.html
