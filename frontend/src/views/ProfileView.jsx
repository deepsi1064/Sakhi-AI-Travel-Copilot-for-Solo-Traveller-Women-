import { useEffect, useState } from "react";
import Message from "../components/Message";
import { useChatThread } from "../useChatThread";

// No dedicated "get/set memory" endpoint exists (by design — see
// docs/memory.md: memory is only exposed as agent tools, not a REST
// resource). Each filled field is sent as its own /chat message so it maps
// to a single remember_preference call within budget, then this prompt
// reliably nudges recall_traveller_context for the summary. Same /chat
// contract throughout, no new API.
const RECALL_PROMPT = "What preferences and places have you saved for me so far?";

const TRAVEL_STYLES = ["No preference", "Relaxed", "Adventure", "Cultural", "Mixed"];
const PACE_PREFERENCES = ["No preference", "Quiet places", "Lively / crowded places"];
const TRANSPORT_OPTIONS = ["No preference", "Train", "Bus", "Flight", "Local auto-rickshaw"];

const EMPTY_PROFILE = { budget: "", style: TRAVEL_STYLES[0], pace: PACE_PREFERENCES[0], transport: TRANSPORT_OPTIONS[0], avoid: "", duration: "" };

export default function ProfileView({ sessionId }) {
  const { messages, loading, error, send } = useChatThread(sessionId, []);
  const [profile, setProfile] = useState(EMPTY_PROFILE);
  const [hasFetched, setHasFetched] = useState(false);

  useEffect(() => {
    if (!hasFetched) {
      setHasFetched(true);
      send(RECALL_PROMPT);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasFetched]);

  function updateField(field, value) {
    setProfile((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSave(e) {
    e.preventDefault();
    if (loading) return;

    const statements = [];
    if (profile.budget.trim()) statements.push(`My typical travel budget is ${profile.budget.trim()}.`);
    if (profile.style !== "No preference") statements.push(`My preferred travel style is ${profile.style}.`);
    if (profile.pace !== "No preference") statements.push(`I prefer ${profile.pace.toLowerCase()}.`);
    if (profile.transport !== "No preference") statements.push(`My preferred transportation is ${profile.transport}.`);
    if (profile.avoid.trim()) statements.push(`Please remember I want to avoid: ${profile.avoid.trim()}.`);
    if (profile.duration.trim()) statements.push(`My typical trip duration is ${profile.duration.trim()} days.`);

    for (const statement of statements) {
      // eslint-disable-next-line no-await-in-loop
      await send(statement);
    }
    await send(RECALL_PROMPT);
  }

  const latest = [...messages].reverse().find((m) => m.role === "assistant");

  return (
    <div className="view profile-view">
      <div className="view-intro">
        <h2>My Profile</h2>
        <p>Tell Sakhi your travel preferences once — she reuses them for every plan this session.</p>
      </div>

      <form className="profile-form" onSubmit={handleSave}>
        <label>
          Budget range
          <input
            type="text"
            value={profile.budget}
            onChange={(e) => updateField("budget", e.target.value)}
            placeholder="e.g. ₹1500/day, budget-conscious"
            disabled={loading}
          />
        </label>

        <label>
          Travel style
          <select value={profile.style} onChange={(e) => updateField("style", e.target.value)} disabled={loading}>
            {TRAVEL_STYLES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>

        <label>
          Quiet vs crowded
          <select value={profile.pace} onChange={(e) => updateField("pace", e.target.value)} disabled={loading}>
            {PACE_PREFERENCES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>

        <label>
          Preferred transportation
          <select value={profile.transport} onChange={(e) => updateField("transport", e.target.value)} disabled={loading}>
            {TRANSPORT_OPTIONS.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>

        <label>
          Things to avoid
          <input
            type="text"
            value={profile.avoid}
            onChange={(e) => updateField("avoid", e.target.value)}
            placeholder="e.g. overnight buses, crowded festivals"
            disabled={loading}
          />
        </label>

        <label>
          Typical trip duration (days)
          <input
            type="number"
            min="1"
            max="90"
            value={profile.duration}
            onChange={(e) => updateField("duration", e.target.value)}
            disabled={loading}
          />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? "Saving…" : "Save Profile"}
        </button>
      </form>

      <div className="view-intro">
        <h3>What Sakhi remembers</h3>
      </div>
      <div className="card">
        {loading && messages.length === 0 && <p className="muted">Loading what Sakhi remembers…</p>}
        {latest && <Message {...latest} />}
        {!loading && !latest && <p className="muted">Nothing yet — save your profile above.</p>}
      </div>

      {error && <div className="error-banner">{error}</div>}

      <button type="button" className="link-button" onClick={() => send(RECALL_PROMPT)} disabled={loading}>
        Refresh
      </button>
    </div>
  );
}
