# Dashboard 404 Error Fix

**Date:** November 6, 2025  
**Issue:** Clicking "Continue Learning" from dashboard returns 404  
**Status:** ✅ Fixed

---

## Problem

When clicking "Continue Learning" on a plan from the dashboard:
```
Navigate to: /plan/1 or /plan/2
Result: 404 Not Found
```

The plans with IDs '1' and '2' don't exist in the database.

---

## Root Cause

The dashboard was using **hardcoded mock data**:

```typescript
const mockPlans = [
  {
    id: '1',  // ❌ This plan doesn't exist in database
    goal: 'Learn Python FastAPI',
    ...
  },
  {
    id: '2',  // ❌ This plan doesn't exist in database
    goal: 'Master React Hooks',
    ...
  },
]
```

When users clicked "Continue Learning":
```typescript
<Link href={`/plan/${plan.id}`}>  // Links to /plan/1 or /plan/2
  <Button>Continue Learning</Button>
</Link>
```

But these plans were never created, so the API returned 404.

---

## Solution

### Implemented localStorage-based Plan Tracking

Since we don't have user authentication yet (Supabase not configured), I implemented a localStorage-based solution to track created plans.

### 1. Updated Dashboard to Load Real Plans

**File:** `frontend/src/app/dashboard/page.tsx`

**Before:**
```typescript
const mockPlans = [...]
const [plans] = useState(mockPlans)
```

**After:**
```typescript
const [plans, setPlans] = useState<DashboardPlan[]>([])
const [loading, setLoading] = useState(true)

useEffect(() => {
  loadPlans()
}, [])

const loadPlans = () => {
  try {
    const storedPlans = localStorage.getItem('user_plans')
    if (storedPlans) {
      const parsedPlans = JSON.parse(storedPlans)
      setPlans(parsedPlans)
    }
  } catch (error) {
    console.error('Error loading plans:', error)
    toast({
      title: 'Error Loading Plans',
      description: 'Could not load your learning plans',
      variant: 'destructive',
    })
  } finally {
    setLoading(false)
  }
}
```

**Features:**
- ✅ Loads plans from localStorage
- ✅ Shows loading state
- ✅ Error handling with toast
- ✅ Dynamic stats calculation

### 2. Updated Plan Creation to Save to localStorage

**File:** `frontend/src/app/plan/new/page.tsx`

```typescript
const plan = await api.createPlan(goal, timeBudget, hoursPerWeek, prerequisites)

// Save plan to localStorage for dashboard
try {
  const storedPlans = localStorage.getItem('user_plans')
  const plans = storedPlans ? JSON.parse(storedPlans) : []
  plans.push({
    id: plan.id,                    // Real UUID from backend
    goal: plan.goal,
    time_budget_hours: plan.time_budget_hours,
    progress: 0,
    lessons_completed: 0,
    lessons_total: plan.lessons.length,
    created_at: new Date().toISOString(),
  })
  localStorage.setItem('user_plans', JSON.stringify(plans))
} catch (storageError) {
  console.error('Failed to save to localStorage:', storageError)
}

router.push(`/plan/${plan.id}`)  // Navigate with real ID
```

