---
title: "Art Way Booking Service"
date: 2026-04-20
summary: "Studio room booking SaaS for a creative space — Django-Ninja + Next.js 15 + Postgres + Celery."
tags: ["django", "django-ninja", "next.js", "postgresql", "saas"]
weight: 1
cover:
  image: "/images/art-way/cover.jpg"
  alt: "Art Way booking app screenshot"
  caption: ""
ShowReadingTime: false
ShowToc: false
---

**Live site:** [artway.space](https://artway.space/)

**Stack:** Python 3.12 · Django 5.1 · django-ninja · PostgreSQL 16 · Redis · Celery · Next.js 15 · React 19 · TypeScript · Tailwind

## What it solves

Art Way is a creative studio renting rooms for rehearsals, photo sessions, and small events. Before this project, room booking happened over Telegram chats — which produced double-bookings, lost messages, and an admin doing manual conflict resolution every week. The brief was a self-service booking flow with admin moderation, recurring bookings, and instant notifications.

## Architecture

The backend is a single Django project structured as four DDD-inspired apps: `users` (registration with admin moderation), `rooms` (room metadata + image management), `bookings` (single + recurring reservations with state machine), `notifications` (Telegram for admins, email for users). Routes are exposed through django-ninja routers under `/api/`, which gives me typed Pydantic schemas, OpenAPI for free, and far less boilerplate than DRF would.

JWT auth runs through django-ninja-jwt; new users sign up, get a "pending" status, and an admin promotes them to "active" via Django Admin before they can book. Runtime settings (working hours, max-days-ahead, auto-reject delay) live in django-constance, so the venue's manager can change them without a deploy.

The frontend is Next.js 15 (App Router) with React 19, React Query for server state, Zustand for the small bits of client state that don't belong on the server, and Tailwind for styling. The TypeScript API client is auto-generated from the django-ninja OpenAPI spec — when the backend schema changes, the frontend types update on rebuild.

Deployment: backend in Docker Compose on a small VPS (nginx + Postgres + Redis + Django + Celery worker), frontend on Vercel. Single `.env` for backend, `NEXT_PUBLIC_API_URL` for frontend.

## What I learned

The state machine for recurring bookings is the hardest single piece. "Approve all 12 weekly recurrences at once" sounds simple until you handle one date colliding with another booking after the fact — I ended up modeling each recurrence as a child booking pointing back to the parent, with admin actions cascading by default but per-instance override possible. That made the UI honest and the data model debug-friendly.
