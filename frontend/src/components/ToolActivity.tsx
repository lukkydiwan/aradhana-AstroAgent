import { useState } from "react";
import type { ToolEvent } from "../types";
import { Telescope, ChevronDown, ChevronUp, CheckCircle, Loader } from "lucide-react";

const TOOL_LABELS: Record<string, string> = {
  geocode_place: "Locating birth city",
  compute_birth_chart: "Computing natal chart",
  get_daily_transits: "Fetching today's transits",
  knowledge_lookup: "Consulting astrology reference",
};

interface Props {
  events: ToolEvent[];
}

export default function ToolActivity({ events }: Props) {
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});

  if (events.length === 0) return null;

  return (
    <div className="mt-2 space-y-1.5">
      {events.map((evt, i) => (
        <div
          key={i}
          className="rounded-xl border border-cosmos-700 bg-cosmos-900/70 overflow-hidden text-xs"
        >
          <button
            onClick={() => setExpanded((p) => ({ ...p, [i]: !p[i] }))}
            className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-cosmos-800/50 transition"
          >
            {evt.status === "running" ? (
              <Loader className="w-3 h-3 text-violet-light animate-spin flex-shrink-0" />
            ) : (
              <CheckCircle className="w-3 h-3 text-emerald-400 flex-shrink-0" />
            )}
            <Telescope className="w-3 h-3 text-cream-dim flex-shrink-0" />
            <span className={evt.status === "running" ? "text-violet-light" : "text-cream-dim"}>
              {TOOL_LABELS[evt.tool] ?? evt.tool}
            </span>
            {evt.status === "done" && (
              <span className="ml-auto text-emerald-400/70">done</span>
            )}
            {evt.output !== undefined && (
              expanded[i]
                ? <ChevronUp className="w-3 h-3 text-cream-dim ml-1 flex-shrink-0" />
                : <ChevronDown className="w-3 h-3 text-cream-dim ml-1 flex-shrink-0" />
            )}
          </button>

          {expanded[i] && evt.output !== undefined && (
            <div className="border-t border-cosmos-700 px-3 py-2">
              <pre className="text-cream-dim/80 whitespace-pre-wrap break-all leading-relaxed max-h-48 overflow-y-auto">
                {typeof evt.output === "string"
                  ? evt.output
                  : JSON.stringify(evt.output, null, 2)}
              </pre>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
