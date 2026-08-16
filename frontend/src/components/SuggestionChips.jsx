export default function SuggestionChips({ items, onPick, disabled }) {
  return (
    <div className="chip-row">
      {items.map((text) => (
        <button
          key={text}
          type="button"
          className="chip"
          onClick={() => onPick(text)}
          disabled={disabled}
        >
          {text}
        </button>
      ))}
    </div>
  );
}
