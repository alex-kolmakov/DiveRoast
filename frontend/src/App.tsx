import { useState, useCallback } from "react";
import { FileUpload } from "./components/FileUpload";
import { ChatInterface } from "./components/ChatInterface";
import type { UploadResponse } from "./types";

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);

  const handleUploadComplete = useCallback((response: UploadResponse) => {
    setSessionId(response.session_id);
  }, []);

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        backgroundColor: "#0f172a",
        color: "#f8fafc",
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      }}
    >
      {/* Left panel: Upload */}
      <div
        style={{
          width: "300px",
          borderRight: "1px solid #1e293b",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            padding: "16px",
            borderBottom: "1px solid #1e293b",
          }}
        >
          <h1 style={{ margin: 0, fontSize: "20px" }}>DiveRoast</h1>
          <p
            style={{
              margin: "4px 0 0",
              fontSize: "12px",
              color: "#64748b",
            }}
          >
            Upload your dive log to get roasted
          </p>
        </div>
        <FileUpload
          onUploadComplete={handleUploadComplete}
          sessionId={sessionId}
        />
      </div>

      {/* Right panel: Chat */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <ChatInterface sessionId={sessionId} />
      </div>
    </div>
  );
}

export default App;
