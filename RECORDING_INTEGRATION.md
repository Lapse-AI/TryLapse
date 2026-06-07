# rrweb + Playwright Video Recording Integration

## Overview

Launch Rehearsal now captures user journeys using a hybrid approach:

1. **rrweb (Event-based recording)** — Captures every DOM mutation, click, scroll, keystroke
2. **Playwright Video** — Captures full screen video of journeys
3. **Interactive Replay** — Reconstruct journey playback from events

## Components Added

### Backend

#### 1. Recording Module (`launch-rehearsal/src/rehearse/recording.py`)
- `save_rrweb_recording()` — Stores rrweb event JSON
- `load_rrweb_recording()` — Retrieves event recording
- `get_video_path()` — Finds Playwright video file
- `list_recordings_for_run()` — Lists all recordings for a run

#### 2. API Endpoints (Added to `server.py`)
- `POST /api/recordings/save` — Save rrweb events from frontend
- `GET /api/recordings/list?runId=X` — List all recordings for a run
- `GET /api/recordings/{runId}/{journeyId}` — Get recording metadata
- `GET /api/recordings/{runId}/{journeyId}/video` — Stream video file
- `GET /api/recordings/{runId}/{journeyId}/export` — Download events JSON

#### 3. Browser Video Support (Modified `browser.py`)
- Added `record_video` parameter to `BrowserSession.__init__()`
- Playwright now records video when `record_video=True`
- Videos saved to `artifacts/{runId}/videos/`

### Frontend

#### 1. Recording Hook (`src/hooks/use-rrweb-recorder.ts`)
- `useRRWebRecorder()` — React hook for rrweb recording
- Exposes: `getRecording()`, `exportRecording()`, `clearRecording()`

#### 2. Recording Wrapper (`src/components/recording-wrapper.tsx`)
- `RecordingWrapper` — Component that wraps app to enable recording
- Provides ref-based API for programmatic access

#### 3. Playback Component (`src/components/journey-recording-player.tsx`)
- `JourneyRecordingPlayer` — Displays recorded journey
- Shows both video and event count
- Allows switching between video playback and event export
- Download button for raw event JSON

## How It Works

### Recording During Run Execution

```
Journey Agent executes steps
    ↓
[CANONICAL SEED ONLY: seed=1, loop=1, viewport=desktop]
    ├─ rrweb captures: DOM mutations, clicks, inputs, scrolls
    ├─ Playwright captures: Full screen video
    └─ Both stored in artifacts/{runId}/
    ↓
Journey Completed
```

### Event Flow

1. **Journey executes** → Playwright starts video recording
2. **Frontend rrweb** → Captures interactive events in parallel (if UI is involved)
3. **On completion** → Events saved via `POST /api/recordings/save`
4. **Video finalization** → Playwright video file saved to disk
5. **Dashboard** → Displays playback component with both formats available

## Usage in Code

### Enable Video Recording for a Journey

```python
# In orchestrator or run_rehearsal:
with BrowserSession(config, artifacts_dir, record_video=True) as session:
    # Journey execution with automatic video capture
    journey_agent.execute(ctx)
```

### Export Recording from Frontend

```typescript
// In a React component
const recorderRef = useRef(null);

function saveRecording() {
  const result = await recorderRef.current?.exportRecording(
    runId, 
    journeyId
  );
  console.log("Saved:", result);
}
```

### Display Recording in Dashboard

```typescript
import { JourneyRecordingPlayer } from '@/components/journey-recording-player';

export function JourneyDetailPage({ runId, journeyId }) {
  return (
    <>
      <h2>Journey Results</h2>
      <JourneyRecordingPlayer runId={runId} journeyId={journeyId} />
    </>
  );
}
```

## File Storage

```
artifacts/
  {runId}/
    recordings/
      {journeyId}-events.json    ← rrweb events
    videos/
      {journeyId}-*.webm        ← Playwright video
      {journeyId}-*.mp4
```

## API Reference

### Save Recording

```bash
POST /api/recordings/save
Content-Type: application/json

{
  "runId": "lr-test-1",
  "journeyId": "j-test-1",
  "events": [...],      # rrweb event array
  "eventCount": 150
}

Response:
{
  "ok": true,
  "path": "/path/to/events.json",
  "eventCount": 150
}
```

### List Recordings

```bash
GET /api/recordings/list?runId=lr-test-1

Response:
{
  "runId": "lr-test-1",
  "recordings": [
    {
      "journeyId": "j-test-1",
      "eventCount": 150,
      "hasVideo": true,
      "videoPath": "/path/to/video.webm"
    }
  ]
}
```

### Get Recording Info

```bash
GET /api/recordings/lr-test-1/j-test-1

Response:
{
  "journeyId": "j-test-1",
  "eventCount": 150,
  "hasVideo": true
}
```

### Download Video

```bash
GET /api/recordings/lr-test-1/j-test-1/video

Returns: WebM video stream
```

### Export Events

```bash
GET /api/recordings/lr-test-1/j-test-1/export

Returns: JSON file with all events
```

## Performance Considerations

### rrweb Recording
- **Overhead**: ~10-15% CPU (event-based, very lightweight)
- **Storage**: ~100KB-500KB per journey (depending on interaction density)
- **Playback**: Instant (all events in memory)

### Playwright Video
- **Overhead**: ~20-30% CPU (frame capture and encoding)
- **Storage**: ~5-50MB per journey (depending on duration and compression)
- **Video Quality**: 1280x720 by default, configurable

### Recommendations
- **Always enable rrweb** — Minimal overhead, maximum detail
- **Enable Playwright video for**:
  - Canonical runs (seed=1 only)
  - Critical journeys
  - When storage space available
  - For demo/marketing materials

## Future Enhancements

1. **Video + Event Sync** — Timeline showing which events occurred at which video frames
2. **Heatmaps** — Visual overlay of click locations from rrweb data
3. **Network Timeline** — API calls synced to video playback
4. **Accessibility** — Captions/descriptions for video
5. **Compression** — MP4 encoding instead of WebM for smaller files
6. **Cloud Export** — Send recordings to S3/GCS/storage service

## Testing

```bash
# Verify recording module
python3 -c "
import sys
sys.path.insert(0, 'launch-rehearsal/src')
from rehearse.recording import *
print('✓ Recording module ready')
"

# Verify frontend builds
cd Frontend_V1 && npm run build

# Test API endpoints (after backend restart)
curl http://localhost:8765/api/recordings/list?runId=test
```

## Configuration

Add to run config to enable recording:

```yaml
run:
  target_url: https://example.com
  record_video: true  # Optional: enable Playwright video
  # rrweb always enabled by default
```

Or via environment variable:

```bash
export REHEARSE_RECORD_VIDEO=1
./rehearse run -c config.yaml
```
