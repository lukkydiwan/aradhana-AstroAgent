import { useEffect, useRef, useState } from "react";
import type { BirthDetails } from "../types";
import { useChat } from "../hooks/useChat";
import BirthDetailsForm from "./BirthDetailsForm";
import MessageBubble from "./MessageBubble";
import { Send, Square, RefreshCw } from "lucide-react";

const SUGGESTIONS = [
  "What does my chart say about my career path?",
  "What's the cosmic energy for me today?",
  "Tell me about my Moon sign.",
  "What are my strongest placements?",
];

export default function ChatInterface() {
  const { messages, isStreaming, error, sendMessage, stopStreaming, clearSession } = useChat();
  const [input, setInput] = useState("");
  const [birthDetails, setBirthDetails] = useState<BirthDetails | undefined>();
  const [showForm, setShowForm] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || isStreaming) return;
    setInput("");
    sendMessage(text, birthDetails);
    if (showForm && birthDetails) setShowForm(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleBirthSubmit = (details: BirthDetails) => {
    setBirthDetails(details);
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-cosmos-700/50">
        <div>
          <h1 className="font-serif text-gold-300 text-lg tracking-wide">Aradhana</h1>
          <p className="text-cream-dim text-xs">Your daily astrology companion</p>
        </div>
        <button
          onClick={clearSession}
          title="New conversation"
          className="text-cream-dim hover:text-cream transition p-1.5 rounded-lg hover:bg-cosmos-700/50"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Scroll area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-5">
        {/* Birth details panel */}
        <div className="max-w-2xl mx-auto">
          {(showForm || !birthDetails) ? (
            <BirthDetailsForm onSubmit={handleBirthSubmit} compact={!isEmpty} />
          ) : (
            <button
              onClick={() => setShowForm(true)}
              className="text-xs text-cream-dim/60 hover:text-cream-dim transition underline underline-offset-2 w-full text-center"
            >
              Edit birth details
            </button>
          )}
        </div>

        {/* Welcome message */}
        {isEmpty && (
          <div className="max-w-2xl mx-auto text-center space-y-6 pt-4 animate-fade-in">
            <div>
              <div className="text-4xl mb-3">✦</div>
              <h2 className="font-serif text-cream text-xl mb-2 italic">
                Welcome, dear seeker
              </h2>
              <p className="text-cream-dim text-sm leading-relaxed max-w-md mx-auto">
                Share your birth details above, then ask me anything — about your natal chart,
                today's planetary energies, or what the stars say about your path.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-md mx-auto">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => { setInput(s); inputRef.current?.focus(); }}
                  className="text-left px-3 py-2.5 rounded-xl border border-cosmos-700 bg-cosmos-800/40 text-cream-dim text-xs hover:border-gold-500/40 hover:text-cream hover:bg-cosmos-800/80 transition leading-snug"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="max-w-2xl mx-auto space-y-4">
          {messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
        </div>

        {/* Error banner */}
        {error && (
          <div className="max-w-2xl mx-auto px-4 py-3 rounded-xl bg-red-900/30 border border-red-500/30 text-red-300 text-xs">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="px-4 pb-5 pt-3 border-t border-cosmos-700/50">
        <div className="max-w-2xl mx-auto flex gap-2 items-end">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your chart, transits, or the stars…"
              rows={1}
              style={{ resize: "none" }}
              className="w-full bg-cosmos-800 border border-cosmos-700 rounded-2xl px-4 py-3 pr-12 text-cream text-sm placeholder-cream-dim/40 focus:outline-none focus:border-gold-500/50 focus:ring-1 focus:ring-gold-500/20 transition leading-relaxed min-h-[48px] max-h-36 overflow-y-auto"
              onInput={(e) => {
                const t = e.currentTarget;
                t.style.height = "auto";
                t.style.height = Math.min(t.scrollHeight, 144) + "px";
              }}
            />
          </div>

          {isStreaming ? (
            <button
              onClick={stopStreaming}
              className="w-11 h-11 flex items-center justify-center rounded-2xl bg-red-900/40 border border-red-500/30 text-red-400 hover:bg-red-900/60 transition flex-shrink-0"
              title="Stop"
            >
              <Square className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              className="w-11 h-11 flex items-center justify-center rounded-2xl bg-gradient-to-br from-gold-500 to-gold-400 text-cosmos-900 hover:from-gold-400 hover:to-gold-300 disabled:opacity-30 disabled:cursor-not-allowed transition flex-shrink-0"
              title="Send"
            >
              <Send className="w-4 h-4" />
            </button>
          )}
        </div>
        <p className="max-w-2xl mx-auto text-center text-cream-dim/30 text-xs mt-2">
          Readings are for reflection only — not medical, legal, or financial advice.
        </p>
      </div>
    </div>
  );
}
