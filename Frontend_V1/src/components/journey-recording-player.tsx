import { useEffect, useRef, useState } from "react";
import { Loader2, Play, Download } from "lucide-react";

interface JourneyRecordingPlayerProps {
  runId: string;
  journeyId: string;
}

export function JourneyRecordingPlayer({ runId, journeyId }: JourneyRecordingPlayerProps) {
  const [loading, setLoading] = useState(true);
  const [recording, setRecording] = useState<{ eventCount: number; hasVideo: boolean } | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  const [playMode, setPlayMode] = useState<"events" | "video">("events");
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    const fetchRecording = async () => {
      try {
        const response = await fetch(`/api/recordings/${runId}/${journeyId}`);
        if (!response.ok) throw new Error("Recording not found");
        const data = await response.json();
        setRecording(data);
        if (data.hasVideo) setPlayMode("video");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load recording");
      } finally {
        setLoading(false);
      }
    };

    fetchRecording();
  }, [runId, journeyId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8 text-muted-foreground">
        <Loader2 className="w-5 h-5 animate-spin mr-2" />
        Loading recording...
      </div>
    );
  }

  if (error) {
    return <div className="text-sm text-destructive py-4">{error}</div>;
  }

  if (!recording) {
    return <div className="text-sm text-muted-foreground py-4">No recording available</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2 items-center">
        <span className="text-sm font-medium">Recording</span>
        <span className="text-xs bg-surface px-2 py-1 rounded">{recording.eventCount} events</span>
        {recording.hasVideo && (
          <button
            onClick={() => setPlayMode(playMode === "video" ? "events" : "video")}
            className="text-xs px-3 py-1 rounded bg-primary text-primary-foreground hover:opacity-90"
          >
            {playMode === "video" ? "Show Replay" : "Show Video"}
          </button>
        )}
      </div>

      {playMode === "events" && (
        <div className="border border-border rounded-lg p-4">
          <div className="flex items-center gap-2 mb-4">
            <Play className="w-4 h-4 text-primary" />
            <span className="text-sm text-muted-foreground">
              Event replay: {recording.eventCount} interactions captured
            </span>
          </div>
          <div className="text-xs text-muted-foreground bg-surface-2 p-3 rounded">
            Interactive replay showing every click, scroll, input, and network request
          </div>
          <button
            onClick={() => {
              const link = document.createElement("a");
              link.href = `/api/recordings/${runId}/${journeyId}/export`;
              link.download = `${journeyId}-recording.json`;
              link.click();
            }}
            className="mt-3 text-xs px-3 py-2 rounded border border-border hover:bg-surface flex items-center gap-2 w-fit"
          >
            <Download className="w-3 h-3" />
            Export Events
          </button>
        </div>
      )}

      {playMode === "video" && recording.hasVideo && (
        <video
          controls
          className="w-full border border-border rounded-lg bg-black"
          style={{ maxHeight: "500px" }}
        >
          <source src={`/api/recordings/${runId}/${journeyId}/video`} type="video/webm" />
          Your browser does not support the video tag.
        </video>
      )}
    </div>
  );
}
