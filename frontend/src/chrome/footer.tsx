// Phase 5 - chrome/footer.tsx
// The 3-column footer per "Global Chrome" §3.0:
//   - Left: "Adversarial Fraud Lab · Mastercard Innovation Challenge 2026"
//   - Center: "Built on a 1,064,963-transaction adversarial dataset
//             (0.115% fraud rate, anti-leakage audited)"
//   - Right: Methodology (hash anchor to #numbers-that-hold-up on the
//           Home page) · GitHub · Contact
//
// The "Methodology" link must do an in-page scroll to the Home page's
// "Numbers that hold up" section. If the user is on a non-Home page when
// they click it, navigate to "/#numbers-that-hold-up" first, then
// scrollIntoView. React Router's <Link to="/#numbers-that-hold-up">
// handles the navigation; the scroll-into-view happens in a
// useEffect that watches the location's hash.

import { useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { ROUTES } from "../lib/constants";
import { ExternalLink } from "../design-system/icons";

function scrollToHash(hash: string) {
  const el = document.getElementById(hash);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function MethodologyLink() {
  const location = useLocation();
  return (
    <Link
      to={`${ROUTES.home}#numbers-that-hold-up`}
      onClick={(e) => {
        // If we're already on the Home page, prevent the navigation
        // (which would push a new history entry) and just scroll.
        if (location.pathname === ROUTES.home) {
          e.preventDefault();
          scrollToHash("numbers-that-hold-up");
        }
      }}
      className="text-[0.75rem] text-[var(--text-secondary)] hover:text-[var(--accent-cyan)] transition-colors"
    >
      Methodology
    </Link>
  );
}

function FooterHashEffect() {
  const location = useLocation();
  // After every route change, if the URL has the methodology hash,
  // scroll to it. The setTimeout lets the new page's content mount
  // before scrollIntoView is called (so the element exists in the DOM).
  useEffect(() => {
    if (location.hash === "#numbers-that-hold-up") {
      const t = window.setTimeout(() => scrollToHash("numbers-that-hold-up"), 0);
      return () => window.clearTimeout(t);
    }
    return undefined;
  }, [location.pathname, location.hash]);
  return null;
}

export function Footer() {
  return (
    <footer
      className="bg-[var(--bg-panel)] border-t border-[var(--border-subtle)] mt-16"
      role="contentinfo"
    >
      <FooterHashEffect />
      <div className="max-w-[var(--max-w-home)] mx-auto px-6 py-6 grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
        {/* Left: project + competition name. */}
        <p className="text-[0.75rem] text-[var(--text-muted)]">
          <span className="text-[var(--text-secondary)] font-medium">
            Adversarial Fraud Lab
          </span>
          {" · Mastercard Innovation Challenge 2026"}
        </p>

        {/* Center: dataset provenance - the one-sentence evidence line
            that says "the numbers you'll see elsewhere on this site are
            from this real dataset." */}
        <p className="text-[0.75rem] text-[var(--text-muted)] text-center">
          Built on a{" "}
          <span className="text-[var(--text-secondary)] font-mono">
            1,064,963
          </span>
          -transaction adversarial dataset (0.115% fraud rate,
          anti-leakage audited)
        </p>

        {/* Right: three small links. Methodology is the in-page
            anchor; GitHub and Contact are placeholders for now
            (the spec doesn't require them to be live, only present
            in the 3-column layout). */}
        <nav
          className="flex items-center gap-4 justify-start md:justify-end"
          aria-label="Footer"
        >
          <MethodologyLink />
          <a
            href="#"
            onClick={(e) => e.preventDefault()}
            className="inline-flex items-center gap-1 text-[0.75rem] text-[var(--text-secondary)] hover:text-[var(--accent-cyan)] transition-colors"
            aria-label="GitHub repository (placeholder)"
          >
            GitHub <ExternalLink aria-hidden />
          </a>
          <a
            href="#"
            onClick={(e) => e.preventDefault()}
            className="inline-flex items-center gap-1 text-[0.75rem] text-[var(--text-secondary)] hover:text-[var(--accent-cyan)] transition-colors"
            aria-label="Contact (placeholder)"
          >
            Contact <ExternalLink aria-hidden />
          </a>
        </nav>
      </div>
    </footer>
  );
}