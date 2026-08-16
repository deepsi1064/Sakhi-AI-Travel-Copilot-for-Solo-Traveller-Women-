import { useEffect, useRef, useState } from "react";
import Message from "../components/Message";
import SuggestionChips from "../components/SuggestionChips";
import { useChatThread } from "../useChatThread";
import { TOPIC_SUGGESTIONS } from "../suggestions";

const WELCOME = {
  role: "assistant",
  text: "Hi, I'm Sakhi — your travel copilot for solo trips in India. Ask me about a destination, transport, or safety context for your trip.",
};

export default function ChatView({ sessionId, pendingMessage, onConsumePending }) {
  const { messages, loading, error, send } = useChatThread(sessionId, [WELCOME]);
  const [input, setInput] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // A suggestion picked on the Home view arrives here as pendingMessage —
  // sent once, then cleared so it doesn't resend on re-render.
  useEffect(() => {
    if (pendingMessage) {
      send(pendingMessage);
      onConsumePending();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingMessage]);

  function handleSubmit(e) {
    e.preventDefault();
    if (!input.trim()) return;
    send(input);
    setInput("");
  }

  return (
    <div className="view chat-view">
      <main className="chat-window">
        {messages.map((m, i) => (
          <Message key={i} {...m} />
        ))}
        {loading && <div className="message message-assistant message-loading">Sakhi is thinking…</div>}
        <div ref={bottomRef} />
      </main>

      {error && <div className="error-banner">{error}</div>}

      <div className="chat-suggestions">
        <SuggestionChips items={TOPIC_SUGGESTIONS} onPick={send} disabled={loading} />
      </div>

      <form className="input-row chat-input" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about a destination, transport, or safety..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
