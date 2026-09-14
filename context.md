# Project Context — Mini-oLx

> A quick-start brief for new developers, AI agents, and reviewers
> joining this codebase. It captures **what** the project is, **how**
> it is organised, **why** key decisions were made, and **where**
> the most important code lives.

---

## What is Mini-oLx?

A Django marketplace where users post second-hand goods for sale and
chat with prospective buyers in real time. Originally deployed on
Render.com and now architected to handle ~1,000 concurrent users.

Tagline: *Every item has a second chance.*

---

## Repository layout

```
mini_olx/
├── manage.py
├── requirements.txt        # Python deps (Django, Channels, Redis, …)
├── runtime.txt             # Python version pin for Render
├── Procfile                # process entrypoint
├── start.sh                # daphne startup script
├── render.yaml             # IaC: web service + Postgres + Redis
├── SCALING.md              # deep-dive on the scaling story
├── product.md              # product spec (vision, features, alternatives)
├── context.md              # ← this file
├── contribute.md           # how to contribute / PR guidelines
│
├── mini_olx/               # project package
│   ├── settings.py         # all settings (env-driven via python-decouple)
│   ├── urls.py             # root URL conf
│   ├── asgi.py             # ASGI router: HTTP + WebSocket
│   ├── wsgi.py             # legacy WSGI fallback
│   └── views.py            # home feed view
│
├── accounts/               # auth & users
│   ├── models.py           # customUser(AbstractUser)
│   ├── forms.py            # customUserForm(UserCreationForm)
│   ├── views.py            # signup w/ OTP, login, logout
│   └── urls.py
│
├── product/                # listings
│   ├── models.py           # product, ProductImage (+ indexes)
│   ├── forms.py            # ProductForm, ProductImageFormSet
│   ├── views.py            # add / detail / my-listings / delete
│   └── urls.py
│
├── chat/                   # real-time messaging
│   ├── models.py           # chatroom, message (+ indexes)
│   ├── views.py            # list / detail / history
│   ├── consumers.py        # AsyncJsonWebsocketConsumer (real-time)
│   ├── routing.py          # ws/chat/<id>/ URL → consumer
│   └── urls.py
│
├── static/
│   ├── style.css           # design system
│   └── js/app.js           # tiny global helper (toast, etc.)
│
└── templates/              # server-rendered UI
    ├── base.html
    ├── home.html
    ├── login.html
    ├── signup.html
    ├── add_product.html
    ├── product_detail.html
    ├── my_products.html
    ├── chat_list.html
    ├── chat_details.html
    └── partials/_message_batch.html
```

---

## Domain model at a glance

```
┌────────────┐         ┌──────────────────┐         ┌────────────┐
│ customUser │◄──┐     │     product      │  1 ── N │ ProductImage│
└────────────┘   │     └──────────────────┘         └────────────┘
       ▲         │              │
       │         │              │
       │ seller  │              │
       │         │              ▼
       │         │     ┌──────────────────┐
       │         │     │     chatroom     │
       └─────────┴─────┤  buyer / seller  │
                ▲       └──────────────────┘
                │              │ 1
       buyer    │              ▼ N
                │       ┌──────────────┐
                └──────►│   message    │
                        └──────────────┘
```

* `chatroom` enforces a unique `(buyer, seller, product)` triple so
  there is exactly one conversation per pair per listing.
* `product.cover_image` is a convenience `@property` returning the
  first image — used by every card on the home feed.

---

## Request lifecycle

### HTTP (browser → page)

1. Browser hits `GET /`.
2. `mini_olx/urls.py` → `mini_olx.views.home`.
3. `home` reads from Redis cache (`home_feed:p1`); on miss it
   paginates `product.objects.order_by('-created_at')`.
4. Renders `templates/home.html` with cached product list.
5. WhiteNoise serves `/static/style.css` (compressed).
6. Cloudinary CDN serves product images.

### WebSocket (chat live update)

1. Browser opens `ws://host/ws/chat/<room_id>/`.
2. `mini_olx/asgi.py` matches the pattern in `chat/routing.py`.
3. `AuthMiddlewareStack` populates `scope['user']`.
4. `chat/consumers.py:ChatConsumer.connect` authorises the user
   against the room (buyer or seller only) and joins group
   `chat_<room_id>`.
5. `consumer.receive_json({type:'chat_message', message})` saves the
   message via `database_sync_to_async`, then `group_send` to peers.
6. Peer renders the bubble with optimistic scroll.

---

## Key conventions

* **Env-driven config.**  All secrets & URLs come from environment
  variables via `python-decouple`. Never hardcode.
* **`DEBUG` must be `False` in production.**  `ALLOWED_HOSTS` must
  include your Render domain.
* **Migrations are explicit.**  Run `python manage.py makemigrations`
  after editing any model, then commit the file.
* **Real-time writes happen in the consumer, not the view.**  The
  HTTP `chat_details` view only renders the initial history.
* **Templates live in `/templates`** at the project root, not per-app.
  This is the convention Django picks up from `TEMPLATES['DIRS']`.

---

## Common pitfalls

* **WebSocket refuses to connect** — usually missing
  `AuthMiddlewareStack` in `asgi.py` or missing `channels_redis`.
* **Chat messages vanish when scaling >1 worker** — `REDIS_URL` is
  empty; the consumer is falling back to `InMemoryChannelLayer`.
* **Home feed shows stale data** — you added a `product` through
  `/admin/` and forgot to bust the cache; the cache TTL is 120 s.
* **OTP emails go nowhere in dev** — set `EMAIL_BACKEND` to the
  console backend in `local_settings.py` to print instead of send.
* **CSRF on WebSocket** — WebSockets use cookie auth, no CSRF needed.
  HTTP POSTs do need `X-CSRFToken` (handled by the chat template).

---

## Where to look for what

| I want to change…                      | File(s)                                                              |
| -------------------------------------- | -------------------------------------------------------------------- |
| Branding, colours, fonts               | `static/style.css`                                                   |
| Navbar links / auth UX                 | `templates/base.html`                                                |
| Home feed layout                       | `templates/home.html`                                                |
| Chat layout                            | `templates/chat_details.html`                                        |
| Chat behaviour (typing, presence)      | `chat/consumers.py`, `templates/chat_details.html` script block      |
| Listing form fields                    | `product/forms.py` + `product/models.py`                             |
| Signup/OTP flow                        | `accounts/views.py`, `accounts/forms.py`, `templates/signup.html`    |
| Scaling knobs                          | `mini_olx/settings.py`, `start.sh`, `SCALING.md`                     |
| Production deploy                      | `render.yaml`                                                        |

---

## Glossary

| Term           | Meaning in this codebase                                             |
| -------------- | -------------------------------------------------------------------- |
| **chatroom**   | The model tying a product + buyer + seller together. Has many messages. |
| **consumer**   | An async handler for WebSocket connections (`chat/consumers.py`).    |
| **group**      | A Channels pub/sub topic. We use one per chatroom.                    |
| **OTP**        | 6-digit one-time-password emailed during signup verification.         |
| **WSGI/ASGI**  | Two Python web server interfaces. ASGI also supports WebSockets.      |
| **Cover image**| The first image in a product's `images` relation; shown on cards.    |

---

*For product spec & roadmap see `product.md`. For scaling specifics
see `SCALING.md`. For contribution rules see `contribute.md`.*