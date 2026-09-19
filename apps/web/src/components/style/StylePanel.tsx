'use client';

import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Activity, AlertTriangle, FileCheck, Layers, Settings, Eye } from 'lucide-react';

export const StylePanel = ({ projectId }: { projectId: string }) => {
  const [policy, setPolicy] = useState<any>(null);
  const [provenance, setProvenance] = useState<any[]>([]);
  const [impact, setImpact] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock fetch data for UI validation
    setLoading(false);
    setPolicy({
      id: 'mock-policy-123',
      name: 'Dynamic Gameplay Edit',
      policy_version: 2,
      status: 'active',
      experimental: true,
      signals: [
        { name: 'reaction_retention', direction: 'increase', strength: 0.9 },
        { name: 'pacing_cuts', direction: 'increase', strength: 0.8 },
      ]
    });
    setProvenance([
      { id: 'run-1', status: 'completed', completed_at: new Date().toISOString() },
      { id: 'run-2', status: 'failed', completed_at: new Date().toISOString() }
    ]);
  }, [projectId]);

  const handleDryRun = () => {
    // call /impact endpoint
    setImpact({
      metrics: [
        { name: 'Avg Clip Duration', default_value: 8.5, styled_value: 6.2, unit: 's' },
        { name: 'Cuts per Minute', default_value: 7.0, styled_value: 9.6, unit: 'cuts' }
      ]
    });
  };

  if (loading) return <div>Loading style...</div>;
  if (!policy) return <Card className="p-4"><p>No style applied</p></Card>;

  return (
    <div className="flex flex-col gap-6 p-4 max-w-4xl mx-auto">
      <Card className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Layers className="w-6 h-6 text-indigo-500" />
              {policy.name}
            </h2>
            <div className="flex gap-2 mt-2">
              <Badge variant="outline">v{policy.policy_version}</Badge>
              <Badge variant={policy.status === 'active' ? 'default' : 'info'}>
                {policy.status}
              </Badge>
              {policy.experimental && (
                <Badge variant="error" className="flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  Experimental Style
                </Badge>
              )}
            </div>
          </div>
          <Button variant="outline" onClick={handleDryRun}>
            <Eye className="w-4 h-4 mr-2" />
            Dry Run (Impact)
          </Button>
        </div>

        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <Activity className="w-5 h-5 text-green-500" />
            Signal Explainability
          </h3>
          <div className="bg-slate-50 dark:bg-slate-900 rounded-md p-4 space-y-2">
            {policy.signals.map((sig: any, idx: number) => (
              <div key={idx} className="flex justify-between items-center text-sm border-b border-slate-200 dark:border-slate-800 pb-2 last:border-0 last:pb-0">
                <span className="font-medium text-slate-700 dark:text-slate-300">{sig.name}</span>
                <div className="flex items-center gap-4">
                  <span className={`text-xs px-2 py-1 rounded ${sig.direction === 'increase' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {sig.direction.toUpperCase()}
                  </span>
                  <span className="text-slate-500">{(sig.strength * 100).toFixed(0)}% strength</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {impact && (
          <div className="mt-6 p-4 border border-indigo-200 bg-indigo-50 dark:bg-indigo-900/20 dark:border-indigo-800 rounded-md">
            <h3 className="font-semibold text-indigo-800 dark:text-indigo-300 mb-2">A/B Impact Difference (Dry Run)</h3>
            <div className="grid grid-cols-2 gap-4">
              {impact.metrics.map((m: any, i: number) => (
                <div key={i} className="bg-white dark:bg-slate-800 p-3 rounded shadow-sm flex justify-between">
                  <span className="text-sm text-slate-500">{m.name}</span>
                  <div className="flex gap-2 text-sm font-medium">
                    <span className="line-through text-slate-400">{m.default_value}</span>
                    <span className="text-indigo-600 dark:text-indigo-400">{m.styled_value}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <FileCheck className="w-5 h-5 text-blue-500" />
          Style Provenance
        </h3>
        <div className="space-y-3">
          {provenance.map((prov, i) => (
            <div key={prov.id} className="flex justify-between items-center bg-slate-50 dark:bg-slate-900 p-3 rounded-md border border-slate-100 dark:border-slate-800 text-sm">
              <div>
                <span className="font-medium">Run {prov.id.substring(0,8)}</span>
                <span className="text-slate-400 ml-2 text-xs">{new Date(prov.completed_at).toLocaleString()}</span>
              </div>
              <Badge variant={prov.status === 'completed' ? 'default' : 'error'}>
                {prov.status}
              </Badge>
            </div>
          ))}
          {provenance.length === 0 && <p className="text-sm text-slate-500">No application history found.</p>}
        </div>
      </Card>
    </div>
  );
};

export default StylePanel;
