import { useState, useCallback, useEffect, useRef } from "react";
import { UploadScreen } from "@/components/UploadScreen";
import { AnalyzingScreen } from "@/components/AnalyzingScreen";
import { Dashboard } from "@/components/Dashboard";
import { ChatDrawer } from "@/components/ChatDrawer";
import { useChat } from "@/hooks/useChat";
import { fetchDashboard } from "@/services/api";
import type { AppPhase, DashboardData, UploadResponse } from "@/types";

function App() {
  const [phase, setPhase] = useState<AppPhase>("upload");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [uploadResponse, setUploadResponse] = useState<UploadResponse | null>(null);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const roastFired = useRef(false);

  const { messages, isLoading, sendMessage } = useChat(sessionId);

  const handleUploadComplete = useCallback((response: UploadResponse) => {
    setSessionId(response.session_id);
    setUploadResponse(response);
    setPhase("analyzing");
  }, []);

  // Fetch dashboard data when entering analyzing phase
  useEffect(() => {
    if (phase !== "analyzing" || !sessionId) return;

    let cancelled = false;
    fetchDashboard(sessionId)
      .then((data) => {
        if (!cancelled) {
          setDashboardData(data);
          setPhase("dashboard");
        }
      })
      .catch((err) => {
        console.error("Dashboard fetch failed:", err);
        if (!cancelled) {
          setPhase("dashboard");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [phase, sessionId]);

  // Auto-fire roast message when dashboard mounts
  useEffect(() => {
    if (phase !== "dashboard" || !sessionId || roastFired.current) return;
    roastFired.current = true;
    sendMessage(
      "Analyze all my dives and give me a brutally honest roast. Highlight the most dangerous moments and tell me what I need to fix."
    );
  }, [phase, sessionId, sendMessage]);

  return (
    <div className="h-screen">
      {phase === "upload" && <UploadScreen onUploadComplete={handleUploadComplete} />}

      {phase === "analyzing" && (
        <AnalyzingScreen uploadResponse={uploadResponse} />
      )}

      {phase === "dashboard" && (
        <>
          {dashboardData ? (
            <Dashboard
              data={dashboardData}
              messages={messages}
              isLoading={isLoading}
              onToggleChat={() => setChatOpen(true)}
            />
          ) : (
            <div className="flex h-full items-center justify-center">
              <p className="text-muted-foreground">
                Dashboard data unavailable. Use chat to interact with your dives.
              </p>
            </div>
          )}
          <ChatDrawer
            open={chatOpen}
            onOpenChange={setChatOpen}
            sessionId={sessionId!}
            messages={messages}
            isLoading={isLoading}
            onSendMessage={sendMessage}
          />
        </>
      )}
    </div>
  );
}

export default App;
