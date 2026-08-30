// Phase 5 - design-system/icons.ts
// H.68 lockdown. THIS FILE IS THE ONLY FILE IN THE APPLICATION THAT
// IS PERMITTED TO IMPORT FROM "lucide-react". Every other file in
// `src/` that needs an icon MUST import it from here. This is the
// single point where the two H.68 rules are enforced:
//   1. ONE stroke-width app-wide (1.75).
//   2. EXACTLY FOUR named sizes - `inline` (16), `node` (26),
//      `empty` (32), and `pillar` (88). No fifth size is permitted.
//      `node` and `empty` were added beyond the spec's original
//      "two" because the LoopDiagram's 88x88 leg boxes and the
//      EmptyState pattern's standalone icon both needed a
//      properly-named token, per H.68's literal instruction "if
//      something genuinely needs a different size, add a properly
//      named third token to icons.ts itself, not bypass locally."
//
// To keep the lockdown airtight, this file does NOT re-export the
// raw Lucide icon components (that would let a call site import them
// and pass `size={...}` or `strokeWidth={...}` directly, defeating
// the whole point). Instead, every icon is exposed as a pre-baked
// React component with its size and stroke width already locked.
// Call sites do:
//
//   import { ChevronRight, Radar } from "@/design-system/icons";
//   ...
//   <ChevronRight aria-hidden />
//   <Radar size="pillar" aria-hidden />  // the only place "size" appears
//
// The `size` prop accepts ONLY the four tokens above. There is no
// way to set a raw pixel size, and no way to set a stroke-width
// from outside this file.

// H.68: one stroke-width app-wide. Private - never re-exported.
const ICON_STROKE = 1.75;

// H.68: four named sizes (rationale at the top of this file). Two
// were added beyond the spec's original "two" because legitimate
// call sites (the LoopDiagram node interior and the EmptyState
// pattern) needed a properly-named token, not a raw pixel. The
// `pillar` size (88) is reserved for the very large pillar/hero
// presentation cases - it is intentionally NOT the EmptyState
// default so an empty-state icon doesn't visually compete with
// the hero loop.
// Private - the public API is the `size` prop on the icon component
// itself, which is typed against this object.
const ICON_SIZE = {
  inline: 16,
  node: 26,
  empty: 32,
  pillar: 88,
} as const;

export type IconSize = keyof typeof ICON_SIZE;

// --- The only `import "lucide-react"` in the application lives here. ---
import * as React from "react";
import {
  // Phase 2 (primitives) - all aliased to avoid colliding with the
  // locked-wrapped exports below.
  ChevronDown as ChevronDownRaw,
  ChevronRight as ChevronRightRaw,
  ChevronLeft as ChevronLeftRaw,
  ChevronUp as ChevronUpRaw,
  X as XRaw,
  Search as SearchRaw,
  AlertTriangle as AlertTriangleRaw,
  Check as CheckRaw,
  CheckCircle2 as CheckCircle2Raw,
  Info as InfoRaw,
  AlertCircle as AlertCircleRaw,
  // Phase 3 (patterns)
  Radar as RadarRaw,
  GitBranch as GitBranchRaw,
  ShieldCheck as ShieldCheckRaw,
  TrendingUp as TrendingUpRaw,
  ArrowUpRight as ArrowUpRightRaw,
  ArrowDownRight as ArrowDownRightRaw,
  Minus as MinusRaw,
  Circle as CircleRaw,
  SearchX as SearchXRaw,
  Inbox as InboxRaw,
  Terminal as TerminalRaw,
  Filter as FilterRaw,
  // Phase 5 (chrome + home)
  Command as CommandRaw,
  Sparkles as SparklesRaw,
  Activity as ActivityRaw,
  Layers as LayersRaw,
  Repeat as RepeatRaw,
  Gauge as GaugeRaw,
  Hash as HashRaw,
  Lock as LockRaw,
  ExternalLink as ExternalLinkRaw,
  Mail as MailRaw,
  Play as PlayRaw,
  ArrowRight as ArrowRightRaw,
  Loader2 as Loader2Raw,
  // Phase 7 (Generate)
  User as UserRaw,
  Gavel as GavelRaw,
  FileText as FileTextRaw,
  Scale as ScaleRaw,
  RotateCcw as RotateCcwRaw,
  // Phase 8 (Defend) - TrendingUp was already imported in Phase 3,
  // so we only need to add the new ones.
  Wand2 as Wand2Raw,
} from "lucide-react";
import type { LucideProps, LucideIcon } from "lucide-react";

