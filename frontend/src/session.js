// A stable session_id lets the backend's Memory tools (remember_preference,
// remember_place, recall_traveller_context) persist across page reloads —
// see docs/memory.md. Generated once per browser, kept in localStorage.
const SESSION_KEY = "sakhi_session_id";

export function getSessionId() {
  let sessionId = localStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, sessionId);
  }
  return sessionId;
}
