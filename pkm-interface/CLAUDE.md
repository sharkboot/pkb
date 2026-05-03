# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Personal Knowledge Management (PKM) interface built with React + TypeScript + Vite. The application provides a chat-based interface for capturing screenshots and text notes, organizing them into a knowledge base, and retrieving information through a Q&A interface.

**Key Features:**
- Screenshot/image upload via drag-drop or file picker
- Text note capture with categorization
- Chat-style Q&A interface powered by an AI assistant (currently stubbed with mock responses)
- Dark/light mode toggle
- Mobile-responsive sidebar navigation
- Knowledge item organization (starred, recent, categories)

## Commands

```bash
# Install dependencies
pnpm install

# Development server with hot reload
pnpm dev

# Production build
pnpm build

# Production build with explicit mode
pnpm build:prod

# Lint code
pnpm lint

# Preview production build
pnpm preview

# Clean install (removes node_modules, lock file, and prunes store)
pnpm clean
```

## Architecture

### Component Structure

- `src/App.tsx` - Root component managing global state (messages, dark mode, mobile menu)
- `src/components/ChatArea.tsx` - Displays chat messages with copy/feedback actions
- `src/components/InputArea.tsx` - Two-panel input: screenshot upload zone + text recording
- `src/components/Sidebar.tsx` - Navigation with categories (All, Recent, Starred, Trash) and recent items
- `src/components/ErrorBoundary.tsx` - React error boundary wrapper

### State Flow

`App.tsx` holds top-level state and passes callbacks to child components:
- `messages` state flows to `ChatArea` for display
- `handleSend` callback in `InputArea` triggers message creation and mock AI response

### Styling

- **Framework**: Tailwind CSS v3.4 with shadcn/ui conventions
- **UI Primitives**: Radix UI components (accessed via @radix-ui packages)
- **Icons**: Lucide React
- **Aliases configured**: `@/components`, `@/lib`, `@/hooks`, `@/components/ui`

### Path Aliases

```typescript
"@": path.resolve(__dirname, "./src")
```

All imports can use `@/` prefix instead of relative paths.

### Build Configuration

- **Vite** with React plugin for Fast Refresh
- **TypeScript** with separate configs for app (`tsconfig.app.json`) and node (`tsconfig.node.json`)
- **ESLint** with TypeScript-ESLint and React Hooks plugins
- `vite-plugin-source-identifier` enabled in dev mode for debugging (disabled in prod via `BUILD_MODE=prod`)

## Mock Behavior

The AI assistant responses are currently stubbed in `App.tsx:getAssistantResponse()` with random Chinese responses. Replace this with actual API integration for production.

## Tech Stack

| Category | Technology |
|----------|------------|
| Framework | React 18 + TypeScript |
| Build | Vite 6 |
| Styling | Tailwind CSS 3.4 |
| UI Primitives | Radix UI |
| Forms | React Hook Form + Zod |
| Package Manager | pnpm |
| Icons | Lucide React |
