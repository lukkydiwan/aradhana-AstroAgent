import { useCallback, useEffect, useRef, useState } from "react";
import type { BirthDetails, ChatMessage, StreamEvent, ToolEvent } from "../types";

const API_BASE = "/api";

function makeId() {
  return Math.random().toString(36).slice(2, 10);
}

export function useChat() {
  const [sessionId, setSessionId] = useState<string | null>(
    () => sessionStorage.getItem("astro_session_id")
  );
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Restore history when sessionId is known
  useEffect(() => {
    if (!sessionId) return;
    fetch(`${API_BASE}/sessions/${sessionId}/messages`)
      .then((r) => r.json())
      .then((data: { messages: { role: string; content: string }[] }) => {
        const restored: ChatMessage[] = data.messages
          .filter((m) => m.role === "user" || m.role === "assistant")
          .map((m) => ({
            id: makeId(),
            role: m.role as "user" | "assistant",
            content: m.content,
            timestamp: Date.now(),
          }));
        // Only restore if the user hasn't already started a new conversation.
        // Without this guard, the history fetch resolving after sendMessage fires
        // would wipe the in-flight assistant message from state.
        if (restored.length > 0) setMessages(prev => prev.length === 0 ? restored : prev);
      })
      .catch(() => {/* silently skip if session gone */});
  }, [sessionId]);

  const ensureSession = useCallback(async (): Promise<string> => {
    if (sessionId) return sessionId;
    const res = await fetch(`${API_BASE}/sessions`, { method: "POST" });
    const { session_id } = (await res.json()) as { session_id: string };
    sessionStorage.setItem("astro_session_id", session_id);
    setSessionId(session_id);
    return session_id;
  }, [sessionId]);

  const sendMessage = useCallback(
    async (text: string, birthDetails?: BirthDetails) => {
      if (isStreaming) return;
      setError(null);

      const sid = await ensureSession();

      const userMsg: ChatMessage = {
        id: makeId(),
        role: "user",
        content: text,
        timestamp: Date.now(),
      };

      const assistantMsgId = makeId();
      const assistantMsg: ChatMessage = {
        id: assistantMsgId,
        role: "assistant",
        content: "",
        streaming: true,
        toolEvents: [],
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);

      abortRef.current = new AbortController();

      try {
        const res = await fetch(`${API_BASE}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: text,
            session_id: sid,
            birth_details: birthDetails ?? null,
          }),
          signal: abortRef.current.signal,
        });

        if (!res.ok || !res.body) {
          throw new Error(`Server error: ${res.status}`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const evt = JSON.parse(line.slice(6)) as StreamEvent;

              if (evt.type === "token") {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? { ...m, content: m.content + (evt.content ?? "") }
                      : m
                  )
                );
              } else if (evt.type === "tool_start") {
                const te: ToolEvent = {
                  tool: evt.tool ?? "unknown",
                  status: "running",
                  input: evt.input,
                };
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? { ...m, toolEvents: [...(m.toolEvents ?? []), te] }
                      : m
                  )
                );
              } else if (evt.type === "tool_end") {
                setMessages((prev) =>
                  prev.map((m) => {
                    if (m.id !== assistantMsgId) return m;
                    const updated = (m.toolEvents ?? []).map((te) =>
                      te.tool === evt.tool && te.status === "running"
                        ? { ...te, status: "done" as const, output: evt.output }
                        : te
                    );
                    return { ...m, toolEvents: updated };
                  })
                );
              } else if (evt.type === "done") {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId ? { ...m, streaming: false } : m
                  )
                );
              } else if (evt.type === "error") {
                setError(evt.message ?? "An unexpected error occurred.");
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantMsgId
                      ? { ...m, streaming: false, content: m.content || "An error occurred." }
                      : m
                  )
                );
              }
            } catch {
              /* malformed SSE line — skip */
            }
          }
        }
      } catch (err: unknown) {
        if (err instanceof Error && err.name === "AbortError") return;
        setError(err instanceof Error ? err.message : "Connection failed.");
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId ? { ...m, streaming: false } : m
          )
        );
      } finally {
        setIsStreaming(false);
      }
    },
    [isStreaming, ensureSession]
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
    setMessages((prev) =>
      prev.map((m) => (m.streaming ? { ...m, streaming: false } : m))
    );
  }, []);

  const clearSession = useCallback(() => {
    sessionStorage.removeItem("astro_session_id");
    setSessionId(null);
    setMessages([]);
    setError(null);
  }, []);

  return { messages, isStreaming, error, sendMessage, stopStreaming, clearSession, sessionId };
}
