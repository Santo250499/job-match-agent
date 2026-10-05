# Job Match Agent frontend

Local React interface for the Job Match Agent API. It posts résumé text and a job description to `POST /analyse` and shows the structured result.

The API defaults to demo mode, so this screen works without an OpenAI API key. Start the API first (see the repository README), then start this app.

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints, usually `http://127.0.0.1:5173`.

The app calls `http://localhost:8000` unless `VITE_API_URL` is set. To point at another API, copy `.env.example.txt` to `.env` and change the URL:

```env
VITE_API_URL=http://localhost:8000
```

Do not put API keys in frontend environment files. The browser only needs the API address.
