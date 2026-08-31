# Vision Kled

**Founder:** Moetez Khaled  
Nanterre, France · [LinkedIn](https://www.linkedin.com/in/moetaz-khaled) · [GitHub](https://github.com/MoetazKled)

Vision Kled is a sales and digital-presence platform. You add a contact, talk with them from the admin console, generate a personal demo website, and convert them into a subscriber.

The first release runs fully on your machine: FastAPI, a React admin, SQLite, and optional OpenAI / Gemini / Anthropic keys.

## Products

| Product | Who it is for |
| --- | --- |
| Vision Portfolio | Job seekers and freelancers |
| Vision Presence | Local businesses and independent professionals |
| Vision Bac | Tunisian Baccalaureate students |

## Run locally

```bash
chmod +x start.sh
./start.sh
```

- Admin: http://localhost:5173
- API docs: http://127.0.0.1:8003/docs

Copy `.env.example` to `.env`. A language-model key is optional for the first tests.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Stack

Python, FastAPI, React, SQLite, Docker. Cloud deployment (Cloud Run / a small VPS) comes after the local loop is proven.

## License

MIT © 2026 Moetez Khaled
