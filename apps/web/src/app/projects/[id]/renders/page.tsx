"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface RenderJob {
  id: string;
  status: string;
  progress: number;
  error_message: string | null;
  output_asset_id: string | null;
  created_at: string;
}

export default function RendersPage() {
  const params = useParams();
  const projectId = params.id as string;
  
  const [renders, setRenders] = useState<RenderJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRenders();
    const interval = setInterval(fetchRenders, 3000);
    return () => clearInterval(interval);
  }, [projectId]);

  const fetchRenders = async () => {
    try {
      const res = await fetch(`/api/v1/projects/${projectId}/renders`);
      const data = await res.json();
      setRenders(data);
    } catch (e) {
      console.error("Failed to fetch renders", e);
    } finally {
      setLoading(false);
    }
  };

  const cancelRender = async (id: string) => {
    await fetch(`/api/v1/renders/${id}/cancel`, { method: "POST" });
    fetchRenders();
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">Renders</h1>
        <Link 
          href={`/projects/${projectId}`}
          className="text-blue-500 hover:underline"
        >
          Back to Project
        </Link>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <div className="space-y-4">
          {renders.length === 0 && <p className="text-gray-500">No renders found.</p>}
          {renders.map((job) => (
            <div key={job.id} className="border p-6 rounded-lg bg-white shadow-sm">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-semibold text-lg">Job: {job.id}</h3>
                  <p className="text-sm text-gray-500">Started: {new Date(job.created_at).toLocaleString()}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  job.status === 'completed' ? 'bg-green-100 text-green-800' :
                  job.status === 'failed' ? 'bg-red-100 text-red-800' :
                  job.status === 'cancelled' ? 'bg-gray-100 text-gray-800' :
                  'bg-blue-100 text-blue-800'
                }`}>
                  {job.status.toUpperCase()}
                </span>
              </div>
              
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-1">
                  <span>Progress</span>
                  <span>{job.progress.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-500" 
                    style={{ width: `${job.progress}%` }}
                  />
                </div>
              </div>

              {job.error_message && (
                <div className="p-3 bg-red-50 text-red-700 text-sm rounded mb-4">
                  {job.error_message}
                </div>
              )}

              <div className="flex gap-2">
                {['pending', 'preparing', 'rendering'].includes(job.status) && (
                  <button
                    onClick={() => cancelRender(job.id)}
                    className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
                  >
                    Cancel
                  </button>
                )}
                {job.status === 'completed' && job.output_asset_id && (
                  <Link
                    href={`/api/v1/media/${job.output_asset_id}/download`}
                    className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
                    target="_blank"
                  >
                    Download Output
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
