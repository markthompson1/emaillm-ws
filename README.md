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