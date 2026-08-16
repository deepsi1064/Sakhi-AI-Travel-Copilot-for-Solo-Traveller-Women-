import { useState } from "react";
import SuggestionChips from "../components/SuggestionChips";
import { DESTINATION_SUGGESTIONS, TOPIC_SUGGESTIONS } from "../suggestions";

export default function HomeView({ onAsk, onPlan }) {
  const [input, setInput] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;
    onAsk(text);
    setInput("");
  }

  return (
    <div className="view home-view">
      <section className="hero">
        <span className="hero-logo" aria-hidden="true">
          🧭
        </span>
        <h1>Sakhi</h1>
        <p className="hero-tagline">Your AI travel decision assistant for solo women travelling in India</p>
        <p className="hero-description">
          Tell Sakhi your preferences, budget and trip details — she turns them into a
          practical, personalized, safety-aware travel plan. Not a generic chatbot: a
          decision assistant that remembers what matters to your trip.
        </p>

        <button type="button" className="cta-button" onClick={onPlan}>
          🗺️ Plan my trip
        </button>

        <form className="input-row input-row-large" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Or just ask Sakhi anything about your trip..."
          />
          <button type="submit" disabled={!input.trim()}>
            Ask Sakhi
          </button>
        </form>
      </section>

      <section className="home-suggestions">
        <h3>Popular destinations</h3>
        <SuggestionChips items={DESTINATION_SUGGESTIONS} onPick={(d) => onAsk(`Tell me about visiting ${d}`)} />

        <h3>Or ask about</h3>
        <SuggestionChips items={TOPIC_SUGGESTIONS} onPick={onAsk} />
      </section>
    </div>
  );
}
