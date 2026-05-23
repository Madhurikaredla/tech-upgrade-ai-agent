# Frontend Engineering Rules

## Project Context
Frontend lives in `apps/ui/src/`. TypeScript + React 18 + Vite + shadcn/ui.

---

## Component File Structure

Every component must follow this exact layout:

```
apps/ui/src/components/FeatureName/ComponentName/
  ComponentName.tsx              # Component JSX — render only
  ComponentName.styles.ts        # Tailwind class strings via cva() or cn()
  ComponentName.module.scss      # CSS/SCSS for non-Tailwind needs (animations, pseudo-selectors, keyframes)
  types.ts                       # Props type, local types
  index.ts                       # Barrel export
```

Rules:
- A "component" in a single `.tsx` file without a folder is a violation.
- `ComponentName.module.scss` is optional — only create it when Tailwind cannot express the style.
- Never mix Tailwind classes and raw CSS for the same property on the same element.

---

## Imports Order (enforced by ESLint)

```ts
// 1. React
import { useState, useCallback } from 'react'

// 2. External libraries
import { useQuery } from '@tanstack/react-query'

// 3. App aliases (@/ paths)
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/store/auth'

// 4. Relative imports
import { ProgramCard } from './ProgramCard'
import { formatDate } from '../utils/date'

// 5. Types (type-only imports)
import type { ProgramConfig } from './types'
```

---

## Hooks Rules

Every custom hook:
- Lives in `apps/ui/src/hooks/` (shared) or `ComponentFolder/use<Name>.ts` (local)
- Name starts with `use`
- Returns a typed object — never a tuple unless it mirrors a React hook signature
- Max 150 lines — extract sub-hooks if longer
- Must have a unit test

---

## Services Layer

```
apps/ui/src/services/<domain>.service.ts
```

- One service per API domain (e.g. `program.service.ts`, `auth.service.ts`)
- All `fetch` / `axios` calls live here — nowhere else
- Returns mapped domain types — never raw API DTOs
- Max 100 lines

---

## React Query Patterns

```ts
// Keys in a constants file
export const QUERY_KEYS = {
  programs: ['programs'] as const,
  program: (id: string) => ['programs', id] as const,
}

// Always use useQuery / useMutation — never useEffect + fetch
const { data, isLoading } = useQuery({
  queryKey: QUERY_KEYS.programs,
  queryFn: () => programService.list(),
})
```

---

## Zustand Store Pattern

```ts
// apps/ui/src/store/<name>.store.ts
type AuthState = {
  user: User | null
  token: string | null   // NOTE: token in memory — never localStorage
  setUser: (user: User) => void
  clear: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  setUser: (user) => set({ user }),
  clear: () => set({ user: null, token: null }),
}))
```

---

## Form Pattern

```ts
// Schema first
const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
})

type LoginFormValues = z.infer<typeof loginSchema>

// Hook
const form = useForm<LoginFormValues>({
  resolver: zodResolver(loginSchema),
})
```

---

## Styling Pattern

### When to use each file

| Need | File |
|---|---|
| Component variants, layout, spacing, color tokens | `ComponentName.styles.ts` (Tailwind via `cva`/`cn`) |
| Animations / `@keyframes` | `ComponentName.module.scss` |
| Complex pseudo-selectors (`:nth-child`, `::before`) | `ComponentName.module.scss` |
| Custom scrollbar, `clip-path`, `mask` | `ComponentName.module.scss` |
| Global base styles, CSS variables, resets | `apps/ui/src/styles/globals.css` |

### `ComponentName.styles.ts` — Tailwind class strings only

```ts
// ComponentName.styles.ts
import { cva } from 'class-variance-authority'
import { cn } from '@/lib/utils'

export const cardStyles = cva(
  'rounded-lg border bg-card text-card-foreground shadow-sm',
  {
    variants: {
      variant: {
        default: 'border-border',
        destructive: 'border-destructive',
      },
    },
    defaultVariants: { variant: 'default' },
  }
)

export const cardHeaderStyles = cn('flex flex-col space-y-1.5 p-6')
```

