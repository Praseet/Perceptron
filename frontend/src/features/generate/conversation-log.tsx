// Phase 7 - features/generate/conversation-log.tsx
// Renders the fraudster/judge transcript returned by /api/generate.
// The transcript is already keyed by role in the API response
// ({ role: "fraudster" | "judge", content: string }).
//
// This is intentionally a thin component. The transcript is
// narrative content - the page does not need to act on it, only
// show it. Each turn gets a left border in the loop leg color so
// the page reads as a single visual document.

import { User, Gavel } from "../../design-system/icons";
import { LOOP_LEGS } from "../../lib/constants";

interface Turn {
  role: string;
  content: string;
}

interface ConversationLogProps {
  conversation: Turn[];
}

export function ConversationLog({ conversation }: ConversationLogProps) {
  if (conversation.length === 0) {
    return (
      <p className="text-[0.75rem] text-[var(--text-muted)] italic">
        No conversation turns.
      </p>
    );
  }
  return (
    <ol className="space-y-3">
      {conversation.map((t, i) => {
        const isFraudster = t.role === "fraudster";
        const accent = isFraudster
          ? LOOP_LEGS.generate.tokenVar
          : LOOP_LEGS.defend.tokenVar;
        const Icon = isFraudster ? User : Gavel;
        const label = isFraudster ? "Fraudster" : "Judge";
        return (
          <li
            key={i}
            className="pl-3 py-2 border-l-2"
            style={{ borderColor: accent }}
          >
            <div className="flex items-center gap-1.5 mb-1">
              <Icon aria-hidden size="inline" style={{ color: accent }} />
              <span
                className="text-[0.6875rem] font-mono uppercase tracking-[0.12em]"
                style={{ color: accent }}
              >
                {label}
              </span>
            </div>
            <p className="text-[0.8125rem] text-[var(--text-primary)] leading-relaxed">
              {t.content}
            </p>
          </li>
        );
      })}
    </ol>
  );
}
