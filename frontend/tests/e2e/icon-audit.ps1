#!/usr/bin/env pwsh
# Phase 10 anti-pattern audit: H.68 icon lockdown check.
# Usage: pwsh tests/e2e/icon-audit.ps1
# Exit code 0 = clean. Exit code 1 = one or more violations found.
#
# What this script enforces (added in Phase 5; refined in Phase 8):
#   1. `from "lucide-react"` is only permitted in
#      src/design-system/icons.ts. Any other file importing
#      lucide-react directly is a violation of the H.68 lockdown.
#   2. No raw `size={N}` (where N is a digit) on an icon component
#      anywhere in src/. The only legal size tokens are the
#      IconSize union ("inline" | "node" | "empty" | "pillar").
#   3. No `strokeWidth=` prop on a LUCIDE ICON component outside
#      the locked injection point in icons.ts. Phase 8 added SVG
#      primitives in the custom ProbabilityGauge (and the Recharts
#      <Line> / <ReferenceDot>) that legitimately need strokeWidth
#      to render properly. The audit is scoped to files that
#      import from lucide-react (or from design-system/icons.ts,
#      which re-exports lucide icons): those are the only files
#      where a strokeWidth override would constitute an icon-
#      bypass. Custom SVG primitives in chart components
#      (ProbabilityGauge, PrCurveChart, ShapWaterfall) are
#      NOT flagged.

$src = Join-Path $PSScriptRoot "..\..\src" -Resolve
$icons = Join-Path $src "design-system\icons.ts" -Resolve

$violations = @()

# Check 1: no raw lucide-react imports outside icons.ts
Get-ChildItem $src -Recurse -File -Include *.ts,*.tsx |
  Where-Object { $_.FullName -ne $icons } |
  Select-String -Pattern 'from "lucide-react"' |
  ForEach-Object { $violations += "RAW LUCIDE IMPORT: $($_.Filename):$($_.LineNumber) -> $($_.Line.Trim())" }

# Check 2: no raw pixel sizes on icon components
Get-ChildItem $src -Recurse -File -Include *.ts,*.tsx |
  Select-String -Pattern 'size=\{[0-9]' |
  ForEach-Object { $violations += "RAW PIXEL SIZE: $($_.Filename):$($_.LineNumber) -> $($_.Line.Trim())" }

# Check 3: strokeWidth on icon components - SCOPED to files that
# import from lucide-react / design-system/icons. Custom SVG
# primitives in chart components (ProbabilityGauge, PrCurveChart,
# ShapWaterfall) are NOT flagged.
$iconFiles = @()
Get-ChildItem $src -Recurse -File -Include *.ts,*.tsx |
  Where-Object { $_.FullName -ne $icons } |
  Where-Object {
    (Select-String -Path $_.FullName -Pattern 'from "lucide-react"' -Quiet) -or
    (Select-String -Path $_.FullName -Pattern 'from "[^"]*design-system/icons"' -Quiet)
  } |
  ForEach-Object { $iconFiles += $_.FullName }

foreach ($f in $iconFiles) {
  Get-Content $f | Select-String -Pattern 'strokeWidth=' | ForEach-Object {
    $violations += "STROKE WIDTH OVERRIDE ON ICON: $($_.Filename):$($_.LineNumber) -> $($_.Line.Trim())"
  }
}

if ($violations.Count -eq 0) {
  Write-Host "[H.68 icon audit] CLEAN - no violations." -ForegroundColor Green
  exit 0
} else {
  Write-Host "[H.68 icon audit] $($violations.Count) violation(s) found:" -ForegroundColor Red
  $violations | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
  exit 1
}