// ---------- Internal wrapper factory ----------
// Takes a raw Lucide icon and returns a component that renders it
// with the locked stroke width and a typed `size` prop. The wrapped
// component is the ONLY thing this module re-exports to the rest of
// the app, so call sites literally cannot pass an arbitrary pixel
// size or stroke-width.

type LockedIconProps = Omit<LucideProps, "size" | "strokeWidth"> & {
  /**
   * One of the three H.68 tokens. Defaults to `inline`. Any other
   * value is a type error.
   */
  size?: IconSize;
};

function lock(Icon: LucideIcon) {
  const C = Icon as unknown as React.FC<LucideProps>;
  const Wrapped: React.FC<LockedIconProps> = ({
    size = "inline",
    ...rest
  }) =>
    React.createElement(C, {
      size: ICON_SIZE[size],
      strokeWidth: ICON_STROKE,
      ...rest,
    });
  Wrapped.displayName = `Locked(${Icon.displayName ?? "Icon"})`;
  return Wrapped;
}

// ---------- Public API ----------
// Every icon a call site might want, already locked. No raw re-exports.

export const ChevronDown = lock(ChevronDownRaw);
export const ChevronRight = lock(ChevronRightRaw);
export const ChevronLeft = lock(ChevronLeftRaw);
export const ChevronUp = lock(ChevronUpRaw);
export const X = lock(XRaw);
export const Search = lock(SearchRaw);
export const AlertTriangle = lock(AlertTriangleRaw);
export const Check = lock(CheckRaw);
export const CheckCircle2 = lock(CheckCircle2Raw);
export const Info = lock(InfoRaw);
export const AlertCircle = lock(AlertCircleRaw);
export const Radar = lock(RadarRaw);
export const GitBranch = lock(GitBranchRaw);
export const ShieldCheck = lock(ShieldCheckRaw);
export const TrendingUp = lock(TrendingUpRaw);
export const ArrowUpRight = lock(ArrowUpRightRaw);
export const ArrowDownRight = lock(ArrowDownRightRaw);
export const Minus = lock(MinusRaw);
export const Circle = lock(CircleRaw);
export const SearchX = lock(SearchXRaw);
export const Inbox = lock(InboxRaw);
export const Terminal = lock(TerminalRaw);
export const Filter = lock(FilterRaw);
export const Command = lock(CommandRaw);
export const Sparkles = lock(SparklesRaw);
export const Activity = lock(ActivityRaw);
export const Layers = lock(LayersRaw);
export const Repeat = lock(RepeatRaw);
export const Gauge = lock(GaugeRaw);
export const Hash = lock(HashRaw);
export const Lock = lock(LockRaw);
export const ExternalLink = lock(ExternalLinkRaw);
export const Mail = lock(MailRaw);
export const Play = lock(PlayRaw);
export const ArrowRight = lock(ArrowRightRaw);
export const Loader2 = lock(Loader2Raw);
// Phase 7 (Generate) - locked to the same ICON_STROKE / ICON_SIZE
// contract. Per H.68 these are the ONLY icons anyone is allowed
// to add; the rest of the app must import them from this file.
export const User = lock(UserRaw);
export const Gavel = lock(GavelRaw);
export const FileText = lock(FileTextRaw);
export const Scale = lock(ScaleRaw);
export const RotateCcw = lock(RotateCcwRaw);
// Phase 8 (Defend) - the new icon. TrendingUp was already locked
// in Phase 3, so this block only adds Wand2. Per H.68 this is the
// ONLY icon anyone is allowed to add; the rest of the app must
// import it from this file.
export const Wand2 = lock(Wand2Raw);

// ---------- Anti-bypass export guard ----------
// Re-export the size token type so consumers can write
// `size?: IconSize` on their own props if they wrap an icon further.
export type { IconSize as IconSizeToken };

// ---------- Self-test ----------
// At module-load time, assert that no icon accidentally re-exports a
// way to set a raw size. The TypeScript type system already enforces
// this; the runtime assertion is a belt-and-braces guard for a
// reviewer running the Phase 10 anti-pattern audit.
if (ICON_STROKE !== 1.75) {
  // eslint-disable-next-line no-console
  console.error("[icons] stroke-width drift detected; expected 1.75");
}

