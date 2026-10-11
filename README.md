# Until 28 October — Romantic Birthday Website

A responsive romantic book website built with HTML, CSS, JavaScript, Python Flask, and CSV. The PDF download is free; there are no payments, subscriptions, or purchase features.

## Project structure

```text
until_28_october/
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── templates/
│   ├── index.html
│   ├── privacy.html
│   ├── admin_login.html
│   ├── admin.html
│   ├── 404.html
│   └── 500.html
├── static/
│   ├── css/style.css
│   └── js/script.js
├── private_books/
│   └── until_28_october.pdf   # add your actual PDF here
└── data/
    └── download_records.csv  # created automatically
```

The cover is drawn in CSS, so an image file is not required. Background music is intentionally omitted: add it only if you have a properly licensed audio file and implement an explicit user-controlled toggle. Audio is never autoplayed.

## Run on Windows with VS Code

1. Extract the ZIP and open the `until_28_october` folder in VS Code.
2. Install Python 3.10 or newer if needed.
3. Open **Terminal → New Terminal**.
4. Create a virtual environment:

   ```powershell
   python -m venv venv
   ```

5. Activate it in PowerShell:

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, you can avoid changing execution policy and run the environment's Python directly:

   ```powershell
   .\venv\Scripts\python.exe -m pip install -r requirements.txt
   .\venv\Scripts\python.exe app.py
   ```

   Alternatively, in Command Prompt use `venv\Scripts\activate.bat`.

6. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

7. Copy `.env.example` to a new file named `.env`. Replace `FLASK_SECRET_KEY` with a long random secret and `ADMIN_PASSWORD` with a unique password. Never commit `.env` to GitHub. You can generate a secret with:

   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

8. Put your actual e-book PDF at `private_books/until_28_october.pdf`. Create the `private_books` folder if it is not present. Do not put the PDF inside `static`.
9. Start the server:

   ```powershell
   python app.py
   ```

10. Open `http://127.0.0.1:5000` in Chrome. Keep the terminal running while you test.

## Test the website

- Scroll through the homepage, birthday letter, book description, and preview.
- The preview text is explicitly marked as a placeholder. Replace it with a real excerpt from your manuscript before publishing.
- Submit the form using your own test name/email and consent checkbox. If the PDF exists, the browser should download it as `Until_28_October.pdf`.
- If the PDF is missing, the site shows a friendly message.
- Open `data/download_records.csv` in Excel to inspect the records. Excel can import it as UTF-8 if needed.
- Open `http://127.0.0.1:5000/admin/login`, sign in with the `ADMIN_PASSWORD` from `.env`, and use the private CSV retrieval button.
- Test an incorrect admin password and confirm the records URL redirects to login when not authenticated.

The CSV is created automatically on first startup. Each row represents a request the server processed, not proof that a visitor opened or read the file.

## Privacy and security notes

- Download requests are recorded only after the visitor submits the form and checks consent.
- The CSV and PDF are stored outside the public `static` directory. Do not add public routes that serve either file.
- Admin access uses a password from the `.env` environment. The application does not include a hardcoded admin password.
- A basic in-memory rate limit and a honeypot reduce accidental repeats and simple spam; they are not a substitute for production-grade abuse protection.
- The application avoids deliberately logging form fields. The hosting provider may have its own technical logs.
- Update `templates/privacy.html` with a real contact email, data-retention period, and hosting details before publishing.
- Protect the CSV because it contains personal information. Restrict filesystem access and delete records when no longer needed.
- Use HTTPS in production and set `COOKIE_SECURE=1` when served over HTTPS.
- The built-in Flask server is for local development only. For deployment use a production WSGI server supported by your host, configure environment variables in the host dashboard, and set up HTTPS.
- Local CSV storage may be ephemeral on some hosts and does not coordinate safely across multiple application instances. Use persistent storage or a database for a public production site.
- The CSS uses Google Fonts. If you want no third-party font requests, download properly licensed font files and serve them locally.
- Never enable Flask debug mode on a public server.

## Common troubleshooting

- **`python` not found:** reinstall Python and enable “Add Python to PATH”, then reopen VS Code.
- **Activation blocked:** use the direct `venv\Scripts\python.exe` commands above or Command Prompt activation.
- **Missing PDF message:** check the exact filename and location: `private_books/until_28_october.pdf`.
- **Admin access is not configured:** ensure `.env` exists beside `app.py` and contains `ADMIN_PASSWORD=...`; restart Flask after editing it.
- **Port already in use:** stop the other server or set a different `PORT` value in `.env`.
- **Google Fonts do not load:** the site will fall back to system serif/sans-serif fonts when offline.

## Before you publish

1. Add the real PDF.
2. Replace the preview placeholder with real manuscript text.
3. Personalize the letter and check every line.
4. Update the privacy notice and contact details.
5. Configure strong environment secrets and HTTPS.
6. Confirm your hosting platform provides persistent storage for records, or migrate to a database.
