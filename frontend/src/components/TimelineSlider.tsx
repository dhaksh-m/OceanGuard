import React, { useEffect } from 'react';
import { Play, Pause, RotateCcw, Clock, FastForward } from 'lucide-react';
import { useIncidentStore } from '../store/useIncidentStore';

export const TimelineSlider: React.FC = () => {
  const { timeline, setTimelineTime, togglePlayback, setPlaybackSpeed } = useIncidentStore();

  // Playback timer effect
  useEffect(() => {
    if (!timeline.isPlaying) return;

    const interval = setInterval(() => {
      setTimelineTime(
        timeline.currentTimeHoursAgo >= 12.0
          ? 0.0
          : timeline.currentTimeHoursAgo + 0.2 * timeline.playbackSpeed
      );
    }, 400);

    return () => clearInterval(interval);
  }, [timeline.isPlaying, timeline.currentTimeHoursAgo, timeline.playbackSpeed]);

  return (
    <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '16px' }}>
      {/* Play/Pause Button */}
      <button
        onClick={togglePlayback}
        style={{
          width: '36px',
          height: '36px',
          borderRadius: '50%',
          background: timeline.isPlaying ? '#ff3b30' : '#1677e8',
          border: 'none',
          color: '#ffffff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer'
        }}
        title={timeline.isPlaying ? 'Pause Playback' : 'Start Playback'}
      >
        {timeline.isPlaying ? <Pause size={18} /> : <Play size={18} style={{ marginLeft: '2px' }} />}
      </button>

      {/* Speed Rate Button */}
      <button
        onClick={() => {
          const nextSpeed = timeline.playbackSpeed === 1 ? 2 : timeline.playbackSpeed === 2 ? 5 : 1;
          setPlaybackSpeed(nextSpeed);
        }}
        style={{
          background: '#0d1c2b',
          border: '1px solid #1e3449',
          color: '#32c7e8',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '11px',
          fontWeight: 'bold',
          cursor: 'pointer'
        }}
      >
        {timeline.playbackSpeed}x
      </button>

      {/* Timeline Scrubber */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#9fb2c3' }}>
          <span><strong style={{ color: '#32c7e8' }}>-{timeline.currentTimeHoursAgo.toFixed(1)}h</strong> (Hindcast Origin)</span>
          <span>Observation Time (0h)</span>
        </div>

        <input
          type="range"
          min="0"
          max="12"
          step="0.1"
          value={timeline.currentTimeHoursAgo}
          onChange={(e) => setTimelineTime(parseFloat(e.target.value))}
          style={{ width: '100%', accentColor: '#1677e8', cursor: 'pointer' }}
        />
      </div>
    </div>
  );
};
