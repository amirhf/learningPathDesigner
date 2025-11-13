# Frontend Quick Start Guide

This guide will help you get the Learning Path Designer frontend up and running in minutes.

## Prerequisites

- Node.js 18+ installed
- Backend services running (see main README)
- npm or yarn package manager

## Quick Setup (5 minutes)

### 1. Navigate to Frontend Directory

```powershell
cd frontend
```

### 2. Install Dependencies

```powershell
npm install
```

This will install all required packages including:
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- shadcn/ui components
- Supabase client
- Zustand for state management

### 3. Configure Environment

Create `.env.local` file:

```powershell
cp .env.local.example .env.local
```

Edit `.env.local` with your settings:

```bash
# Required - Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8080

# Optional - For authentication features
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

**Note:** The app will work without Supabase, but authentication features will be disabled.

### 4. Start Development Server

```powershell
npm run dev
```

The app will start on [http://localhost:3000](http://localhost:3000)

## Verify Installation

1. **Open browser** to http://localhost:3000
2. **Check home page** loads with navigation
3. **Test search** - Navigate to `/search` and try a query
4. **Create plan** - Go to `/plan/new` and fill out the form

## Common Issues

### Port 3000 Already in Use

```powershell
# Use a different port
$env:PORT=3001; npm run dev
```

### Cannot Connect to Backend

Ensure backend gateway is running:

```powershell
curl http://localhost:8080/health
```

Expected response: `{"status":"ok"}`

### Module Not Found Errors

Clear cache and reinstall:

```powershell
rm -rf node_modules
rm package-lock.json
npm install
```

## Project Structure

```
frontend/
├── src/
│   ├── app/              # Pages (Next.js App Router)
│   │   ├── page.tsx     # Home page
│   │   ├── search/      # Search interface
│   │   ├── plan/        # Plan creation & viewing
│   │   ├── quiz/        # Quiz interface
│   │   ├── dashboard/   # User dashboard
│   │   └── auth/        # Authentication
│   ├── components/       # React components
│   │   ├── ui/          # shadcn/ui components
│   │   └── navigation.tsx
│   └── lib/             # Utilities
│       ├── api.ts       # API client
│       ├── supabase.ts  # Auth client
│       └── utils.ts     # Helpers
├── public/              # Static files
└── package.json
```

## Available Pages

| Route | Description |
|-------|-------------|
| `/` | Home page with features overview |
| `/search` | Semantic search for resources |
| `/plan/new` | Create new learning plan |
| `/plan/[id]` | View specific learning plan |
| `/quiz/new` | Take a quiz |
| `/dashboard` | User dashboard |
| `/auth` | Sign in / Sign up |

## Development Workflow

### Making Changes

1. Edit files in `src/` directory
2. Changes auto-reload in browser
3. Check console for errors

### Adding Components

Use shadcn/ui CLI:

```powershell
npx shadcn-ui@latest add [component-name]
```

Example:
```powershell
npx shadcn-ui@latest add dialog
```

### Type Checking

```powershell
npm run type-check
```

### Linting

```powershell
npm run lint
```

## Building for Production

```powershell
# Build
npm run build

# Start production server
npm start
```

## Testing the App

### 1. Test Search

1. Go to http://localhost:3000/search
2. Enter: "Python FastAPI tutorial"
3. Click Search
4. Should see results from backend

### 2. Test Plan Creation

1. Go to http://localhost:3000/plan/new
2. Goal: "Learn React Hooks"
3. Time Budget: 10 hours
4. Click "Generate Learning Plan"
5. Should redirect to plan view

### 3. Test Quiz

1. From a plan page, click "Take Quiz" on a lesson
2. Answer questions
3. Submit quiz
4. See results with explanations

## API Integration

The frontend calls these backend endpoints:

```typescript
// Search
POST /api/search
Body: { query: string, limit: number }

// Create Plan
POST /api/plan
Body: { goal: string, time_budget_hours: number, prerequisites: string[] }

// Get Plan
GET /api/plan/:id

// Generate Quiz
POST /api/quiz/generate
Body: { resource_ids: string[], num_questions: number }

// Submit Quiz
POST /api/quiz/submit
Body: { quiz_id: string, answers: Record<string, number> }
```

See `src/lib/api.ts` for implementation details.

## Customization

### Change Theme Colors

Edit `src/app/globals.css`:

```css
:root {
  --primary: 221.2 83.2% 53.3%;  /* Blue */
  --secondary: 210 40% 96.1%;    /* Light gray */
  /* ... more colors */
}
```

### Modify Navigation

Edit `src/components/navigation.tsx`:

```typescript
const navItems = [
  { href: '/', label: 'Home', icon: BookOpen },
  { href: '/search', label: 'Search', icon: Search },
  // Add more items...
]
```

### Update API URL

Change in `.env.local`:

```bash
NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

## Next Steps

1. **Set up Supabase** (optional)
   - Create project at https://supabase.com
   - Add credentials to `.env.local`
   - Enable authentication features

2. **Customize branding**
   - Update colors in `globals.css`
   - Add logo to `public/`
   - Modify navigation

3. **Add features**
   - User profiles
   - Plan sharing
   - Progress analytics
   - Social features

## Getting Help

- Check browser console for errors
- Review `frontend/README.md` for detailed docs
- Check backend logs if API calls fail
- Ensure all services are running

## Useful Commands

```powershell
# Development
npm run dev              # Start dev server
npm run type-check       # Check TypeScript
npm run lint            # Run linter

# Production
npm run build           # Build for production
npm start               # Start production server

# Maintenance
npm install             # Install dependencies
npm update              # Update packages
rm -rf .next            # Clear build cache
```

## Success Checklist

- [ ] Dependencies installed
- [ ] Environment configured
- [ ] Dev server running on port 3000
- [ ] Home page loads
- [ ] Search works
- [ ] Plan creation works
- [ ] Quiz interface works
- [ ] No console errors

## What's Next?

Once the frontend is running:

1. **Test all features** end-to-end
2. **Seed backend data** for realistic testing
3. **Set up authentication** with Supabase
4. **Customize styling** to match your brand
5. **Deploy to production** (Vercel recommended)

---

**Need help?** Check the main README or frontend/README.md for more details.
