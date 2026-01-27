---
name: prototype
description: Quickly scaffold a new prototype or MVP
argument-hint: [app-name] [type]
---

# Prototype Command

Create a new prototype application quickly.

## Usage

```
/prototype my-app       # Default Next.js + Supabase
/prototype my-app api   # API-only (Hono + Drizzle)
/prototype my-app mobile # Expo mobile app
```

## Process

1. **Gather requirements**
   - What problem does this solve?
   - Who is the primary user?
   - What's the core feature?

2. **Scaffold project**
   - Create directory structure
   - Install dependencies
   - Set up database schema
   - Configure auth

3. **Implement core flow**
   - Build main user journey
   - Skip error handling for now
   - Use placeholder data where needed

4. **Deploy**
   - Push to Vercel/Expo
   - Share preview URL

## Templates

### Next.js + Supabase (Default)
- Next.js 15 App Router
- Supabase Auth + Database
- Tailwind + shadcn/ui
- Drizzle ORM

### API Only
- Hono framework
- Drizzle + PostgreSQL
- OpenAPI spec
- Deploy to Cloudflare Workers

### Mobile
- Expo SDK 53
- Expo Router
- NativeWind
- Supabase backend

## Output

Return a working prototype with:
- Deployed URL
- GitHub repo (if requested)
- Key files overview
- Next steps for iteration
