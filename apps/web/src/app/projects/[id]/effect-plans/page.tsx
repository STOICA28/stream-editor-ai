'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';

export default function EffectPlansPage() {
  const { id: projectId } = useParams() as { id: string };
  const [editPlans, setEditPlans] = useState<any[]>([]);
  const [selectedEditPlan, setSelectedEditPlan] = useState<string>('');
  
  const [effectRuns, setEffectRuns] = useState<any[]>([]);
  const [selectedRun, setSelectedRun] = useState<string>('');
  const [instructions, setInstructions] = useState<any[]>([]);
  
  const [currentTime, setCurrentTime] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);

  // 1. Fetch Edit Plans (mocked or real)
  useEffect(() => {
    fetch(`/api/v1/projects/${projectId}/edit-plans`)
      .then(res => res.json())
      .then(data => {
        setEditPlans(data.runs || []);
        if (data.runs && data.runs.length > 0) {
          setSelectedEditPlan(data.runs[0].id);
        }
      });
  }, [projectId]);

  // 2. Fetch Effect Runs when Edit Plan selected
  useEffect(() => {
    if (!selectedEditPlan) return;
    fetch(`/api/v1/projects/${projectId}/edit-plans/${selectedEditPlan}/effects/runs`)
      .then(res => res.json())
      .then(data => {
        setEffectRuns(data.runs || []);
        if (data.runs && data.runs.length > 0) {
          loadEffectRun(data.runs[0].id);
        } else {
          setInstructions([]);
          setSelectedRun('');
        }
      });
  }, [selectedEditPlan, projectId]);

  const loadEffectRun = (runId: string) => {
    setSelectedRun(runId);
    fetch(`/api/v1/effect-plans/${runId}/effects`)
      .then(res => res.json())
      .then(setInstructions);
  };

  const startNewRun = () => {
    if (!selectedEditPlan) return;
    fetch(`/api/v1/projects/${projectId}/edit-plans/${selectedEditPlan}/effects/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario: "screen_to_face" })
    })
    .then(res => res.json())
    .then(data => {
      alert(`Started run: ${data.run_id}`);
      // Simple reload
      setTimeout(() => {
        fetch(`/api/v1/projects/${projectId}/edit-plans/${selectedEditPlan}/effects/runs`)
          .then(res => res.json())
          .then(d => setEffectRuns(d.runs || []));
      }, 1000);
    });
  };

  const activeEffects = instructions.filter(i => 
    currentTime >= i.source_start && currentTime <= i.source_end
  );

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">M8 - Effect Planning Debugger</h1>
      
      <div className="flex gap-8 mb-8">
        <div>
          <h2 className="text-xl font-semibold mb-2">Edit Plan</h2>
          <select 
            className="border p-2 rounded" 
            value={selectedEditPlan} 
            onChange={(e) => setSelectedEditPlan(e.target.value)}
          >
            <option value="">Select an Edit Plan</option>
            {editPlans.map(ep => (
              <option key={ep.id} value={ep.id}>{ep.id.split('-')[0]}</option>
            ))}
            {/* Dummy fallback if api doesn't return anything */}
            {editPlans.length === 0 && <option value="mock-plan">mock-plan-xxx</option>}
          </select>
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-2">Effect Plan Runs</h2>
          <div className="flex gap-2">
            {effectRuns.map(run => (
              <button 
                key={run.id}
                onClick={() => loadEffectRun(run.id)}
                className={`px-4 py-2 border rounded ${selectedRun === run.id ? 'bg-purple-600 text-white' : ''}`}
              >
                {run.id.split('-')[0]}
              </button>
            ))}
            <button 
              className="px-4 py-2 border rounded bg-green-600 text-white"
              onClick={startNewRun}
              disabled={!selectedEditPlan}
            >
              + Generate
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-8">
        {/* Video Player */}
        <div className="relative border rounded bg-black aspect-video overflow-hidden">
          <video 
            ref={videoRef}
            src="/synthetic_test.mp4" 
            controls 
            className="w-full h-full"
            onTimeUpdate={handleTimeUpdate}
          />
          
          {/* Overlays */}
          {activeEffects.map(eff => (
            <div 
              key={eff.id}
              className={`absolute border-4 pointer-events-none transition-all duration-300
                ${eff.effect_type === 'zoom_face' ? 'border-green-400' : 'border-blue-400'}`}
              style={{
                left: eff.x !== null ? `${eff.x * 100}%` : '0%',
                top: eff.y !== null ? `${eff.y * 100}%` : '0%',
                width: eff.width !== null ? `${eff.width * 100}%` : '100%',
                height: eff.height !== null ? `${eff.height * 100}%` : '100%',
                backgroundColor: eff.effect_type === 'grayscale' ? 'rgba(128,128,128,0.5)' : 'rgba(0,0,0,0)'
              }}
            >
              <div className="absolute top-0 left-0 bg-black/75 text-white text-xs px-2 py-1 font-bold">
                {eff.effect_type.toUpperCase()} ({eff.target_type})
              </div>
            </div>
          ))}
        </div>

        {/* Instructions Panel */}
        <div className="flex flex-col gap-4 max-h-[60vh] overflow-y-auto">
          <div className="p-4 border rounded shadow-sm bg-gray-50">
            <h3 className="font-bold text-lg text-purple-700">Instructions ({instructions.length})</h3>
            <ul className="text-sm flex flex-col gap-2 mt-2">
              {instructions.map(inst => {
                const isActive = currentTime >= inst.source_start && currentTime <= inst.source_end;
                return (
                  <li key={inst.id} className={`p-2 border rounded ${isActive ? 'border-purple-500 bg-purple-100' : 'bg-white'}`}>
                    <div className="font-bold text-md">{inst.effect_type}</div>
                    <div className="text-gray-500 text-xs">Time: {inst.source_start.toFixed(1)}s - {inst.source_end.toFixed(1)}s</div>
                    <div className="text-xs mt-1"><span className="font-semibold">Target:</span> {inst.target_type}</div>
                    <div className="text-xs"><span className="font-semibold">Reason:</span> {inst.reason}</div>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
