---
title: "Two years founding SafeWay, four years running it: lessons from a solo industrial-safety SaaS"
date: 2026-03-20
tags: ["founder-story", "flask", "react-native", "offline-first", "saas"]
description: "What stuck and what didn't from running a solo industrial-safety SaaS for four years — and why I'm rewriting the mobile app in Flutter now."
ShowToc: true
TocOpen: false
cover:
  image: "/images/safeway/cover.jpg"
  alt: "SafeWay landing"
---

## The pitch

SafeWay is a mobile-first incident-logging and safety-management tool for industrial sites — factories, construction sites, warehouses. The core loop: a worker spots a hazard or a near-miss, opens the app, logs it with photo and location, routes it to a supervisor, and tracks resolution. Safety officers get dashboards; supervisors get task queues; workers get a form that's faster than paper.

Development started in 2019. The product went into production use in 2021. It runs on a free / lite / pro tier model, available on iOS and Android. Four years of real production workloads, real users, real 3am pages.

---

## Why solo, why this domain

Before I started writing code I spent several months watching how safety reporting actually happens on sites. Paper forms. WhatsApp photos with no structured data. Excel trackers maintained by one person who's always either overwhelmed or on vacation. The gap between "we log everything" and "we have actionable data" was enormous, and it was almost entirely a tooling gap, not a process gap.

Field interviews confirmed it. Workers found dedicated apps either too complex to open under a hard hat or so generic they felt irrelevant to their specific job type. The problem was real, the existing options were bad, and the fix was mobile-first, fast to open, and offline-capable.

I went solo not because I'm averse to working with people, but because the validation threshold for this kind of vertical SaaS is low enough for one developer. You need a working prototype that field workers can actually use, and a handful of paying customers before you know whether the domain model is right. Burning runway on a team before clearing that bar is backwards.

---

## Stack choices that aged well

**Flask + SQLAlchemy as modular apps.** The backend is split across eight Blueprint apps: `auth`, `companies`, `units`, `issues`, `events`, `reports`, `chat`, and a top-level `main`. Each app owns its routes, its services, and its database access. Flask's explicit wiring gives you full visibility when you're the only person reading the code — no magic registry, no convention-over-configuration black boxes. SQLAlchemy gave me composable queries that I could actually debug, and Alembic migrations I could read and reason about before running them.

```python
# app/__init__.py — Blueprint registration pattern
from project.auth import auth as auth_blueprint
from project.issues import issues as issues_blueprint
from project.reports import reports as reports_blueprint

app.register_blueprint(auth_blueprint, url_prefix='/api/auth')
app.register_blueprint(issues_blueprint, url_prefix='/api/issues')
app.register_blueprint(reports_blueprint, url_prefix='/api/reports')
```

No ceremony for ceremony's sake. If something broke, I knew exactly which Blueprint to open.

**PostgreSQL.** Zero regrets, ever. Row-level security, transactional DDL, JSON columns for semi-structured inspection metadata, full-text search for the issue log. I have never once wished I had picked something else.

**Offline-first via redux-offline — the decision I'm most proud of.**

Industrial sites have notoriously patchy signal. A warehouse basement has no coverage. A construction crane platform has intermittent 3G. If the app requires connectivity to submit a hazard report, the app fails exactly when safety reporting is most urgent.

`@redux-offline/redux-offline` wraps every side-effecting Redux action in an `effect` / `rollback` / `commit` shape. Actions get queued in AsyncStorage when offline and replayed in order when the network returns. The UI updates optimistically — the worker sees their report "submitted" immediately — and the queue drains silently in the background.

```js
// An issue creation action with optimistic update + offline queue
dispatch({
  type: ISSUE_CREATE_REQUEST,
  payload: { ...issueData, id: localId },
  meta: {
    offline: {
      effect: {
        url: '/api/issues/',
        method: 'POST',
        body: JSON.stringify(issueData),
      },
      commit: { type: ISSUE_CREATE_SUCCESS },
      rollback: { type: ISSUE_CREATE_FAILURE, meta: { localId } },
    },
  },
});
```

