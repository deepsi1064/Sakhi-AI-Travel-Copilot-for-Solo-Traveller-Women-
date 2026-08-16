import { useEffect, useState } from "react";
import Message from "../components/Message";
import { useChatThread } from "../useChatThread";

// Same reasoning as TripsView's RECALL_PROMPT: no dedicated safety-info
// endpoint. This prompt is engineered to route through the real Safety MCP
// tool (get_emergency_info) and/or RAG safety content — same /chat contract.
const SAFETY_PROMPT = "What safety information and emergency contacts should I know as a solo female traveller in India?";

export default function SafetyView({ sessionId }) {
  const { messages, loading, error, send } = useChatThread(sessionId, []);
  const [question, setQuestion] = useState("");
  const [hasFetched, setHasFetched] = useState(false);

  useEffect(() => {
    if (!hasFetched) {
      setHasFetched(true);
      send(SAFETY_PROMPT);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasFetched]);

  function handleAsk(e) {
    e.preventDefault();
    const text = question.trim();
    if (!text || loading) return;
    setQuestion("");
    send(text);
  }

  return (
    <div className="view safety-view">
      <div className="view-intro">
        <h2>Safety</h2>
        <p>General guidance and emergency numbers — see the disclaimer on each answer.</p>
      </div>

      <div className="thread">
        {messages.map((m, i) => (
          <Message key={i} {...m} />
        ))}
        {loading && <div className="message message-assistant message-loading">Sakhi is checking…</div>}
      </div>

      {error && <div className="error-banner">{error}</div>}

      <form className="input-row" onSubmit={handleAsk}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about safety for a specific place or situation..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !question.trim()}>
          Ask
        </button>
      </form>
    </div>
  );
}
