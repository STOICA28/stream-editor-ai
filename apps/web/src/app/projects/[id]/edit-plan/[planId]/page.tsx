"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { PageLoader } from "@/components/ui/Loading";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function RoughCutPage() {
  const params = useParams<{ id: string; planId: string }>();
  const { id, planId } = params;
  
  const [plan, setPlan] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/projects/${id}/edit-plan/plans/${planId}`);
      if (res.ok) {
        setPlan(await res.json());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id, planId]);

  async function handleDelete(clipId: string) {
    if (!confirm("Remove this clip from the edit plan?")) return;
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/projects/${id}/edit-plan/plans/${planId}/clips/${clipId}`, {
        method: "DELETE"
      });
      if (res.ok) {
        await fetchData();
      } else {
        alert("Failed to delete clip");
      }
    } catch (e) {
      alert("Error deleting clip");
    }
  }

  async function handleExtendStart(clipId: string, currentStart: number, amountSecs: number) {
    const newStart = Math.max(0, currentStart - amountSecs);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/projects/${id}/edit-plan/plans/${planId}/clips/${clipId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_start: newStart })
      });
      if (res.ok) {
        await fetchData();
      } else {
        alert("Failed to update clip boundaries");
      }
    } catch (e) {
      alert("Error updating clip boundaries");
    }
  }

  if (loading) return <PageLoader />;
  if (!plan) return <div className="p-8 text-center">Plan not found</div>;

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-1 container mx-auto py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Rough Cut / Human Review</h1>
            <p className="text-muted-foreground mt-2">
              Review and manually adjust the clips selected for Plan {plan.id.substring(0, 8)}
            </p>
          </div>
          <Link
            href={`/projects/${id}/edit-plan`}
            className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80"
          >
            Back to Plans
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="md:col-span-1 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Plan Overview</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="text-sm text-muted-foreground">Original Duration</div>
                  <div className="font-medium">{formatTime(plan.original_duration)}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Selected Duration</div>
                  <div className="font-medium">{formatTime(plan.selected_duration)}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Compression Ratio</div>
                  <div className="font-medium">{(plan.compression_ratio * 100).toFixed(1)}%</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Clips</div>
                  <div className="font-medium">{plan.clip_count}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Status</div>
                  <Badge variant={plan.status === 'completed' ? 'success' : 'default'}>
                    {plan.status}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="md:col-span-3">
            <Card>
              <CardHeader>
                <CardTitle>Timeline</CardTitle>
              </CardHeader>
              <CardContent>
                {plan.clips.length === 0 ? (
                  <div className="text-center p-8 text-muted-foreground border border-dashed border-surface-border rounded">
                    No clips in this plan.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {plan.clips.map((clip: any, index: number) => (
                      <div key={clip.id} className="flex gap-4 p-4 border border-surface-border rounded-md bg-surface-elevated">
                        <div className="flex-shrink-0 w-16 text-center font-bold text-lg text-muted-foreground">
                          {index + 1}
                        </div>
                        <div className="flex-1">
                          <div className="flex justify-between mb-2">
                            <span className="font-medium text-primary">
                              Output: {formatTime(clip.output_start)} - {formatTime(clip.output_end)}
                            </span>
                            <span className="text-sm text-muted-foreground">
                              Source: {formatTime(clip.source_start)} - {formatTime(clip.source_end)}
                            </span>
                          </div>
                          <p className="text-sm mb-2">{clip.selection_reason}</p>
                          <div className="flex gap-2 items-center mb-2">
                            <Badge variant="outline">{clip.priority} priority</Badge>
                            <Badge variant="outline">Conf: {clip.confidence?.toFixed(2) || '0.00'}</Badge>
                            {clip.locked && <Badge variant="default">Locked</Badge>}
                          </div>
                          
                          <div className="flex gap-2 items-center mt-4 pt-4 border-t border-surface-border">
                            <span className="text-xs font-medium mr-2">Quick Edits:</span>
                            <Button size="sm" variant="outline" onClick={() => handleExtendStart(clip.id, clip.source_start, 8)}>
                              + 8s (Start)
                            </Button>
                            <Button size="sm" variant="destructive" onClick={() => handleDelete(clip.id)}>
                              Cut / Remove
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
