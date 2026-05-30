import type { ChatMessage } from "../types";
import ToolActivity from "./ToolActivity";

interface Props {
  message: ChatMessage;
}

function Cursor() {
  return (
    <span className="inline-block w-0.5 h-4 bg-gold-400 animate-pulse ml-0.5 align-text-bottom" />
  );
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end animate-fade-in">
        <div className="max-w-[80%] rounded-2xl rounded-tr-sm px-4 py-3 bg-gradient-to-br from-violet-muted to-violet-muted/70 text-cream text-sm leading-relaxed">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start animate-fade-in">
      <div className="max-w-[88%] space-y-1">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-gold-500 to-gold-400 flex items-center justify-center flex-shrink-0">
            <span className="text-cosmos-900 text-xs">✦</span>
          </div>
          <span className="text-gold-400 text-xs font-medium tracking-wider">Jyotish</span>
        </div>

        {(message.toolEvents?.length ?? 0) > 0 && (
          <ToolActivity events={message.toolEvents ?? []} />
        )}

        {(message.content || message.streaming) && (
          <div className="rounded-2xl rounded-tl-sm px-4 py-3 bg-cosmos-800/80 border border-cosmos-700/50 text-cream text-sm leading-relaxed whitespace-pre-wrap">
            {message.content}
            {message.streaming && !message.content && (
              <span className="text-cream-dim italic">Thinking…</span>
            )}
            {message.streaming && <Cursor />}
          </div>
        )}
      </div>
    </div>
  );
}