**Features:**
- ✅ Saves plan metadata after creation
- ✅ Uses real UUID from backend
- ✅ Tracks lessons count
- ✅ Error handling (doesn't break plan creation)

### 3. Added Loading State to Dashboard

```typescript
if (loading) {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    </div>
  )
}
```

---

## Files Modified

### Frontend (2 files)
1. **frontend/src/app/dashboard/page.tsx**
   - Removed mock data
   - Added localStorage loading
   - Added loading state
   - Dynamic stats calculation

2. **frontend/src/app/plan/new/page.tsx**
   - Save plan to localStorage after creation
   - Store real plan ID and metadata

---

## Data Flow

### Create Plan
```
1. User fills form at /plan/new
   ↓
2. Submit → api.createPlan()
   ↓
3. Backend creates plan with UUID (e.g., 4c958141-55ad-4151-8a79-784cee5a5176)
   ↓
4. Frontend receives plan with real ID
   ↓
5. Save to localStorage:
   {
     id: "4c958141-55ad-4151-8a79-784cee5a5176",
     goal: "Learn Python",
     time_budget_hours: 10,
     progress: 0,
     lessons_completed: 0,
     lessons_total: 3,
     created_at: "2025-11-06T14:00:00Z"
   }
   ↓
6. Navigate to /plan/4c958141-55ad-4151-8a79-784cee5a5176
```

### View Dashboard
```
1. Navigate to /dashboard
   ↓
2. Load plans from localStorage
   ↓
3. Display real plans with real IDs
   ↓
4. Click "Continue Learning"
   ↓
5. Navigate to /plan/{real-uuid}
   ↓
6. Plan loads successfully ✅
```

---

## localStorage Schema

```typescript
// Key: 'user_plans'
// Value: JSON array
[
  {
    id: "4c958141-55ad-4151-8a79-784cee5a5176",
    goal: "Learn Python basics",
    time_budget_hours: 10,
    progress: 0,
    lessons_completed: 0,
    lessons_total: 3,
    created_at: "2025-11-06T14:00:00.000Z"
  },
  {
    id: "be55fd46-f3d8-4476-8e4e-f6235cfde8d9",
    goal: "Master React Hooks",
    time_budget_hours: 15,
    progress: 0,
    lessons_completed: 0,
    lessons_total: 4,
    created_at: "2025-11-06T15:30:00.000Z"
  }
]
```

---

## Testing

### 1. Create a New Plan ✅
```
1. Go to http://localhost:3000/plan/new
2. Fill form:
   - Goal: "Learn TypeScript"
   - Time Budget: 10 hours
   - Hours Per Week: 5 hours
3. Click "Generate Learning Plan"
4. ✅ Plan created with real UUID
5. ✅ Saved to localStorage
6. ✅ Redirected to plan view
```

### 2. View Dashboard ✅
```
1. Go to http://localhost:3000/dashboard
2. ✅ Shows created plan
3. ✅ Displays correct goal
4. ✅ Shows 0% progress (new plan)
5. ✅ Stats updated correctly
```

### 3. Continue Learning ✅
```
1. On dashboard, click "Continue Learning"
2. ✅ Navigates to /plan/{real-uuid}
3. ✅ Plan loads successfully
4. ✅ Shows all milestones and resources
5. ✅ No 404 error!
```

---

## Limitations & Future Improvements

### Current Limitations

1. **localStorage Only**
   - Plans stored per browser
   - Cleared if browser data is cleared
   - Not synced across devices

2. **No User Authentication**
   - All plans are "anonymous"
   - No user-specific filtering
   - No multi-user support

3. **No Progress Tracking**
   - Progress always shows 0%
   - Lessons completed not updated
   - No persistence of completion state

### Future Improvements

#### Short Term
1. **Add Progress Tracking**
   ```typescript
   // Update localStorage when lesson completed
   const updateProgress = (planId: string, lessonId: string) => {
     const plans = JSON.parse(localStorage.getItem('user_plans') || '[]')
     const plan = plans.find(p => p.id === planId)
     if (plan) {
       plan.lessons_completed++
       plan.progress = (plan.lessons_completed / plan.lessons_total) * 100
       localStorage.setItem('user_plans', JSON.stringify(plans))
     }
   }
   ```

2. **Add Plan Deletion**
   ```typescript
   const deletePlan = (planId: string) => {
     const plans = JSON.parse(localStorage.getItem('user_plans') || '[]')
     const filtered = plans.filter(p => p.id !== planId)
     localStorage.setItem('user_plans', JSON.stringify(filtered))
   }
   ```

#### Medium Term
1. **Implement Supabase Authentication**
   - User login/signup
   - Link plans to user_id in database
   - Server-side plan storage

2. **Add Backend Endpoint for User Plans**
   ```python
   @app.get("/plans/user/{user_id}")
   async def get_user_plans(user_id: str):
       """Get all plans for a user"""
       plans = db_client.get_user_plans(user_id)
       return plans
   ```

3. **Sync localStorage with Backend**
   - On login: fetch plans from server
   - On create: save to both localStorage and server
   - Periodic sync

#### Long Term
1. **Real-time Sync**
   - WebSocket updates
   - Multi-device sync
   - Offline support with sync

2. **Advanced Features**
   - Plan sharing
   - Collaborative learning
   - Progress analytics
   - Recommendations

---

## Migration Path to Supabase

When Supabase is configured:

### 1. Database Schema
```sql
CREATE TABLE user_plans (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    plan_id UUID REFERENCES learning_plans(plan_id),
    progress INTEGER DEFAULT 0,
    lessons_completed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. API Endpoint
```typescript
// GET /api/plans (with auth)
async getUserPlans(): Promise<DashboardPlan[]> {
  const user = await getCurrentUser()
  if (!user) throw new Error('Not authenticated')
  
  return this.request<DashboardPlan[]>('/api/plans', {
    headers: {
      'Authorization': `Bearer ${user.token}`
    }
  })
}
```

### 3. Dashboard Update
```typescript
useEffect(() => {
  const loadPlans = async () => {
    const user = await getCurrentUser()
    if (user) {
      // Load from API
      const plans = await api.getUserPlans()
      setPlans(plans)
    } else {
      // Fallback to localStorage
      const storedPlans = localStorage.getItem('user_plans')
      if (storedPlans) setPlans(JSON.parse(storedPlans))
    }
  }
  loadPlans()
}, [])
```

---

## Success Metrics

| Metric | Before | After |
|--------|--------|-------|
| Dashboard Plans | Mock data (IDs 1, 2) | Real plans ✅ |
| Continue Learning | 404 Error | Works ✅ |
| Plan IDs | Hardcoded | Real UUIDs ✅ |
| Data Persistence | None | localStorage ✅ |
| Stats | Static | Dynamic ✅ |

---

## Notes

### Why localStorage?

1. **No Auth Yet** - Supabase not configured
2. **Simple Solution** - Works immediately
3. **Good UX** - Plans persist across sessions
4. **Easy Migration** - Can upgrade to backend later

### localStorage vs Cookies

- **localStorage:** 5-10MB, survives browser restart
- **Cookies:** 4KB limit, sent with every request
- **Choice:** localStorage is better for this use case

### localStorage vs IndexedDB

- **localStorage:** Simple key-value, synchronous
- **IndexedDB:** Complex queries, asynchronous, larger storage
- **Choice:** localStorage is sufficient for now

---

**Status:** ✅ **FIXED AND TESTED**

**Verification:** Dashboard now shows real plans and "Continue Learning" works correctly.

---

**Last Updated:** November 6, 2025 18:01  
**Tested By:** Manual verification with real plan creation  
**Deployed To:** Development environment (frontend only)
