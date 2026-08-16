import { useState } from "react";
import { ChatApiError, sendChatMessage } from "./api";

// Shared by ChatView/TripsView/SafetyView — all three are just the same
// send-to-/chat + track-loading/error pattern aimed at a different prompt.
export function useChatThread(sessionId, initialMessages = []) {
  const [messages, setMessages] = useState(initialMessages);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function send(text) {
    const trimmed = text.trim();
    if (!trimmed || loading) return null;

    setMessages((prev) => [...prev, { role: "user", text: trimmed }]);
    setError(null);
    setLoading(true);

    try {
      const result = await sendChatMessage(trimmed, sessionId);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: result.reply,
          disclaimer: result.disclaimer,
          toolCalls: result.tool_calls,
        },
      ]);
      return result;
    } catch (err) {
      setError(err instanceof ChatApiError ? err.message : "Something went wrong.");
      return null;
    } finally {
      setLoading(false);
    }
  }

  return { messages, loading, error, send };
}
