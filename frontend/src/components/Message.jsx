export default function Message({ role, text, disclaimer, toolCalls }) {
  const isUser = role === "user";
  return (
    <div className={`message ${isUser ? "message-user" : "message-assistant"}`}>
      <div className="message-role">{isUser ? "You" : "Sakhi"}</div>
      <div className="message-text">{text}</div>
      {toolCalls && toolCalls.length > 0 && (
        <div className="message-tools">used: {toolCalls.map((t) => t.name).join(", ")}</div>
      )}
      {disclaimer && <div className="message-disclaimer">{disclaimer}</div>}
    </div>
  );
}
