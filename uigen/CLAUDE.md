# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# First-time setup
npm run setup          # install deps + prisma generate + migrate

# Development
npm run dev            # Next.js dev server with Turbopack at localhost:3000

# Build & production
npm run build
npm run start

# Database
npx prisma generate    # Regenerate client after schema changes
npx prisma migrate dev # Apply schema changes
npm run db:reset       # Drop and recreate the database

# Tests
npm test               # Run all tests
npx vitest run src/lib/__tests__/file-system.test.ts  # Run a single test file

# Lint
npm run lint
```

## Architecture

UIGen is an AI-powered React component generator. Users describe components in a chat interface; Claude generates them using file-system tools; the result is compiled with Babel and rendered live in an iframe.

### Key Data Flow

1. User sends prompt → `POST /api/chat`
2. Route streams a response using Vercel AI SDK (`streamText`) with two tools:
   - `str_replace_editor` — creates/edits files in the virtual FS (`view`, `create`, `str_replace`, `insert`)
   - `file_manager` — renames/deletes files
3. Tool calls update a `VirtualFileSystem` instance (in-memory tree of `FileNode` objects, reconstructed fresh from the serialized `files` payload on each request)
4. On finish, if the user is authenticated, the full state is serialized to `Project.messages` and `Project.data` (JSON columns in SQLite)
5. `FileSystemContext` pushes FS state to `PreviewFrame`, which compiles JSX with Babel standalone (`src/lib/transform/`) and renders it in a sandboxed `<iframe>`

### Preview / Transform Pipeline (`src/lib/transform/jsx-transformer.ts`)

- Each `.js/.jsx/.ts/.tsx` file is compiled with `@babel/standalone` and turned into a **blob URL**
- An **import map** is built mapping every file path (and its `@/`-aliased variant) to its blob URL
- Third-party packages (non-relative, non-`@/` imports) are resolved via `https://esm.sh/<package>`
- Missing local imports get a placeholder stub module so the preview doesn't crash
- Tailwind CSS is loaded via CDN (`https://cdn.tailwindcss.com`) inside the iframe — it is **not** an installed package
- The preview entry point must be `/App.jsx` (default export or `App` named export)
- CSS files are inlined as `<style>` tags; CSS imports are stripped from JS before Babel runs

### System Prompt Conventions (`src/lib/prompts/generation.tsx`)

The AI is instructed to:
- Always start a new project by creating `/App.jsx` as the entry point
- Use Tailwind CSS for all styling (no hardcoded styles)
- Use the `@/` import alias for all local files (e.g., `import Foo from '@/components/Foo'`)
- Never create HTML files

### Provider Selection (`src/lib/provider.ts`)

- `ANTHROPIC_API_KEY` present → real `claude-haiku-4-5` via `@ai-sdk/anthropic`
- Key absent → `MockLanguageModel` (static counter/form/card responses; `maxSteps` reduced to 4)

### Auth (`src/lib/auth.ts`, `src/actions/index.ts`)

JWT sessions stored in an `auth-token` httpOnly cookie (7-day expiry). Passwords hashed with bcrypt (10 rounds). Anonymous users can generate freely; on sign-in, any anonymous work stored in `sessionStorage` (via `src/lib/anon-work-tracker.ts`) is migrated into a new saved project.

### State Management

- `ChatContext` (`src/lib/contexts/chat-context.tsx`) — message history, loading state
- `FileSystemContext` (`src/lib/contexts/file-system-context.tsx`) — virtual FS state shared between editor and preview

### Database

Prisma + SQLite. Schema: `User` (id, email, password) and `Project` (messages JSON, data JSON, optional userId FK). Generated client output is `src/generated/prisma` — run `npx prisma generate` after any schema change.

### Routing

- `/` — anonymous/new session (root `page.tsx` + `main-content.tsx`)
- `/[projectId]` — loads a saved project for authenticated users

### Windows Note

Scripts use `cross-env` to set `NODE_OPTIONS='--require ./node-compat.cjs'` (needed for Prisma on Windows/Turbopack). Do not remove `cross-env` from the scripts.
