// Tiny classnames helper. No `clsx` or `classnames` dependency for this
// project - this is a one-line alternative that handles the only two
// patterns primitives use: joining and conditional inclusion.
export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}