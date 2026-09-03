# AI Appointment Scheduler

An AI-powered appointment scheduling app built with FastAPI, SQLAlchemy, and Ollama.

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy environment variables:
   ```bash
   cp .env.example .env
   ```
3. Ensure Ollama is running locally with the `gemma4` model.
4. Start the app:
   ```bash
   python main.py
   ```
5. Open [http://localhost:8000](http://localhost:8000) in your browser.

## Deploy to Vercel + GitHub

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Prepare app for Vercel deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai_appointment_app.git
git push -u origin main
```

### 2. Set up a PostgreSQL database

Vercel serverless functions do not persist SQLite files. Use a hosted PostgreSQL provider:

- [Neon](https://neon.tech) (free tier available)
- [Supabase](https://supabase.com)
- [Vercel Postgres](https://vercel.com/storage/postgres)

Copy the connection string — it will look like:
```
postgresql://user:password@host/dbname?sslmode=require
```

### 3. Deploy on Vercel

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub.
2. Click **Add New → Project** and import your GitHub repository.
3. Vercel auto-detects the Python project. No build command is needed.
4. Add these **Environment Variables** in the Vercel project settings:

   | Variable | Value |
   |----------|-------|
   | `SECRET_KEY` | A long random string (e.g. from `openssl rand -hex 32`) |
   | `DATABASE_URL` | Your PostgreSQL connection string |
   | `OLLAMA_BASE_URL` | URL of a reachable Ollama server |
   | `OLLAMA_MODEL` | `gemma4` (or your model name) |

5. Click **Deploy**.

Your app will be live at `https://your-project.vercel.app`.

### 4. AI in production

Ollama runs locally by default and is not available on Vercel. For production you need one of:

- A self-hosted Ollama server with a public URL
- A tunnel (e.g. ngrok) pointing to your local Ollama during testing
- Any Ollama-compatible HTTP API at the same `/api/generate` endpoint

Set `OLLAMA_BASE_URL` in Vercel to that URL.

## Docker (optional)

For local full-stack development with PostgreSQL:

```bash
docker-compose up --build
```

## Project Structure

```
├── api/index.py       # Vercel serverless entry point
├── app/               # FastAPI backend (API, auth, scheduler, AI)
├── static/            # Frontend HTML pages
├── main.py            # FastAPI app (local + Vercel)
├── vercel.json        # Vercel routing config
└── requirements.txt   # Python dependencies
```
