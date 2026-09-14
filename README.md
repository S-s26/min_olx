# Mini-oLx

> A lightweight, peer-to-peer marketplace where neighbours buy and sell
> second-hand goods through real-time chat.

* 🌐 Live: <https://min-olx-1.onrender.com>
* 📄 Spec: see [`product.md`](./product.md)
* 🧭 Context: see [`context.md`](./context.md)
* 🚀 Scaling: see [`SCALING.md`](./SCALING.md)
* 🤝 Contributing: see [`contribute.md`](./contribute.md)

## Stack

* Django 5.1 + Django Channels 4 (ASGI)
* Daphne (HTTP + WebSockets on one port)
* PostgreSQL + Redis (cache + channel layer)
* Cloudinary (media), WhiteNoise (static), Gmail SMTP (transactional mail)

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in values
python manage.py migrate
python manage.py runserver
```

Read [`contribute.md`](./contribute.md) for the full setup.

## License

MIT. See `LICENSE` (coming soon).