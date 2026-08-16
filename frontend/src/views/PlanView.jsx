import { useState } from "react";
import Message from "../components/Message";
import SuggestionChips from "../components/SuggestionChips";
import { ChatApiError, planTrip, sendChatMessage } from "../api";
import { DESTINATION_SUGGESTIONS } from "../suggestions";

const EMPTY_FORM = { destination: "", startingCity: "", durationDays: "", budget: "", preferences: "" };

export default function PlanView({ sessionId }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  // Generated plans live only in this session's React state — there's no
  // "trips" table server-side, only preferences/places via Memory. See
  // docs/planning.md.
  const [plans, setPlans] = useState([]);

  function updateField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (loading) return;
    setError(null);
    setLoading(true);
    try {
      const result = await planTrip({
        destination: form.destination.trim() || null,
        starting_city: form.startingCity.trim() || null,
        duration_days: form.durationDays ? Number(form.durationDays) : null,
        budget: form.budget.trim() || null,
        preferences: form.preferences.trim() || null,
        session_id: sessionId,
      });
      setPlans((prev) => [
        { id: Date.now(), destination: form.destination.trim(), saving: false, saved: false, ...result },
        ...prev,
      ]);
    } catch (err) {
      setError(err instanceof ChatApiError ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveTrip(planId) {
    const target = plans.find((p) => p.id === planId);
    if (!target) return;
    setPlans((prev) => prev.map((p) => (p.id === planId ? { ...p, saving: true } : p)));

    const note = `Planning a trip${target.destination ? ` to ${target.destination}` : ""}: ${target.plan.slice(0, 150)}`;
    try {
      await sendChatMessage(`Please remember: ${note}`, sessionId);
      setPlans((prev) => prev.map((p) => (p.id === planId ? { ...p, saving: false, saved: true } : p)));
    } catch {
      setPlans((prev) => prev.map((p) => (p.id === planId ? { ...p, saving: false } : p)));
    }
  }

  return (
    <div className="view plan-view">
      <div className="view-intro">
        <h2>Plan a Trip</h2>
        <p>Tell Sakhi your trip details — get a personalized, safety-aware itinerary.</p>
      </div>

      <form className="plan-form" onSubmit={handleSubmit}>
        <label>
          Destination
          <input
            type="text"
            value={form.destination}
            onChange={(e) => updateField("destination", e.target.value)}
            placeholder="Leave blank for a suggestion"
            disabled={loading}
          />
        </label>
        <SuggestionChips items={DESTINATION_SUGGESTIONS} onPick={(d) => updateField("destination", d)} disabled={loading} />

        <label>
          Starting city
          <input
            type="text"
            value={form.startingCity}
            onChange={(e) => updateField("startingCity", e.target.value)}
            placeholder="e.g. Mumbai"
            disabled={loading}
          />
        </label>

        <div className="form-row-split">
          <label>
            Duration (days)
            <input
              type="number"
              min="1"
              max="90"
              value={form.durationDays}
              onChange={(e) => updateField("durationDays", e.target.value)}
              disabled={loading}
            />
          </label>
          <label>
            Approx. budget
            <input
              type="text"
              value={form.budget}
              onChange={(e) => updateField("budget", e.target.value)}
              placeholder="e.g. ₹15,000 total"
              disabled={loading}
            />
          </label>
        </div>

        <label>
          Preferences / constraints for this trip
          <textarea
            value={form.preferences}
            onChange={(e) => updateField("preferences", e.target.value)}
            placeholder="e.g. travelling with a friend, want one beach + one heritage site"
            rows={2}
            disabled={loading}
          />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? "Planning…" : "Plan my trip"}
        </button>
      </form>

      {error && <div className="error-banner">{error}</div>}

      <div className="plan-results">
        {plans.map((p) => (
          <div key={p.id} className="card plan-card">
            <Message role="assistant" text={p.plan} disclaimer={p.disclaimer} toolCalls={p.tool_calls} />
            <div className="plan-emergency">
              <strong>Emergency numbers</strong>
              <p>{p.emergency_info}</p>
            </div>
            <button
              type="button"
              className="link-button"
              onClick={() => handleSaveTrip(p.id)}
              disabled={p.saving || p.saved}
            >
              {p.saved ? "Saved to My Profile" : p.saving ? "Saving…" : "Save this trip"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
