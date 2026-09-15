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
  const router = useRouter();
  
  const [plan, setPlan] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showRejected, setShowRejected] = useState(false);

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

  async function handleCreateRevision() {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/projects/${id}/edit-plan/plans/${planId}/revisions`, {
        method: "POST"
      });
      if (res.ok) {
        const newPlan = await res.json();
        router.push(`/projects/${id}/edit-plan/${newPlan.id}`);
      } else {
        alert("Failed to create revision");
      }
    } catch (e) {
      console.error(e);
      alert("Error creating revision");
    }
  }

  async function handleFeedback(clipId: string, feedbackType: string, newValue?: any) {
    if (plan.origin === 'ai') {
      alert("Cannot edit AI plans directly. Please create a revision first.");
      return;
    }
    
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/projects/${id}/edit-plan/plans/${planId}/clips/${clipId}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          feedback_type: feedbackType,
          new_value: newValue,
          reason_category: "manual_edit",
          reason_text: "User requested change in UI"
        })
      });
      
      if (res.ok) {
        await fetchData();
      } else {
        const err = await res.json();
        alert(`Failed: ${err.detail || 'Unknown error'}`);
      }
    } catch (e) {
      console.error(e);
      alert("Error sending feedback");
    }
  }

  if (loading) return <PageLoader />;
  if (!plan) return <div className="p-8 text-center">Plan not found</div>;

  const displayClips = plan.clips.filter((c: any) => showRejected || c.review_state !== 'rejected');

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
        
        {plan.origin === 'ai' && (
          <div className="bg-amber-900/20 border border-amber-700/50 p-4 rounded-md mb-8 flex justify-between items-center">
            <div>
              <h3 className="text-amber-500 font-bold mb-1">Read-Only AI Plan</h3>
              <p className="text-sm text-amber-500/80">
                This is an original AI-generated plan and cannot be destructively modified. Create a revision to make edits.
              </p>
            </div>
            <Button onClick={handleCreateRevision} variant="default" className="bg-amber-600 hover:bg-amber-700 text-white">
              Create Revision
            </Button>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="md:col-span-1 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Plan Overview</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="text-sm text-muted-foreground">Origin</div>
                  <Badge variant={plan.origin === 'ai' ? 'default' : 'secondary'}>
                    {plan.origin.toUpperCase()} {plan.revision_number ? `(Rev ${plan.revision_number})` : ''}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Original Duration</div>
                  <div className="font-medium">{formatTime(plan.original_duration)}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Selected Duration</div>
                  <div className="font-medium">{formatTime(plan.selected_duration)}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Clips</div>
                  <div className="font-medium">{plan.clip_count}</div>
                </div>
                <div className="pt-4 border-t border-surface-border">
                  <label className="flex items-center gap-2 text-sm cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={showRejected} 
                      onChange={(e) => setShowRejected(e.target.checked)} 
                    />
                    Show Rejected Clips
                  </label>
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
                {displayClips.length === 0 ? (
                  <div className="text-center p-8 text-muted-foreground border border-dashed border-surface-border rounded">
                    No clips to display.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {displayClips.map((clip: any, index: number) => {
                      const isRejected = clip.review_state === 'rejected';
                      return (
                        <div key={clip.id} className={`flex gap-4 p-4 border border-surface-border rounded-md ${isRejected ? 'bg-red-900/10 opacity-75' : 'bg-surface-elevated'}`}>
                          <div className="flex-shrink-0 w-16 text-center font-bold text-lg text-muted-foreground">
                            {index + 1}
                          </div>
                          <div className="flex-1">
                            <div className="flex justify-between mb-2">
                              <span className={`font-medium ${isRejected ? 'line-through text-muted-foreground' : 'text-primary'}`}>
                                Output: {formatTime(clip.output_start)} - {formatTime(clip.output_end)}
                              </span>
                              <span className="text-sm text-muted-foreground">
                                Source: {formatTime(clip.source_start)} - {formatTime(clip.source_end)}
                              </span>
                            </div>
                            <p className="text-sm mb-2">{clip.selection_reason}</p>
                            
                            <div className="flex gap-2 items-center mb-2">
                              <Badge variant="outline">{clip.review_state}</Badge>
                              {clip.locked && <Badge variant="default" className="bg-blue-600">Locked</Badge>}
                              <Badge variant="outline">{clip.priority}</Badge>
                            </div>
                            
                            {plan.origin !== 'ai' && (
                              <div className="flex gap-2 items-center mt-4 pt-4 border-t border-surface-border">
                                {!isRejected && (
                                  <>
                                    <Button size="sm" variant="outline" onClick={() => handleFeedback(clip.id, 'modify_start', clip.source_start - 8)}>
                                      -8s Start
                                    </Button>
                                    <Button size="sm" variant="outline" onClick={() => handleFeedback(clip.id, 'modify_end', clip.source_end + 8)}>
                                      +8s End
                                    </Button>
                                    <Button size="sm" variant="secondary" onClick={() => handleFeedback(clip.id, 'lock', !clip.locked)}>
                                      {clip.locked ? 'Unlock' : 'Lock'}
                                    </Button>
                                  </>
                                )}
                                
                                {isRejected ? (
                                  <Button size="sm" variant="outline" onClick={() => handleFeedback(clip.id, 'accept')}>
                                    Restore (Accept)
                                  </Button>
                                ) : (
                                  <Button size="sm" variant="destructive" onClick={() => handleFeedback(clip.id, 'reject')}>
                                    Reject Clip
                                  </Button>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      )
                    })}
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
