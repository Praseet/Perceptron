// Phase 5 - chrome/command-palette.tsx
// Cmd/Ctrl+K command palette. Per the spec, the palette has three
// groups, all fed by TanStack Query so the result list is searchable
// and the underlying data is the same as the rest of the app:
//
//   1. "Pages" - the 5 routes.
//   2. "Attacks" - fuzzy search over the 25 attacks from getAttacks().
//   3. "Actions" - "Run the loop" -> /loop?prefill=1cycle,
//                   "Generate a random attack" -> /generate?attack_id=<random>,
//                   "Predict a random transaction" -> /defend?random=1.

import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Command } from "cmdk";
import { useQuery } from "@tanstack/react-query";
import { getApiClient } from "../lib/api/client";
import { useAppStore } from "../lib/store";
import { ROUTES, ATTACKS_QUERY_KEY } from "../lib/constants";
import { Dialog } from "../design-system/primitives";
import { Command as CommandIcon } from "../design-system/icons";

interface PaletteItem {
  id: string;
  label: string;
  hint?: string;
  onSelect: () => void;
  group: "Pages" | "Attacks" | "Actions";
}

export function CommandPalette() {
  const open = useAppStore((s) => s.commandPaletteOpen);
  const setOpen = useAppStore((s) => s.setCommandPaletteOpen);
  const navigate = useNavigate();
  const [value, setValue] = useState("");

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        const tag = (e.target as HTMLElement | null)?.tagName?.toLowerCase();
        if (tag === "input" || tag === "textarea") return;
        e.preventDefault();
        setOpen(!useAppStore.getState().commandPaletteOpen);
      } else if (e.key === "Escape" && useAppStore.getState().commandPaletteOpen) {
        setOpen(false);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [setOpen]);

  useEffect(() => {
    if (!open) setValue("");
  }, [open]);

  const attacks = useQuery({
    queryKey: [...ATTACKS_QUERY_KEY],
    queryFn: () => getApiClient().getAttacks(),
    staleTime: 30_000,
  });

  const items: PaletteItem[] = useMemo(() => {
    const pages: PaletteItem[] = [
      { id: "page-home", group: "Pages", label: "Home", hint: "/",
        onSelect: () => { setOpen(false); navigate(ROUTES.home); } },
      { id: "page-identify", group: "Pages", label: "Identify", hint: "/identify",
        onSelect: () => { setOpen(false); navigate(ROUTES.identify); } },
      { id: "page-generate", group: "Pages", label: "Generate", hint: "/generate",
        onSelect: () => { setOpen(false); navigate(ROUTES.generate); } },
      { id: "page-defend", group: "Pages", label: "Defend", hint: "/defend",
        onSelect: () => { setOpen(false); navigate(ROUTES.defend); } },
      { id: "page-loop", group: "Pages", label: "Loop", hint: "/loop",
        onSelect: () => { setOpen(false); navigate(ROUTES.loop); } },
    ];

    const attackItems: PaletteItem[] = (attacks.data ?? []).map((a) => ({
      id: `attack-${a.id}`,
      group: "Attacks" as const,
      label: a.name,
      hint: `${a.id} - category ${a.category}`,
      onSelect: () => {
        setOpen(false);
        navigate(`${ROUTES.identify}?attack_id=${encodeURIComponent(a.id)}`);
      },
    }));

    const actions: PaletteItem[] = [
      { id: "action-run-loop", group: "Actions", label: "Run the loop",
        hint: "pre-filled for 1 cycle",
        onSelect: () => { setOpen(false); navigate(`${ROUTES.loop}?prefill=1cycle`); } },
      { id: "action-generate-random", group: "Actions", label: "Generate a random attack",
        hint: "picks a random implemented attack",
        onSelect: () => {
          setOpen(false);
          const implemented = (attacks.data ?? []).filter((a) => a.status === "implemented");
          const list = implemented.length > 0 ? implemented : (attacks.data ?? []);
          const pick = list[Math.floor(Math.random() * list.length)];
          if (pick) {
            navigate(`${ROUTES.generate}?attack_id=${encodeURIComponent(pick.id)}`);
          } else {
            navigate(ROUTES.generate);
          }
        } },
      { id: "action-predict-random", group: "Actions", label: "Predict a random transaction",
        hint: "navigate to Defend with ?random=1",
        onSelect: () => { setOpen(false); navigate(`${ROUTES.defend}?random=1`); } },
    ];

    return [...pages, ...attackItems, ...actions];
  }, [attacks.data, navigate, setOpen]);

  return (
    <Dialog
      open={open}
      onClose={() => setOpen(false)}
      title={
        <span className="inline-flex items-center gap-2">
          <CommandIcon aria-hidden />
          <span>Command palette</span>
        </span>
      }
    >
      <Command label="Command palette" shouldFilter className="w-[480px]">
        <Command.Input
          value={value}
          onValueChange={setValue}
          placeholder="Type a page, attack, or action..."
          className="w-full h-10 px-3 bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded-[var(--radius-input)] text-[0.875rem] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-cyan)]"
          aria-label="Search command palette"
        />
        <Command.List className="max-h-[60vh] overflow-y-auto mt-2">
          <Command.Empty className="py-6 text-center text-[0.8125rem] text-[var(--text-muted)]">
            No results.
          </Command.Empty>
          {(["Pages", "Attacks", "Actions"] as const).map((g) => {
            const groupItems = items.filter((i) => i.group === g);
            if (groupItems.length === 0) return null;
            return (
              <Command.Group
                key={g}
                heading={g}
                className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1 [&_[cmdk-group-heading]]:text-[0.6875rem] [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider [&_[cmdk-group-heading]]:text-[var(--text-muted)] [&_[cmdk-group-heading]]:font-semibold"
              >
                {groupItems.map((it) => (
                  <Command.Item
                    key={it.id}
                    value={`${it.label} ${it.hint ?? ""}`}
                    onSelect={() => it.onSelect()}
                    className="flex items-center justify-between gap-2 px-2 py-1.5 rounded-[var(--radius-input)] text-[0.8125rem] text-[var(--text-primary)] cursor-pointer data-[selected=true]:bg-[var(--bg-elevated)] data-[selected=true]:text-[var(--accent-cyan)]"
                  >
                    <span className="truncate">{it.label}</span>
                    {it.hint && (
                      <span className="text-[0.6875rem] text-[var(--text-muted)] font-mono shrink-0">
                        {it.hint}
                      </span>
                    )}
                  </Command.Item>
                ))}
              </Command.Group>
            );
          })}
        </Command.List>
      </Command>
    </Dialog>
  );
}
