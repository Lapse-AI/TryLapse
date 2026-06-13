import { useEffect, useRef } from "react";
import rrweb from "rrweb";

interface RecordingEvent {
  type: number;
  data: Record<string, unknown>;
  timestamp: number;
}

export function useRRWebRecorder(enabled: boolean = true) {
  const recordingRef = useRef<RecordingEvent[]>([]);
  const stopRecordRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const events: RecordingEvent[] = [];
    recordingRef.current = events;

    const stop = rrweb.record({
      emit(event: RecordingEvent) {
        events.push(event);
      },
      recordCanvas: true,
      recordCrossOriginIframes: false,
      sampling: {
        mousemove: 10,
        input: "last",
        scroll: 150,
      },
      maskAllInputs: false,
      maskInputOptions: {
        password: true,
      },
      blockClass: "rr-block",
      ignoreClass: "rr-ignore",
    });

    stopRecordRef.current = stop;

    return () => {
      if (stop) {
        stop();
      }
    };
  }, [enabled]);

  const getRecording = () => recordingRef.current;

  const exportRecording = async (runId: string, journeyId: string) => {
    const events = recordingRef.current;
    if (events.length === 0) {
      console.warn("No recording events to export");
      return null;
    }

    try {
      const response = await fetch("/api/recordings/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          runId,
          journeyId,
          events,
          eventCount: events.length,
          timestamp: new Date().toISOString(),
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to save recording: ${response.statusText}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error("Failed to export recording:", error);
      return null;
    }
  };

  const clearRecording = () => {
    recordingRef.current = [];
  };

  return {
    getRecording,
    exportRecording,
    clearRecording,
    isRecording: !!stopRecordRef.current,
  };
}
