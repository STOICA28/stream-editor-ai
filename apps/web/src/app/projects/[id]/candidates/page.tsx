import Link from "next/link";
import { Suspense } from "react";
import { notFound } from "next/navigation";
import { formatDuration } from "@/lib/utils";

export const metadata = {
  title: "Candidate Fragments | StreamEditor AI",
};

async function getCandidateRuns(projectId: string) {
  try {
    const res = await fetch(`http://127.0.0.1:8000/api/projects/${projectId}/candidate-runs`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return res.json();
  } catch (error) {
    console.error("Failed to fetch candidate runs:", error);
    return [];
  }
}

async function getCandidates(runId: string) {
  try {
    const res = await fetch(`http://127.0.0.1:8000/api/candidate-runs/${runId}/candidates`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data.items || [];
  } catch (error) {
    console.error("Failed to fetch candidates:", error);
    return [];
  }
}

export default async function CandidatesPage({ params }: { params: { id: string } }) {
  const runs = await getCandidateRuns(params.id);
  const latestRun = runs.length > 0 ? runs[0] : null;
  const candidates = latestRun ? await getCandidates(latestRun.id) : [];

  return (
    <div className="container mx-auto py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Candidate Fragments</h1>
          <p className="text-muted-foreground mt-2">
            AI-generated potential highlights from your project.
          </p>
        </div>
        <div className="flex gap-4">
          <Link
            href={`/projects/${params.id}`}
            className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80"
          >
            Back to Project
          </Link>
          <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
            Generate Candidates
          </button>
        </div>
      </div>

      {!latestRun ? (
        <div className="border border-dashed rounded-lg p-12 text-center text-muted-foreground">
          No candidate runs found for this project. Click &quot;Generate Candidates&quot; to start.
        </div>
      ) : (
        <div className="space-y-6">
          <div className="p-4 border rounded-md bg-muted/20 flex gap-8 items-center">
            <div>
              <span className="text-xs text-muted-foreground uppercase font-semibold">Latest Run Status</span>
              <div className="font-medium mt-1">{latestRun.status}</div>
            </div>
            <div>
              <span className="text-xs text-muted-foreground uppercase font-semibold">Candidates Found</span>
              <div className="font-medium mt-1">{latestRun.candidate_count || 0}</div>
            </div>
            <div>
              <span className="text-xs text-muted-foreground uppercase font-semibold">Provider</span>
              <div className="font-medium mt-1">{latestRun.provider}</div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {candidates.map((cand: any) => (
              <div key={cand.id} className="border rounded-lg p-5 flex flex-col gap-4 bg-card">
                <div className="flex justify-between items-start">
                  <div className="font-semibold text-lg">{formatDuration(cand.end_time - cand.start_time)}s clip</div>
                  <div className={`px-2 py-1 rounded text-xs font-semibold ${
                    cand.debug_label === 'interesting' ? 'bg-green-100 text-green-800' :
                    cand.debug_label === 'uncertain' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {cand.debug_label || "unknown"}
                  </div>
                </div>

                <div className="text-sm text-muted-foreground line-clamp-3">
                  {cand.summary || cand.transcript_excerpt || "No summary available."}
                </div>

                <div className="mt-auto pt-4 border-t grid grid-cols-3 gap-2 text-center text-sm">
                  <div>
                    <div className="text-xs text-muted-foreground">Humor</div>
                    <div className="font-medium">{cand.score_humor?.toFixed(2) || "-"}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Importance</div>
                    <div className="font-medium">{cand.score_importance?.toFixed(2) || "-"}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Rank</div>
                    <div className="font-medium">{cand.experimental_rank?.toFixed(2) || "-"}</div>
                  </div>
                </div>
              </div>
            ))}
            
            {candidates.length === 0 && latestRun.status === 'completed' && (
              <div className="col-span-full p-8 text-center border border-dashed rounded-lg text-muted-foreground">
                No candidates matched the criteria in this run.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
