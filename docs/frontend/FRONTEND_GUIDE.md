# Frontend Development Guide

This guide covers frontend architecture, components, and design principles.

## Overview

The frontend is a modern React SPA built with Vite and styled with TailwindCSS.

### Technology Stack
- React 18.3.1
- Vite 5.2.11 (build tool and dev server)
- TailwindCSS 3.4.3 (styling)
- Axios 1.7.2 (HTTP client)
- React Markdown 9.0.1 (markdown rendering)
- Lucide React 0.378.0 (icons)

## Project Structure

```
allma-frontend/
├── src/
│   ├── main.jsx              (entry point)
│   ├── App.jsx               (root component)
│   ├── components/           (React components)
│   ├── hooks/                (custom hooks)
│   ├── services/             (API and demo services)
│   ├── assets/               (images, fonts)
│   └── index.css             (global styles)
├── package.json
├── vite.config.js
├── tailwind.config.js
└── vercel.json               (Vercel deployment config)
```

## Development Setup

```bash
cd allma-frontend
npm install
npm run dev
```

Then open http://localhost:5173

## Key Features

### Dark/Light Mode
Automatic detection with manual override. Persisted to localStorage.

### Real-time Streaming
Token-by-token response streaming for better UX perception.

### Document Upload
Drag-and-drop file upload for RAG document ingestion.

### Responsive Design
Mobile-first design working on all device sizes.

### Demo Mode
Auto-fallback to demo mode when backend is unavailable.

See `src/services/demoApi.js` for simulated API responses.

## Component Architecture

### Layout Components
- Header (title, model selector, theme toggle)
- Sidebar (conversation list, new chat button)
- MainContent (chat interface)
- Modal components (settings, documents)

### Chat Components
- MessageList (display messages)
- UserMessage (styled user input)
- AssistantMessage (with markdown rendering)
- InputArea (text input, file upload)

### Utility Components
- MarkdownRenderer (code highlighting)
- RAGToggle (enable/disable RAG)
- ModelSelector (switch between models)

## Styling

TailwindCSS configuration in `tailwind.config.js`:
- Custom color palette
- Extended animations
- Configured spacing scale
- Custom plugins for glassmorphism effects

## API Integration

See [API Reference](../API.md) for endpoint documentation.

API client in `src/services/api.js`:
- Automatic backend availability detection
- Fallback to demo mode if backend unavailable
- Error handling and retry logic

## Deployment

### Vercel Deployment

```bash
cd allma-frontend
npm install
npm run build
npx vercel --prod
```

Configuration in `vercel.json`:
- Build settings for Vite
- Environment variables
- Routes configuration
- SPA fallback for client-side routing

### Docker Deployment

Multi-stage build in `Dockerfile`:
1. Build stage: Node.js build environment
2. Runtime stage: Nginx serving static files

## Environment Variables

Create `.env.local`:

```env
VITE_API_URL=http://localhost:8000
VITE_DEMO_MODE=false
```

## Building

```bash
# Development
npm run dev

# Production build
npm run build

# Preview production build locally
npm run preview

# Linting
npm run lint
```

## Performance Optimization

### Code Splitting
Components loaded lazily using React.lazy()

### Bundle Optimization
- Tree-shaking via Vite
- CSS purging via TailwindCSS
- Image optimization

### Runtime Performance
- Memoization for expensive components
- Debouncing for user input
- Virtual scrolling for long lists

## Accessibility

- Semantic HTML elements
- ARIA labels where needed
- Keyboard navigation support
- Color contrast WCAG AA compliance
- Screen reader friendly

## Testing

See [Contributing Guidelines](../../CONTRIBUTING.md) for test setup.

```bash
npm test
npm test -- --coverage
```

## Troubleshooting

**Build fails**
- Clear node_modules: `rm -rf node_modules && npm install`
- Clear vite cache: `rm -rf .vite`

**Backend connection issues**
- Check `VITE_API_URL` matches backend address
- Verify backend is running on correct port
- Check CORS configuration

**Styling issues**
- Rebuild Tailwind: `npm run build`
- Clear browser cache
- Check tailwind.config.js for purge paths

## Next Steps

- [Design System](DESIGN_SYSTEM.md)
- [Component Reference](COMPONENT_REFERENCE.md)
- [API Documentation](../API.md)
- [Full README](../../README.md)
