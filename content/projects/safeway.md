---
title: "SafeWay"
date: 2026-03-15
summary: "Workplace safety SaaS for industrial B2B — solo-founded, ran in production for 4+ years, currently rewriting in Flutter + Django-Ninja."
tags: ["flask", "react-native", "expo", "offline-first", "saas", "founder"]
weight: 2
cover:
  image: "/images/safeway/cover.jpg"
  alt: "SafeWay landing page screenshot"
  caption: ""
ShowReadingTime: false
ShowToc: false
---

**Live site:** [safeway.app](https://www.safeway.app/)

**Stack (v1):** Python · Flask · SQLAlchemy · PostgreSQL · React Native (Expo) · Redux · redux-offline · Sentry

## What it solves

Industrial workplaces — factories, construction sites, warehouses — file safety incidents on paper. The forms are slow, the data isn't analyzable, and supervisors find out about a hazard hours after a worker spotted it. SafeWay digitizes the issue → event → report flow on mobile, with an offline-first capture path (workers in production halls often have unreliable signal) and a web admin for supervisors and HSE officers.

## Founder context

I founded SafeWay in 2019 and ran it solo for two years — backend, mobile, landing, App Store and Play Store submissions, sales calls, in-field focus groups inside actual industrial sites. The product launched in production in 2021 and has been running ever since with paying customers on free, lite, and pro tiers.

## Architecture (v1)

Backend is a Flask + SQLAlchemy modular app split into `auth`, `companies`, `units`, `issues`, `events`, `reports`, `chat`. Postgres, gunicorn, Sentry from day one, mailgun for transactional email, JWT via Flask-JWT-Extended, Pillow for image processing, alembic for migrations. The mobile app is React Native on Expo SDK 41 with Redux + redux-offline — the offline-first piece is the most important technical decision in the project, because workers cannot retry uploads manually when their signal flakes. Push notifications go through expo-server-sdk; barcode scanning, camera, and geolocation use Expo modules. The landing page is Next.js + Tailwind on Vercel.

## What's next

After 4 years in production, I'm rewriting the mobile app in **Flutter** with a **Django-Ninja** backend — same domain, modernized stack, lessons from running v1 baked in. A detailed writeup is coming when v2 ships.

## What I learned

Three things I'd tell my 2019 self. **One:** offline-first is harder than the redux-offline README implies — optimistic UI with retry-on-reconnect needs a per-action conflict resolution policy, not a one-size-fits-all queue. **Two:** Expo's managed workflow is a fast start but a tight ceiling — every time I needed a native lib, I had to drop to bare workflow, and that toggle is more painful than just starting bare. **Three:** Sentry on day one for both crashes and breadcrumbs is non-negotiable for solo SaaS — when you're debugging an incident at 3am with no on-call, the breadcrumb trail is the only thing standing between you and a full revert.