### `ComponentName.module.scss` — CSS/SCSS only

```scss
// ComponentName.module.scss
// Use only for things Tailwind cannot express.

@keyframes slideIn {
  from { transform: translateY(-8px); opacity: 0; }
  to   { transform: translateY(0);    opacity: 1; }
}

.animatedCard {
  animation: slideIn 200ms ease-out;
}

.scrollArea {
  scrollbar-width: thin;
  scrollbar-color: hsl(var(--border)) transparent;
}
```

### `ComponentName.tsx` — consume both, write neither

```tsx
// ComponentName.tsx
import { cardStyles } from './ComponentName.styles'
import styles from './ComponentName.module.scss'

export function Card({ variant }: CardProps) {
  return (
    <div className={cn(cardStyles({ variant }), styles.animatedCard)}>
      ...
    </div>
  )
}
```

### Hard rules — no exceptions

- Never write a `style={{ }}` attribute anywhere in `.tsx`
- Never write Tailwind classes as string literals inside `.tsx` — they belong in `.styles.ts`
- Never write `<style>` tags in component files
- Never import a global CSS file from a component — only CSS modules
- Every light-mode Tailwind class must have a `dark:` counterpart

---

## Error Boundary Pattern

```tsx
// Required at: app root, route level, async widget level
<ErrorBoundary fallback={<ErrorFallback />}>
  <Suspense fallback={<Spinner />}>
    <AsyncComponent />
  </Suspense>
</ErrorBoundary>
```

---

## Route Constants

```ts
// apps/ui/src/constants/routes.ts
export const ROUTES = {
  HOME: '/',
  PROGRAMS: '/programs',
  PROGRAM: (id: string) => `/programs/${id}`,
  LOGIN: '/login',
} as const
```

Never hardcode `/programs/123` — always use `ROUTES.PROGRAM(id)`.

---

## Toast Pattern

```ts
// Only in hooks — never in components
function useProgramCreate() {
  const { toast } = useToast()
  const mutation = useMutation({
    mutationFn: programService.create,
    onSuccess: () => toast({ title: 'Program created' }),
    onError: (err) => toast({ title: 'Failed', description: mapError(err), variant: 'destructive' }),
  })
  return mutation
}
```

---

## Modularization Rules

Split code when a file exceeds these limits — never leave it monolithic:

| File type | Max lines | Split strategy |
|---|---|---|
| `.tsx` component | 200 | Extract sub-components into their own folders |
| `use<Name>.ts` hook | 150 | Extract sub-hooks (`useNameData`, `useNameActions`) |
| `<domain>.service.ts` | 100 | Split by resource (`program.service.ts` → `program-form.service.ts`) |
| `.styles.ts` | 80 | One styles file per component — never share across components |
| `.module.scss` | 60 | If larger, the component itself is too complex — split the component |

Additional splitting rules:
- A component with more than 3 distinct UI regions (header / body / footer / sidebar …) must be split into sub-components.
- A hook that manages more than one async resource must be split.
- Constants, query keys, and route paths each live in their own dedicated file under `constants/`.
- Types shared across more than one component belong in a `shared/types/` file, not co-located.
- Never barrel-export business logic — only UI components and their types.

---

## Accessibility Checklist

Before marking any interactive component done:
- [ ] All `<button>` elements have `type="button"` or `type="submit"`
- [ ] All form inputs have `<label htmlFor=...>`
- [ ] All images have meaningful `alt` text (or `alt=""` if decorative)
- [ ] Focus ring visible on keyboard navigation (`focus-visible:ring-2`)
- [ ] No `onClick` on `<div>`, `<span>`, or `<li>`
- [ ] ARIA roles where native semantics are insufficient