Per-action rollback handlers meant conflict resolution was explicit: if the server rejected a create (duplicate, validation error), the UI reverted precisely that item rather than blowing up the whole queue. This pattern took real design work upfront, but it paid back that investment every week in production. Offline-first is not an afterthought you can bolt on later.

---

## Stack choices that didn't

**Expo managed workflow at SDK 41.** The managed workflow is genuinely great until you need to reach outside Expo's native module envelope. SafeWay needed camera access for photo attachments (fine), barcode scanning (fine), and eventually lower-level features that the managed workflow couldn't support without ejecting. I dropped to the bare workflow twice across the product lifetime. Each eject is a migration event that breaks the OTA update pipeline and costs days of stabilisation. If I started today I would begin in bare workflow from day one, or not use Expo at all.

**Redux + Redux-Offline boilerplate.** The offline-first architecture was the right call; the implementation layer accrued real cost. Redux in a React Native app of this scale means: action type constants, action creators, reducers, selectors, middleware wiring, and then the `redux-offline` meta envelope on top of every async action. That's five or six files involved in adding a single new network operation. After two years the store folder was the heaviest directory in the codebase by file count. Today I would reach for Zustand for local state and RTK Query for server state — the redux-offline patterns can be replicated with RTK Query's optimistic update hooks at a fraction of the surface area.

**Flask 1.x on a push-heavy workload.** Flask 1.x predates first-class async support. When push notification volume scaled — batched safety alerts, real-time supervisor pings — the synchronous request model started showing latency under load. I worked around it with gunicorn workers and background threads, but the seams were visible. Flask 2.x async views help, but the SQLAlchemy 1.x session model was not built for concurrent async paths, and untangling that isn't a weekend job.

---

## Operational reality of solo SaaS

Running a SaaS alone for four years means you are simultaneously the engineer, the on-call responder, the support desk, and the sales call. A few things I learned the hard way:

**Sentry on day one, breadcrumbs on.** I added `sentry-sdk` before the first production deploy, and I enabled breadcrumbs. When a user reports "the app froze after I took the photo," a Sentry event with 20 breadcrumbs showing the action sequence leading to the crash is the difference between a 20-minute fix and a 4-hour archaeology session. The mobile side used `sentry-expo`, which captures both JS exceptions and native crashes. For a solo developer, Sentry is not optional infrastructure — it's your only co-worker in the room at 3am.

**Feature flags for risky paths, even with two users.** When I added offline sync I shipped it behind a flag so I could enable it per-account and roll back cleanly if the queue got corrupted. The flag machinery was three lines of config. The time it saved on the first rollback was two days. Principle: anything that touches stored state or user data gets a flag, regardless of current user count.

**Build for being unavailable.** At some point you go on vacation or you get sick. SafeWay has health checks that alert to my phone, a runbook I can follow on hotel wifi, and zero silent failure modes in the critical path. "Silent failure" means the app appears healthy while data is being lost or not delivered. I instrumented every queue flush, every push delivery response, every schema migration step. If something is wrong I want a noisy alert, not a support email three days later.

---

## What's next

Four years of production use teaches you things you cannot learn from first principles. The domain model I shipped in 2021 reflected my understanding of how safety supervisors work. The model I would design today reflects how they *actually* work — which is different in ways that matter for data structure and UX flow.

The rewrite is in progress. **Flutter** for the mobile app: one codebase, proper native performance, a rendering model that doesn't fight you when you need custom UI for offline state indicators. **Django-Ninja** for the backend — the same stack I chose for Art Way, and the choice I'd make again. The offline-first patterns from v1 are being ported, not discarded; the core insight about sync being first-class is still correct.

When v2 ships I'll write the detailed technical post: what the new offline sync layer looks like in Flutter, how the Django-Ninja API design changed from the Flask Blueprints, and what the domain model rethink cost in migration complexity. That post will have the specifics. This one is the retrospective.

If you're early in a solo B2B mobile product: validate offline-first as a hard requirement on day one, add error monitoring before your first user, and accept that the stack choices that feel cautious in year one are the ones you'll thank yourself for in year four.
