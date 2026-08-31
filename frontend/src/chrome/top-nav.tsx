// Phase 5 - chrome/top-nav.tsx
// The sticky 56px top nav. Per the Phase 5 spec and "Global Chrome":
//   - Sticky, 56px tall, --bg-panel, 1px bottom border (--border-subtle).
//   - Wordmark left: "AFL" in --accent-cyan + "Adversarial Fraud Lab" in
//     --text-primary. Both in --font-display at section-title weight.
//   - 5 nav items: Home / Identify / Generate / Defend / Loop.
//     Home is the implicit wordmark link (not duplicated as a 5th item
//     in the spec's prose, but the spec is explicit elsewhere that Home
//     is one of the 5 routes - so the wordmark is the visual "Home"
//     anchor and the 4 explicit-feature items are to its right).
//     Active route gets an underline in --accent-cyan.
//   - Right side: <SystemStatusPill /> + "Run the loop" cyan-outline
//     button (32px tall) that navigates to /loop?prefill=1cycle.
//
// Important: per the spec, "Run the loop" is implemented via a route
// search param (/loop?prefill=1cycle), NOT via the Zustand store. The
// one-time navigation hint lives in the URL, not cross-cutting state.

// Phase 12 (§12.8.1): the active-route indicator is one shared element
// (a small absolutely-positioned underline span) that ANIMATES ITS
// POSITION via framer-motion's layoutId when the active route changes -
// the same object moving between items, ~200ms easeOut. Quick, and
// genuinely the same indicator, not a shared-element showcase effect.
import { NavLink, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ROUTES, type RoutePath } from "../lib/constants";
import { SystemStatusPill } from "./system-status-pill";
import { Button } from "../design-system/primitives";
import { Play, ArrowRight } from "../design-system/icons";
import { MOTION_EASE } from "../design-system/motion";

interface NavItem {
  label: string;
  to: RoutePath;
  end?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Identify", to: ROUTES.identify },
  { label: "Generate", to: ROUTES.generate },
  { label: "Defend", to: ROUTES.defend },
  { label: "Loop", to: ROUTES.loop },
];

const linkBase =
  "relative inline-flex items-center h-14 px-3 text-[0.8125rem] font-medium transition-colors duration-150";
const linkIdle = "text-[var(--text-secondary)] hover:text-[var(--text-primary)]";
const linkActive = "text-[var(--text-primary)]";

export function TopNav() {
  const navigate = useNavigate();

  return (
    <header
      className="sticky top-0 z-40 h-14 bg-[var(--bg-panel)] border-b border-[var(--border-subtle)]"
      role="banner"
    >
      <div className="h-full max-w-[var(--max-w-home)] mx-auto px-6 flex items-center gap-6">
        {/* Wordmark. Doubles as the Home link per the spec ("Home is the
            wordmark link, not duplicated"). */}
        <NavLink
          to={ROUTES.home}
          end
          className="inline-flex items-baseline gap-2 group"
          aria-label="Adversarial Fraud Lab — Home"
        >
          <span
            className="font-mono text-[0.875rem] font-semibold tracking-[0.04em] text-[var(--accent-cyan)]"
            aria-hidden
          >
            AFL
          </span>
          <span className="hidden md:inline font-display text-[0.9375rem] font-bold text-[var(--text-primary)] tracking-[-0.01em]">
            Adversarial Fraud Lab
          </span>
        </NavLink>

        {/* Center-left nav items. NavLink renders the active class via
            a function so the active-underline appears on the matched
            route. Hidden below md because the wordmark + button + 4
            nav links overflow at <768px; the command palette (cmd+k)
            covers the gap on mobile. */}
        <nav className="hidden md:flex items-center" aria-label="Primary">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `${linkBase} ${isActive ? linkActive : linkIdle}`
              }
            >
              {({ isActive }) => (
                <>
                  {item.label}
                  {isActive && (
                    <motion.span
                      layoutId="nav-active-underline"
                      aria-hidden
                      className="absolute bottom-0 left-2 right-2 h-[2px] bg-[var(--accent-cyan)]"
                      transition={{ duration: 0.2, ease: MOTION_EASE }}
                    />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Right side: status pill + Run the loop button. ml-auto pushes
            them to the right edge of the flex row. */}
        <div className="ml-auto flex items-center gap-4">
          <span className="hidden md:inline-flex">
            <SystemStatusPill />
          </span>
          <Button
            variant="secondary"
            size="sm"
            className="h-8 border-[var(--accent-cyan)] text-[var(--accent-cyan)] hover:bg-[var(--bg-elevated)]"
            onClick={() => navigate(`${ROUTES.loop}?prefill=1cycle`)}
            aria-label="Run the loop, pre-filled for 1 cycle"
          >
            <Play aria-hidden />
            <span className="hidden lg:inline">Run the loop</span>
            <span className="hidden lg:inline"><ArrowRight aria-hidden /></span>
          </Button>
        </div>
      </div>
    </header>
  );
}