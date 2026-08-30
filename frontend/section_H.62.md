# H.62 Official web research notes — 2026-08-29

The following implementation guidance was checked against current official documentation.

## React

`React.lazy` defers loading until the component is rendered and should be declared at module scope. Rejected lazy imports propagate to the nearest Error Boundary. citeturn957766search0

`<Suspense>` is the correct boundary for showing fallback content while a lazy component is loading. citeturn957766search5

## TanStack Query

Queries receive an `AbortSignal`, enabling request cancellation when integrated with `fetch`. citeturn515681search3

Mutations expose `idle`, `pending`, `error`, and `success` lifecycle state, and related queries should generally be invalidated after successful mutations when cached data is now stale. citeturn515681search13turn515681search0

## Tailwind v4

Tailwind's current theme-variable system is based on `@theme`, and those variables participate in generated utilities. citeturn515681search12

Tailwind scans source as text and cannot reliably generate dynamic class fragments produced via string concatenation/interpolation; static class maps or CSS variables are the safe approach. citeturn889556search1

Tailwind's responsive model is mobile-first. citeturn889556search0

## shadcn/ui

shadcn is source distribution rather than an opaque runtime component library, so copied component source should be treated as project-owned and restyled to the AFL system. citeturn423138search2

The current CLI supports adding components, and `components.json` configures how those components and aliases are managed. citeturn423138search0turn423138search6

Current shadcn form guidance uses React Hook Form + Zod + `zodResolver`. citeturn957766search10

Current shadcn documentation has evolved around Toast/Sonner/Base UI, so keep the project's Toast API stable rather than coupling feature code to the registry's internal choice. citeturn957766search1turn957766search4

## React Flow

Current React Flow documentation confirms viewport control (`fitView`, min/max zoom) and the accessibility APIs for keyboard-focusable nodes and edges. citeturn515681search11turn830860search0

Current handle documentation confirms explicit source/target handle positions and handle IDs as the mechanism for controlling edge attachment. citeturn830860search1

## Recharts

Current Recharts documentation exposes accessibility support through `accessibilityLayer`. citeturn515681search15

## Motion

Current Motion documentation recommends `useReducedMotion` / `MotionConfig` to respect device motion preferences and explains that reduced motion can disable/simplify movement rather than merely slow it. citeturn515681search1turn515681search2turn515681search4

## Playwright

Current Playwright supports projects for multiple browsers/devices and a `webServer` configuration to start a development server automatically before tests. citeturn515681search10turn515681search7

## Accessibility standards

WCAG 2.2 adds explicit criteria around focus visibility, focus not being obscured, dragging, and minimum target size. citeturn830860search3turn957766search12

---

