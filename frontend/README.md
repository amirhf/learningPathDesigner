# Learning Path Designer - Frontend

Modern Next.js 14 application with TypeScript, Tailwind CSS, and shadcn/ui components.

## Features

- 🎨 **Modern UI** - Beautiful interface built with Tailwind CSS and shadcn/ui
- 🔍 **Semantic Search** - Find learning resources using AI-powered search
- 🎯 **Plan Generation** - Create personalized learning plans with AI
- 📝 **Interactive Quizzes** - Test knowledge with AI-generated questions
- 📊 **Progress Tracking** - Monitor learning progress and achievements
- 🔐 **Authentication** - Supabase-powered user authentication
- 📱 **Responsive** - Works seamlessly on desktop and mobile

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui (Radix UI primitives)
- **Icons**: Lucide React
- **State Management**: Zustand
- **Authentication**: Supabase
- **API Client**: Fetch API

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend services running (see main README)

### Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.local.example .env.local
   ```
   
   Edit `.env.local` and add:
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8080
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

4. **Open browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── auth/              # Authentication page
│   │   ├── dashboard/         # User dashboard
│   │   ├── plan/              # Learning plan pages
│   │   │   ├── new/          # Create new plan
│   │   │   └── [id]/         # View specific plan
│   │   ├── quiz/              # Quiz pages
│   │   │   └── new/          # Take quiz
│   │   ├── search/            # Resource search
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Home page
│   │   └── globals.css        # Global styles
│   ├── components/
│   │   ├── ui/                # shadcn/ui components
│   │   └── navigation.tsx     # Navigation component
│   └── lib/
│       ├── api.ts             # API client
│       ├── supabase.ts        # Supabase client
│       ├── store.ts           # Zustand store
│       └── utils.ts           # Utility functions
├── public/                     # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Pages

### Home (`/`)
Landing page with features overview and call-to-action.

### Search (`/search`)
Semantic search interface for finding learning resources.

### Create Plan (`/plan/new`)
Wizard for creating personalized learning plans:
- Set learning goal
- Define time budget
- Add prerequisites

### View Plan (`/plan/[id]`)
View and track progress on a learning plan:
- See all lessons and resources
- Mark lessons as complete
- Take quizzes for each lesson
- Track overall progress

### Quiz (`/quiz/new`)
Interactive quiz interface:
- AI-generated questions
- Multiple choice format
- Instant feedback
- Detailed explanations with citations

### Dashboard (`/dashboard`)
User dashboard with:
- Learning statistics
- Active plans overview
- Progress tracking
- Quick actions

### Authentication (`/auth`)
Sign in / Sign up page with Supabase integration.

## API Integration

The frontend communicates with the backend gateway at `http://localhost:8080`:

- `POST /api/search` - Search resources
- `POST /api/plan` - Create learning plan
- `GET /api/plan/:id` - Get plan details
- `POST /api/quiz/generate` - Generate quiz
- `POST /api/quiz/submit` - Submit quiz answers

See `src/lib/api.ts` for the complete API client.

## Styling

### Tailwind CSS

Utility-first CSS framework with custom configuration in `tailwind.config.ts`.

### shadcn/ui Components

Pre-built accessible components:
- Button, Card, Input, Label
- Badge, Progress, Toast
- Dialog, Dropdown, Tabs
- And more...

### Theme

Customizable theme with CSS variables in `src/app/globals.css`:
- Light and dark mode support
- Primary, secondary, accent colors
- Consistent spacing and typography

## State Management

Using Zustand for lightweight state management:
- User authentication state
- Current plan state
- Search query state

## Authentication

Supabase authentication with:
- Email/password sign up and sign in
- Password reset (coming soon)
- Protected routes (coming soon)
- User profile management (coming soon)

## Development Tips

### Adding New Components

Use shadcn/ui CLI to add components:
```bash
npx shadcn-ui@latest add [component-name]
```

### Type Safety

All API responses are typed. See `src/lib/api.ts` for type definitions.

### Error Handling

Use the toast system for user feedback:
```typescript
import { useToast } from '@/components/ui/use-toast'

const { toast } = useToast()
toast({
  title: 'Success',
  description: 'Action completed',
})
```

## Building for Production

1. **Build the application**:
   ```bash
   npm run build
   ```

2. **Start production server**:
   ```bash
   npm start
   ```

3. **Deploy**:
   - Vercel (recommended)
   - Netlify
   - Docker
   - Any Node.js hosting

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Backend gateway URL | Yes |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | For auth |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key | For auth |

## Troubleshooting

### Port Already in Use

If port 3000 is in use, specify a different port:
```bash
PORT=3001 npm run dev
```

### API Connection Issues

Ensure the backend gateway is running on port 8080:
```bash
curl http://localhost:8080/health
```

### Build Errors

Clear Next.js cache and rebuild:
```bash
rm -rf .next
npm run build
```

## Contributing

1. Follow the existing code style
2. Use TypeScript for type safety
3. Add proper error handling
4. Test on different screen sizes
5. Update documentation

## License

Part of the Learning Path Designer project.
