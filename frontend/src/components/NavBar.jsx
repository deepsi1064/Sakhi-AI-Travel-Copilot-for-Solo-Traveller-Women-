const TABS = [
  { id: "home", label: "Home", icon: "🏠" },
  { id: "plan", label: "Plan", icon: "🗺️" },
  { id: "profile", label: "Profile", icon: "🧳" },
  { id: "safety", label: "Safety", icon: "🛡️" },
  { id: "chat", label: "Chat", icon: "💬" },
];

export default function NavBar({ active, onNavigate }) {
  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <div className="navbar-brand">
          <span aria-hidden="true">🧭</span> Sakhi
        </div>
        <div className="navbar-tabs">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`navbar-tab ${active === tab.id ? "active" : ""}`}
              onClick={() => onNavigate(tab.id)}
              aria-current={active === tab.id ? "page" : undefined}
            >
              <span aria-hidden="true">{tab.icon}</span>
              <span className="navbar-tab-label">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
}
