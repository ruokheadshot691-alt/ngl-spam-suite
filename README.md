---
title: NGL Test Suite
emoji: 📨
colorFrom: gray
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# NGL Test Suite

⚠️ **DISCLAIMER:** Untuk testing & edukasi saja. Spam tanpa izin melanggar
ToS NGL. Space ini publik — siapa pun yang tahu URL bisa pakai.

## Fitur
- Batch sender ke NGL (max 50 job per request)
- Spintax + placeholder
- Device pool rotation
- Retry dengan exponential backoff
- Web UI premium (dark mode, amber accent)

## API
- `GET /api/health` — health check
- `POST /api/send` — kirim batch
- `POST /api/send-one` — kirim 1 pesan
- `GET /api/docs` — Swagger UI