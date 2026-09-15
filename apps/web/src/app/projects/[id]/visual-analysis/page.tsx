'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';

export default function VisualAnalysisPage() {
  const { id: projectId } = useParams() as { id: string };
  const [runs, setRuns] = useState<any[]>([]);
  const [selectedRun, setSelectedRun] = useState<any>(null);
  const [regions, setRegions] = useState<any[]>([]);
  const [layouts, setLayouts] = useState<any[]>([]);
  const [focusTargets, setFocusTargets] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [currentTime, setCurrentTime] = useState(0);

  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    fetch(`/api/v1/projects/${projectId}/visual-analysis`)
      .then(res => res.json())
      .then(data => {
        setRuns(data.runs);
        if (data.runs.length > 0) {
          loadRunData(data.runs[0].id);
        }
      });
  }, [projectId]);

  const loadRunData = (runId: string) => {
    setSelectedRun(runs.find(r => r.id === runId) || { id: runId });
    fetch(`/api/v1/visual-analysis/${runId}/regions`).then(r => r.json()).then(setRegions);
    fetch(`/api/v1/visual-analysis/${runId}/layouts`).then(r => r.json()).then(setLayouts);
    fetch(`/api/v1/visual-analysis/${runId}/focus-targets`).then(r => r.json()).then(setFocusTargets);
    fetch(`/api/v1/visual-analysis/${runId}/events`).then(r => r.json()).then(setEvents);
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const activeRegions = regions.filter(r => currentTime >= r.start_time && currentTime <= r.end_time);
  const activeFocus = focusTargets.filter(ft => currentTime >= ft.start_time && currentTime <= ft.end_time);
  const currentLayout = layouts.find(l => currentTime >= l.start_time && currentTime <= l.end_time);

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">M7 - Visual Understanding & Focus Debugger</h1>
      
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-2">Runs</h2>
        <div className="flex gap-4">
          {runs.map(run => (
            <button 
              key={run.id}
              onClick={() => loadRunData(run.id)}
              className={`px-4 py-2 border rounded ${selectedRun?.id === run.id ? 'bg-blue-600 text-white' : ''}`}
            >
              {run.id.split('-')[0]} - {run.status}
            </button>
          ))}
          <button 
            className="px-4 py-2 border rounded bg-green-600 text-white"
            onClick={() => {
              fetch(`/api/v1/projects/${projectId}/visual-analysis`, { method: 'POST' })
                .then(r => r.json())
                .then(data => alert(`Started run: ${data.run_id}`));
            }}
          >
            + New Analysis
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-8">
        {/* Video Player */}
        <div className="relative border rounded bg-black aspect-video overflow-hidden">
          {/* We will just use a synthetic proxy for debugging */}
          <video 
            ref={videoRef}
            src="/synthetic_test.mp4" 
            controls 
            className="w-full h-full"
            onTimeUpdate={handleTimeUpdate}
          />
          
          {/* Overlays */}
          {activeRegions.map(region => (
            <div 
              key={region.id}
              className="absolute border-2 border-red-500 bg-red-500/20 pointer-events-none flex flex-col justify-end p-1"
              style={{
                left: `${region.x * 100}%`,
                top: `${region.y * 100}%`,
                width: `${region.width * 100}%`,
                height: `${region.height * 100}%`,
              }}
            >
              <span className="text-xs text-white bg-red-600 px-1 rounded">{region.region_type} ({Math.round(region.confidence * 100)}%)</span>
            </div>
          ))}

          {activeFocus.map(focus => (
            <div 
              key={focus.id}
              className="absolute border-4 border-yellow-400 bg-yellow-400/20 pointer-events-none"
              style={{
                left: focus.x !== null ? `${focus.x * 100}%` : '0%',
                top: focus.y !== null ? `${focus.y * 100}%` : '0%',
                width: focus.width !== null ? `${focus.width * 100}%` : '100%',
                height: focus.height !== null ? `${focus.height * 100}%` : '100%',
              }}
            >
              <span className="text-xs text-black font-bold bg-yellow-400 px-1 rounded shadow">
                🎯 FOCUS: {focus.target_type}
              </span>
            </div>
          ))}
        </div>

        {/* Info Panels */}
        <div className="flex flex-col gap-4 max-h-[60vh] overflow-y-auto">
          <div className="p-4 border rounded shadow-sm">
            <h3 className="font-bold text-lg text-blue-600">Current Layout</h3>
            {currentLayout ? (
              <p>{currentLayout.layout_name}</p>
            ) : (
              <p className="text-gray-500">No layout detected</p>
            )}
          </div>

          <div className="p-4 border rounded shadow-sm">
            <h3 className="font-bold text-lg text-green-600">Active Focus</h3>
            {activeFocus.length > 0 ? (
              <ul className="list-disc pl-5">
                {activeFocus.map(f => (
                  <li key={f.id}>{f.target_type} ({f.evidence_summary})</li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">None</p>
            )}
          </div>

          <div className="p-4 border rounded shadow-sm">
            <h3 className="font-bold text-lg text-red-600">Events</h3>
            <ul className="text-sm flex flex-col gap-2">
              {events.map(ev => (
                <li key={ev.id} className={currentTime >= ev.start_time && currentTime <= ev.end_time ? 'font-bold bg-yellow-100 p-1 rounded' : ''}>
                  <span className="text-gray-500 w-24 inline-block">[{ev.start_time.toFixed(1)}s - {ev.end_time.toFixed(1)}s]</span> 
                  {ev.event_type} - {ev.description}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
