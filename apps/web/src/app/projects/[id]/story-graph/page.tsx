import Link from "next/link";

export const metadata = {
  title: "Story Graph | StreamEditor AI",
};

async function getStoryGraphRuns(projectId: string) {
  try {
    const res = await fetch(`http://127.0.0.1:8000/api/v1/projects/${projectId}/story-graph/runs`, {
      cache: "no-store",
    });
    if (!res.ok) return [];
    return res.json();
  } catch (error) {
    console.error("Failed to fetch story graph runs:", error);
    return [];
  }
}

export default async function StoryGraphPage({ params }: { params: { id: string } }) {
  const runs = await getStoryGraphRuns(params.id);
  const latestRun = runs.length > 0 ? runs[0] : null;

  return (
    <div className="container mx-auto py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Story Graph</h1>
          <p className="text-muted-foreground mt-2">
            Narrative relationships and callbacks extracted from your project.
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
            Generate Story Graph
          </button>
        </div>
      </div>

      {!latestRun ? (
        <div className="border border-dashed rounded-lg p-12 text-center text-muted-foreground">
          No Story Graph runs found for this project. Click &quot;Generate Story Graph&quot; to start.
        </div>
      ) : (
        <div className="space-y-6">
          <div className="p-4 border rounded-md bg-muted/20 flex gap-8 items-center">
            <div>
              <span className="text-xs text-muted-foreground uppercase font-semibold">Latest Run Status</span>
              <div className="font-medium mt-1">{latestRun.status}</div>
            </div>
            <div>
              <span className="text-xs text-muted-foreground uppercase font-semibold">Nodes</span>
              <div className="font-medium mt-1">{latestRun.node_count || 0}</div>
            </div>
            <div>
              <span className="text-xs text-muted-foreground uppercase font-semibold">Edges</span>
              <div className="font-medium mt-1">{latestRun.edge_count || 0}</div>
            </div>
            <div>
              <span className="text-xs text-muted-foreground uppercase font-semibold">Threads</span>
              <div className="font-medium mt-1">{latestRun.thread_count || 0}</div>
            </div>
            <div>
              <span className="text-xs text-muted-foreground uppercase font-semibold">Provider</span>
              <div className="font-medium mt-1">{latestRun.provider}</div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
             <div className="p-8 text-center border border-dashed rounded-lg text-muted-foreground col-span-full">
                Interactive Graph Visualization is coming soon.
             </div>
          </div>
        </div>
      )}
    </div>
  );
}
