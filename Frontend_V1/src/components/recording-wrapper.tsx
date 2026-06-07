import { useEffect, useRef, ReactNode, MutableRefObject } from 'react';

export interface RecordingEvent {
  type: number;
  data: Record<string, unknown>;
  timestamp: number;
}

export interface RecorderRef {
  getRecording: () => RecordingEvent[];
  stopRecording: () => void;
  exportRecording: (runId: string, journeyId: string) => Promise<unknown>;
}

interface RecordingWrapperProps {
  children: ReactNode;
  recordRef?: MutableRefObject<RecorderRef | null>;
  enabled?: boolean;
}

export function RecordingWrapper({ children, recordRef, enabled = true }: RecordingWrapperProps) {
  const eventsRef = useRef<RecordingEvent[]>([]);
  const stopRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const events: RecordingEvent[] = [];
    eventsRef.current = events;

    try {
      // Load rrweb dynamically
      void import('rrweb').then((rrwebModule) => {
        const rrweb = rrwebModule.default || rrwebModule;
        const stop = rrweb.record?.({
          emit(event: RecordingEvent) {
            events.push(event);
          },
          recordCanvas: true,
          recordCrossOriginIframes: false,
          sampling: {
            mousemove: 10,
            input: 'last',
            scroll: 150,
          },
          maskAllInputs: false,
          blockClass: 'rr-block',
          ignoreClass: 'rr-ignore',
        });

        if (stop) {
          stopRef.current = stop;

          if (recordRef) {
            recordRef.current = {
              getRecording: () => events,
              stopRecording: () => stop?.(),
              exportRecording: async (runId: string, journeyId: string) => {
                try {
                  const response = await fetch('/api/recordings/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      runId,
                      journeyId,
                      events,
                      eventCount: events.length,
                      timestamp: new Date().toISOString(),
                    }),
                  });
                  if (!response.ok) throw new Error(response.statusText);
                  return await response.json();
                } catch (error) {
                  console.error('Failed to export recording:', error);
                  return null;
                }
              },
            };
          }
        }
      }).catch((error) => {
        console.error('Failed to load rrweb:', error);
      });
    } catch (error) {
      console.error('Failed to initialize recording:', error);
    }

    return () => {
      stopRef.current?.();
    };
  }, [enabled, recordRef]);

  return <>{children}</>;
}
