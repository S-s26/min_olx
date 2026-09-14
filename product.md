# Mini-oLx — Product Specification

> A lightweight, peer-to-peer marketplace where neighbours buy and sell
> second-hand goods through real-time chat. Originally deployed on
> Render.com; architected to grow to **1,000+ concurrent users**.

---

## Table of contents

1. [Vision](#vision)
2. [Personas](#personas)
3. [Feature surface](#feature-surface)
4. [Architecture overview](#architecture-overview)
5. [Feature deep-dive (build, why, alternatives)](#feature-deep-dive)
   * [5.1 Accounts & OTP signup](#51-accounts--otp-signup)
   * [5.2 Product listings & media](#52-product-listings--media)
   * [5.3 Real-time chat over WebSockets](#53-real-time-chat-over-websockets)
   * [5.4 Search & browse](#54-search--browse)
   * [5.5 Notification & presence](#55-notification--presence)
6. [Tech stack](#tech-stack)
7. [Scaling to 1,000+ users](#scaling-to-1000-users)
8. [Better solutions / alternatives](#better-solutions--alternatives)
9. [Roadmap](#roadmap)

---

## Vision

Most local marketplaces solve "discovery" but stop at "contact the
seller". Mini-oLx fuses discovery **and** conversation into a single
fast loop: see a product → tap → chat opens with the seller
already online.

Goals:

* **Zero cold-start.**  A buyer can move from a search result to a
  live chat with the seller in under 1 second.
* **Local by default.**  Every listing carries an address; ranking is
  distance-first (room for v2).
* **Privacy first.**  Phone numbers stay masked until both parties
  agree to share them.

---

## Personas

| Persona     | Story                                                                    | Top jobs-to-be-done                                         |
| ----------- | ------------------------------------------------------------------------ | ----------------------------------------------------------- |
| **Mira**    | College student upgrading her phone; needs quick cash.                   | Post a product in <60 s, chat with buyers instantly.        |
| **Aman**    | Renter moving to a new city; needs furniture fast.                       | Search nearby, message multiple sellers at once.            |
| **Riya**    | Hobby seller flipping books on weekends.                                 | Manage inventory, keep track of conversations.              |

---

## Feature surface

### MVP (shipped)

* Email + OTP signup & login (custom user model)
* CRUD for products with up to 5 images
* Per-product chat (buyer ↔ seller)
* Real-time chat over WebSockets (Django Channels)
* Online/offline presence indicators
* Typing indicator
* "My listings" dashboard
* Homepage with paginated feed, category chips, search box

### v2 (planned)

* Geolocation-based ranking
* Saved searches & push notifications
* Stripe-backed "Make offer" + escrow
* Reporting & admin moderation queue
* Mobile app via React Native (re-using the WebSocket API)

---

## Architecture overview

```
                ┌──────────────┐
   Browser ───► │   Daphne     │  ◄── HTTP + WebSocket (single port)
   (HTML/JS)    │ (ASGI worker)│
                └──────┬───────┘
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
       ┌────────┐          ┌─────────────┐
       │ Django │          │  Channels   │ ──► Redis (pub/sub, cache)
       │ views  │          │  consumers  │
       └────┬───┘          └─────────────┘
            ▼
       ┌────────────┐    ┌────────────┐
       │ PostgreSQL │    │ Cloudinary │ (media + CDN)
       └────────────┘    └────────────┘
```

Single binary serves both protocols. One Redis instance powers
real-time fan-out **and** Django cache. Zero separate worker tier for
the MVP.

---

## Feature deep-dive

### 5.1 Accounts & OTP signup

**What it is** — Two-step signup: fill the form → server emails a
6-digit code → user enters code → account created + logged in.

**How to build**

1. `accounts.forms.customUserForm` extends `UserCreationForm` with
   `email`, `phone`, `address`.
2. View `accounts.views.signup` (`templates/signup.html`):
   * Validates the form.
   * Generates `otp = str(random.randint(100000, 999999))`.
   * Stores form data + otp in `request.session`.
   * Calls `django.core.mail.send_mail` via the configured SMTP
     backend.
   * Re-renders the same template in an "otp_sent" branch that hides
     the password fields and shows the OTP input.
3. On OTP submit: re-validates the saved form data, creates the user,
   `login()`s them, clears session, redirects home.

**Why we chose this**

* No third-party OTP SaaS — Gmail SMTP is enough at low volume and
  free.
* Session-backed flow survives refresh (no "you didn't finish
  signup" support tickets).
* The OTP step also serves as a soft email-verification: malformed
  addresses bounce and never produce accounts.

**Alternatives considered**

| Alternative                | Why we didn't pick it                              |
| -------------------------- | -------------------------------------------------- |
| Twilio / Vonage SMS OTP    | Adds a $1 / 100 SMS cost and a vendor dep          |
| Magic-link email           | Slower UX (click email), no keyboard flow          |
| OAuth (Google/Apple)       | Real users in our target demo skip email-only flow |
| Passwordless (WebAuthn)    | Needs second device for most users in v1           |

### 5.2 Product listings & media

**What it is** — Sellers upload a product with title, price, address,
up to 5 images. Buyers see a card-grid home feed with category,
price, distance hint, and age.

**How to build**

* `product.models.product` carries the listing fields.
* `product.models.ProductImage` is a 1-to-many `ImageField` with
  `upload_to='products/'` — Cloudinary picks it up via
  `STORAGES['default']` and stores remotely.
* View `product.views.add_product` uses `modelformset_factory` for
  the images; up to 5 via `max_num=5`.
* Home feed view (`mini_olx.views.home`) paginates by 24, caches
  page-1 in Redis for 120 s.

**Why we chose this**

* Cloudinary gives us global CDN + dynamic transforms (`w_400`) for
  free up to 25 GB.
* A formset is the cleanest Django idiom for "N images at once" —
  no extra JS, full server-side validation, accessible by default.
* Per-page caching is the cheapest win for the home route. Cache is
  invalidated on add/delete.

**Alternatives**

| Alternative                       | Trade-off                                            |
| --------------------------------- | ---------------------------------------------------- |
| Direct-to-S3 with Lambda resizer  | More control, more code, more cost                   |
| Single-image per listing          | Simpler form, but worse for buyers                   |
| Markdown description              | Friendly for power users; risky for spam             |

### 5.3 Real-time chat over WebSockets

**What it is** — A 1-to-1 chat between a buyer and a seller about a
specific product. Both sides see messages appear live. Typing
indicator and online presence are shown.

**How to build**

The full pipeline:

1. **Routing** — `chat/routing.py` exposes
   `ws/chat/<room_id>/`. Only authenticated users reach the consumer;
   `AuthMiddlewareStack` is wired in `mini_olx/asgi.py`.
2. **Consumer** — `chat/consumers.py:ChatConsumer` is an
   `AsyncJsonWebsocketConsumer` that:
   * Authorises the user (`_user_is_participant`) — refuses if the
     user is not the buyer or seller.
   * Joins the `chat_<room_id>` channel group.
   * Saves messages via `database_sync_to_async(_save_message)`.
   * Broadcasts to the group; the other peer renders the bubble.
3. **Wire format** — JSON, two message types: `chat_message` and
   `typing`. Easy to extend with `read` receipts later.
4. **Fallback** — When the WS is not open yet (mobile flaky
   network), the form falls back to a regular HTTP POST so messages
   are never lost.

**Why we chose this**

* **Channels + Daphne** is the simplest ASGI stack for Django — no
  separate Node/Socket.IO server to operate.
* **Redis channel layer** lets us scale to N workers without
  dropping messages between them.
* **Async consumer** keeps long-lived sockets cheap (one task per
  socket, no thread).

**Alternatives**

| Alternative                            | Trade-off                                              |
| -------------------------------------- | ------------------------------------------------------ |
| Server-Sent Events                     | Half duplex; needs reverse proxy tricks for backpressure |
| Socket.IO on a Node sidecar            | Faster dev, doubles the deployable footprint           |
| Firebase Realtime DB / Firestore       | Vendor lock-in, $$$, harder to query history            |
| Polling every 2 s                      | Cheapest infra, but kills the "instant" UX             |

### 5.4 Search & browse

**What it is** — Top-of-page search box filters the homepage feed by
keyword and category.

**How to build**

* `home` view accepts `?q=` and `?page=` query params.
* The template renders a `molx-search` form; submission is plain
  GET — works without JS.
* Indexes in `product/models.py` (`prod_created_idx`,
  `prod_cat_created_idx`) ensure filtered searches stay fast.

**Why we chose this**

* Keyword SQL `ILIKE` is enough for v1 — Postgres trigram indexes
  make it sub-second up to ~10k rows.
* The same `/` URL powers both "all listings" and "search" — one
  cache key, one render path.

**Alternatives**

| Alternative     | When to switch                                          |
| --------------- | ------------------------------------------------------- |
| PostgreSQL GIN trigram | Move to this when row count > 10k                  |
| Meilisearch     | Need typo tolerance + faceted filters                  |
| Typesense       | Need multi-language + synonyms                         |
| Algolia         | Need SaaS-grade relevance + analytics                  |

### 5.5 Notification & presence

* **Presence** — The consumer publishes a `presence_event` whenever a
  peer connects/disconnects. The UI shows a green dot in the chat
  header.
* **Typing** — A debounced 1.2 s "is_typing" ping.
* **Unread badge** (planned) — Use the `updated_at` on the chatroom +
  a per-user `last_read_at` column. Trivial to add in v2.

---

## Tech stack

| Layer                | Choice                                   | Reason                                              |
| -------------------- | ---------------------------------------- | --------------------------------------------------- |
| Language             | Python 3.13                              | First-class Django support                          |
| Framework            | Django 5.1                               | Batteries-included, mature                          |
| Real-time            | Django Channels 4 + daphne 4              | One ASGI server, native WSGI fallback               |
| Database             | PostgreSQL (via `dj-database-url`)        | Free 1 GB on Render; relational fits our data      |
| Cache / channel layer| Redis 7 (managed on Render)              | Pub/sub + cache in one instance                     |
| Object storage / CDN | Cloudinary                               | Free tier, on-the-fly image transforms              |
| Static files         | WhiteNoise + manifest compression        | Zero-CDN CSS/JS, no extra infra                     |
| Mail                 | Gmail SMTP                               | Free up to ~500 emails/day                          |
| Hosting              | Render.com Blueprint (`render.yaml`)     | Single-file infra-as-code                           |

---

## Scaling to 1,000+ users

See `SCALING.md` for the full plan. TL;DR:

* Daphne + 3 workers ≈ 5,400 HTTP rps, 12k open sockets per process.
* Redis-backed channel layer keeps cross-worker fan-out at O(1).
* Composite indexes on every hot query path.
* Page-1 home feed cached 120 s — DB sees one feed query / 2 min.

---

## Better solutions / alternatives

If you have a bigger team / budget, the better path is:

1. **Frontend framework.**  Use Next.js or Astro for SSR + partial
   hydration. Server-side rendering the chat *shell* lets us drop
   TTFB and ship less JS. Why we didn't: Django templates + small
   static JS keeps the deployable to a single Python process.
2. **Managed real-time.**  Pusher / Ably / Supabase Realtime give you
   SLA'd WebSockets without operating Redis. Why we didn't: cost
   per connection adds up at 1k users; Redis is ~$0 on Render.
3. **Elasticsearch / OpenSearch** for search once catalogue > 100k.
4. **S3 + Lambda** for image transforms at scale; Cloudinary's free
   tier runs out around 25 GB.
5. **Multi-tenant product model** if launching more marketplaces
   than one. Use `django-tenants` + Postgres schemas.

---

## Roadmap

| Quarter | Theme                           | Features                                              |
| ------- | ------------------------------- | ----------------------------------------------------- |
| Q1 2026 | Polish (this release)           | New UI, WebSockets, scaling infra                     |
| Q2 2026 | Discovery                       | Geo ranking, push notifications, saved searches       |
| Q3 2026 | Trust & safety                  | Reporting, moderation, phone-mask-by-default          |
| Q4 2026 | Commerce                        | Stripe escrow, in-app offers, shipping integration    |

---

*Last updated: July 2026. Authored with ❤️ by the Mini-oLx team.*