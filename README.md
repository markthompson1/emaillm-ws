# EmailLM – Windsurf Track

This repository contains the code and documentation for the **Windsurf-based** implementation
of the EmailLM MVP.

```
docs/           Product requirements & diagrams
src/            Windsurf project code
.github/        CI workflow & templates
```

## Getting started

1. Install Windsurf (see https://windsurf.dev).
2. Clone this repo and run `windsurf open` inside `src/`.
3. Copy your `SENDGRID_API_KEY`, `OPENAI_API_KEY`, `STRIPE_SECRET_KEY` into
   GitHub *Settings → Secrets → Actions*.
4. Push a feature branch and open a pull‑request – CI will lint the docs and
   run placeholder tests.

## Local setup

1. Copy `.env.example` to `.env` and fill in your secrets.
2. Place your Google service account JSON at the path you set in `GOOGLE_APPLICATION_CREDENTIALS`.
3. Run `pip install -r requirements.txt` to install dependencies.
4. Run tests with `pytest -q` (pytest will automatically load variables from `.env`).