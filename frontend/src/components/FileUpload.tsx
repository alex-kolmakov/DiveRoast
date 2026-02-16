import { useState, useCallback } from "react";
import { uploadDiveLog } from "../services/api";
import type { UploadResponse } from "../types";

interface Props {
  onUploadComplete: (response: UploadResponse) => void;
  sessionId: string | null;
}

export function FileUpload({ onUploadComplete, sessionId }: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setIsUploading(true);
      setError(null);

      try {
        const result = await uploadDiveLog(file, sessionId || undefined);
        setUploadResult(result);
        onUploadComplete(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Upload failed");
      } finally {
        setIsUploading(false);
      }
    },
    [sessionId, onUploadComplete]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div style={{ padding: "16px" }}>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${isDragging ? "#2563eb" : "#475569"}`,
          borderRadius: "12px",
          padding: "24px",
          textAlign: "center",
          cursor: "pointer",
          backgroundColor: isDragging ? "#1e3a5f" : "#0f172a",
          transition: "all 0.2s",
        }}
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".ssrf,.xml"
          onChange={handleChange}
          style={{ display: "none" }}
        />
        <div style={{ fontSize: "32px", marginBottom: "8px" }}>
          {isUploading ? "..." : "\u{1F4C2}"}
        </div>
        <p style={{ color: "#94a3b8", margin: 0 }}>
          {isUploading
            ? "Parsing dive log..."
            : "Drop your .ssrf or .xml dive log here"}
        </p>
      </div>

      {error && (
        <p style={{ color: "#ef4444", marginTop: "8px", fontSize: "14px" }}>
          {error}
        </p>
      )}

      {uploadResult && (
        <div
          style={{
            marginTop: "12px",
            padding: "12px",
            backgroundColor: "#1e293b",
            borderRadius: "8px",
            fontSize: "14px",
            color: "#94a3b8",
          }}
        >
          <strong style={{ color: "#22c55e" }}>
            {uploadResult.dive_count} dives loaded
          </strong>
          <br />
          Dive numbers: {uploadResult.dive_numbers.join(", ")}
        </div>
      )}
    </div>
  );
}
