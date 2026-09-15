"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { PageLoader } from "@/components/ui/Loading";
import { Badge } from "@/components/ui/Badge";

export default function EditPlanPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const router = useRouter();

  const [runs, setRuns] = useState<any[]>([]);
  const [plans, setPlans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  // Form state
  const [targetDuration, setTargetDuration] = useState("9000");
  const [tolerance, setTolerance] = useState("900");
  const [profile, setProfile] = useState("balanced");
  const [provider, setProvider] = useState("mock");

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [id]);

  async function fetchData() {
    try {
      const [runsRes, plansRes] = await Promise.all([
        fetch(`http://127.0.0.1:8000/api/v1/projects/${id}/edit-plan/runs`),
        fetch(`http://127.0.0.1:8000/api/v1/projects/${id}/edit-plan/plans`)
      ]);
      
      if (runsRes.ok) setRuns(await runsRes.json());
      if (plansRes.ok) setPlans(await plansRes.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function generatePlan(e: React.FormEvent) {
    e.preventDefault();
    setGenerating(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/projects/${id}/edit-plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_duration_seconds: parseFloat(targetDuration),
          tolerance_seconds: parseFloat(tolerance),
          profile: profile,
          provider: provider
        })
      });
      if (res.ok) {
        fetchData();
      } else {
        alert("Failed to start generation");
      }
    } catch (err) {
      alert("Error starting generation");
    } finally {
      setGenerating(false);
    }
  }

  if (loading) return <PageLoader />;

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-1 container mx-auto py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Edit Plans</h1>
            <p className="text-muted-foreground mt-2">
              Generate and review AI editorial plans for this video.
            </p>
          </div>
          <Link
            href={`/projects/${id}`}
            className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80"
          >
            Back to Project
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="md:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Generate Edit Plan</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={generatePlan} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Target Duration (s)</label>
                    <input 
                      type="number" 
                      value={targetDuration}
                      onChange={e => setTargetDuration(e.target.value)}
                      className="w-full bg-surface-base border border-surface-border rounded-md px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Tolerance (s)</label>
                    <input 
                      type="number" 
                      value={tolerance}
                      onChange={e => setTolerance(e.target.value)}
                      className="w-full bg-surface-base border border-surface-border rounded-md px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Profile</label>
                    <select 
                      value={profile} 
                      onChange={e => setProfile(e.target.value)}
                      className="w-full bg-surface-base border border-surface-border rounded-md px-3 py-2"
                    >
                      <option value="compact">Compact (Fast paced, dense)</option>
                      <option value="balanced">Balanced (Standard)</option>
                      <option value="comprehensive">Comprehensive (Keep context)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">AI Provider</label>
                    <select 
                      value={provider} 
                      onChange={e => setProvider(e.target.value)}
                      className="w-full bg-surface-base border border-surface-border rounded-md px-3 py-2"
                    >
                      <option value="mock">Mock (Fast deterministic tests)</option>
                      <option value="gemini">Gemini Pro (Actual AI)</option>
                    </select>
                  </div>
                  <Button type="submit" className="w-full" disabled={generating}>
                    {generating ? "Queuing..." : "Generate Plan"}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>

          <div className="md:col-span-2 space-y-8">
            <div>
              <h2 className="text-xl font-bold mb-4">Completed Plans</h2>
              {plans.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground border border-dashed border-surface-border rounded-lg">
                  No edit plans generated yet.
                </div>
              ) : (
                <div className="space-y-4">
                  {plans.map(plan => (
                    <Card key={plan.id}>
                      <CardContent className="p-4 flex justify-between items-center">
                        <div>
                          <p className="font-medium">Plan {plan.id.substring(0, 8)}</p>
                          <div className="text-sm text-muted-foreground mt-1 space-x-4">
                            <span>Clips: {plan.clip_count}</span>
                            <span>Selected: {Math.round(plan.selected_duration)}s</span>
                            <span>Ratio: {(plan.selected_duration / plan.original_duration * 100).toFixed(1)}%</span>
                          </div>
                        </div>
                        <Link href={`/projects/${id}/edit-plan/${plan.id}`}>
                          <Button>View Rough Cut</Button>
                        </Link>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>

            <div>
              <h2 className="text-xl font-bold mb-4">Recent Runs</h2>
              {runs.length === 0 ? (
                <p className="text-sm text-muted-foreground">No runs started.</p>
              ) : (
                <div className="space-y-2">
                  {runs.map(run => (
                    <div key={run.id} className="flex justify-between items-center p-3 border border-surface-border rounded-md bg-surface-elevated text-sm">
                      <div>
                        <span className="font-medium mr-2">{run.id.substring(0, 8)}</span>
                        <span className="text-muted-foreground">{run.profile} (T:{run.target_duration_seconds}s)</span>
                      </div>
                      <Badge variant={
                        run.status === "completed" ? "success" : 
                        run.status === "failed" ? "destructive" : 
                        "default"
                      }>
                        {run.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
