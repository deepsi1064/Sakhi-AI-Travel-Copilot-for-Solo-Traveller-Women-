import { useRef, useState } from "react";
import NavBar from "./components/NavBar";
import HomeView from "./views/HomeView";
import ChatView from "./views/ChatView";
import PlanView from "./views/PlanView";
import ProfileView from "./views/ProfileView";
import SafetyView from "./views/SafetyView";
import { getSessionId } from "./session";
import "./App.css";

export default function App() {
  const sessionId = useRef(getSessionId()).current;
  const [activeView, setActiveView] = useState("home");
  // Views mount once, on first visit, then stay mounted (hidden via CSS) so
  // their local state (chat history, fetched memory summary, generated
  // plans) survives tab switches without needing a shared store.
  const [visitedViews, setVisitedViews] = useState(() => new Set(["home"]));
  const [pendingMessage, setPendingMessage] = useState(null);

  function goTo(view) {
    setVisitedViews((prev) => (prev.has(view) ? prev : new Set(prev).add(view)));
    setActiveView(view);
  }

  function askSakhi(text) {
    setPendingMessage(text);
    goTo("chat");
  }

  function slotClass(view) {
    return activeView === view ? "view-slot" : "view-slot hidden";
  }

  return (
    <div className="app">
      <NavBar active={activeView} onNavigate={goTo} />

      <div className="view-container">
        {visitedViews.has("home") && (
          <div className={slotClass("home")}>
            <HomeView onAsk={askSakhi} onPlan={() => goTo("plan")} />
          </div>
        )}
        {visitedViews.has("plan") && (
          <div className={slotClass("plan")}>
            <PlanView sessionId={sessionId} />
          </div>
        )}
        {visitedViews.has("profile") && (
          <div className={slotClass("profile")}>
            <ProfileView sessionId={sessionId} />
          </div>
        )}
        {visitedViews.has("safety") && (
          <div className={slotClass("safety")}>
            <SafetyView sessionId={sessionId} />
          </div>
        )}
        {visitedViews.has("chat") && (
          <div className={slotClass("chat")}>
            <ChatView
              sessionId={sessionId}
              pendingMessage={pendingMessage}
              onConsumePending={() => setPendingMessage(null)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
