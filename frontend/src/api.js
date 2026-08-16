// Talks to the existing FastAPI /chat endpoint. No new backend surface —
// same request/response shape used by curl in the backend docs.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY || "";

export class ChatApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

export async function sendChatMessage(message, sessionId) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
      },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
  } catch {
    throw new ChatApiError("Could not reach the Sakhi server. Is the backend running?", 0);
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body.detail) detail = body.detail;
    } catch {
      // non-JSON error body: keep the generic message
    }
    throw new ChatApiError(detail, response.status);
  }

  return response.json();
}

// Same client, same error handling, different endpoint — POST /plan reuses
// the agent loop under the hood (see docs/planning.md), it's not a second
// backend.
export async function planTrip(payload) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/plan`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(API_KEY ? { "X-API-Key": API_KEY } : {}),
      },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ChatApiError("Could not reach the Sakhi server. Is the backend running?", 0);
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body.detail) detail = body.detail;
    } catch {
      // non-JSON error body: keep the generic message
    }
    throw new ChatApiError(detail, response.status);
  }

  return response.json();
}
