---
title: "Building Art Way: why I picked django-ninja over DRF in 2026"
date: 2026-04-15
tags: ["django", "python", "api-design", "art-way"]
description: "How I weighed DRF against django-ninja for a small typed-frontend app, what I won, and where it hurt."
ShowToc: true
TocOpen: false
cover:
  image: "/images/art-way/cover.jpg"
  alt: "Art Way booking app"
---

## Context

Art Way is a booking SaaS I built solo for a creative studio — dancers, musicians, and event organizers renting rehearsal rooms by the hour. The domain is narrow: rooms, bookings, users, notifications. Scale is modest — dozens of bookings a week, a single VPS running Django + Celery + Postgres behind nginx. Nothing that needs sharding or a gRPC mesh.

What *did* matter: the frontend is Next.js 15 with React 19 and TypeScript, consuming the API from both client and server components. A typed frontend changes the economics of your API design. Type drift between backend response shapes and frontend interfaces is a constant source of bugs, and in a one-person project there's no code-review safety net to catch it. OpenAPI wasn't optional — I needed a machine-readable contract that the frontend could consume. And boilerplate is the enemy of a solo developer: every file I write to wire up DRF is a file I can't spend on actual features.

Those three constraints — typed frontend, auto-generated OpenAPI, minimal ceremony — drove the framework choice before I wrote a line of code.

## DRF vs django-ninja: what I weighed

DRF is the obvious default. It's been the Django API layer for over a decade, has a huge ecosystem, and drf-spectacular gives you OpenAPI generation that works for almost any project. If you need fine-grained permission classes, nested routers with HyperlinkedModelSerializer, or a community library for almost any integration, DRF has it. That maturity is real.

The cost is ceremony. A typical DRF endpoint for creating a booking requires a `Serializer` class, a `ViewSet` or `APIView`, a `permission_classes` list, registration in a `DefaultRouter`, and usually a second serializer for output if the input shape differs from the model. Validation logic lives in `validate_*` methods that you have to know to look for. The indirection is manageable on a large team where conventions are documented, but on a solo project it's just noise.

django-ninja takes the FastAPI approach: endpoints are plain functions decorated with HTTP-method decorators, request/response shapes are Pydantic `Schema` classes defined via type annotations, auth is a dependency, and OpenAPI is generated automatically from all of that — no separate tool needed. The learning curve is low if you know Python type hints, which in 2026 you do.

For a small, typed-frontend app the tilt is clear. The boilerplate delta alone would have cost me a week of project time. What sealed it was the Pydantic path: schema validation errors surface automatically with structured JSON responses, `EmailStr` and `field_validator` handle the domain rules I care about, and the output schema is the *same* type system the input schema uses. One mental model instead of two.

## What I won

**The register endpoint is representative.** Here's the actual ninja version:

```python
@router.post("/register", response={201: UserSchema, 400: ErrorSchema, 429: ErrorSchema})
def register(request, data: UserRegisterSchema):
    if User.objects.filter(email=data.email).exists():
        return 400, {"detail": "Email already registered"}
    user = User.objects.create_user(
        email=data.email, password=data.password,
        first_name=data.first_name, last_name=data.last_name,
        phone=data.phone, birth_date=data.birth_date,
    )
    return 201, user
```

The `response={201: UserSchema, 400: ErrorSchema}` dict is the OpenAPI spec for that endpoint — django-ninja reads it to generate both the schema and the HTTP status codes. A DRF equivalent would need a `RegisterSerializer`, a `UserSerializer` for output, an `APIView` with `post()`, and manual `Response(serializer.data, status=201)` calls. Rough line-count difference: ~12 lines vs ~45, and the DRF version is harder to follow because the logic is split across classes.

**Pydantic schemas handle complex payloads without special casing.** The booking creation schema carries date, time, and optional recurrence fields, all with native Python types:

```python
class BookingCreateSchema(Schema):
    room_id: int
    date: date
    start_time: time
    end_time: time
    recurrence_type: str | None = None
    recurrence_end_date: date | None = None
```

`date` and `time` come from the stdlib. Pydantic validates and coerces them from JSON strings automatically. No custom field classes, no `to_internal_value` overrides.

**Auth DI is a single line.** `ninja_jwt` wires JWT authentication into the `NinjaAPI` instance globally:

```python
api = NinjaAPI(
    title="Art Way Booking API",
    auth=JWTAuth(),
)
```

Inside any protected endpoint, the authenticated user is `request.auth`. To get the current user's bookings:

```python
@router.get("", response=list[BookingListSchema])
def list_my_bookings(request, status: str | None = None, from_date: date | None = None):
    user = request.auth
    return Booking.objects.filter(user=user, master_booking__isnull=True).order_by("-date")
```

Query parameters (`status`, `from_date`) are declared as function arguments with types — ninja reads them from the URL automatically.

**The frontend gets typed data for free.** Because ninja generates a valid OpenAPI spec at `/api/docs`, I pointed `openapi-typescript` at it and got TypeScript interfaces that mirror the Pydantic schemas exactly. The `User`, `Booking`, and `BookingSeries` interfaces in the frontend `types/index.ts` were seeded from that output and stay in sync when backend schemas change. At the call site it looks like:

```typescript
export const bookingsApi = {
  create: async (data: BookingCreateData): Promise<Booking> => {
    const response = await api.post<Booking>("/bookings", data);
    return response.data;
  },
};
```

`Booking` here is the TypeScript interface generated from `BookingSchema`. The contract is machine-enforced, not documentation.

## What hurt

The ecosystem gap is real. drf-spectacular does more than just generate an OpenAPI schema — it has extension points for custom field resolvers, response envelope wrapping, and integration with third-party DRF packages. django-ninja's OpenAPI output is good but you own edge cases yourself.

Pagination and filtering you build from scratch. DRF's `PageNumberPagination` and `django-filter` integration are battle-tested and handle ordering, search, and page size negotiation out of the box. In Art Way, filtering bookings by status and date is a handful of `if status: queryset = queryset.filter(...)` lines because the feature set is small. At higher complexity — dozens of filterable fields, cursor pagination, public APIs where clients drive the filter syntax — that hand-rolled approach stops being a net win.

The permission model is lightweight by design. Ninja's auth is a boolean gate: authenticated or not. DRF's `permission_classes` composability — `IsAuthenticated & (IsOwner | IsAdminUser)` — is more expressive for APIs with multiple actor roles. I worked around this with explicit checks in handlers (`if not user.is_approved: return 403, ...`), which is fine at this scale but would not compose well across dozens of endpoints.

`django-constance` and the Django admin work fine alongside ninja, but there's no ninja-native equivalent of DRF's browsable API for quick manual testing. The auto-docs at `/api/docs` fill most of that gap.

## When I'd go back to DRF

If the project were a public API serving many third-party integrations, DRF would win. The combination of drf-spectacular for schema generation, third-party packages for OAuth scopes and rate limiting, and the established permission framework reduces the surface area I'd need to own. Same answer for a codebase with existing DRF serializers: the migration cost is rarely worth it unless you're starting from scratch.

For Art Way — single developer, typed Next.js frontend, modest scale, OpenAPI as the integration layer — django-ninja was the right call. It got out of my way and let me ship.
