import { StylePanel } from '@/components/style/StylePanel';

export default function StylePage({ params }: { params: { id: string } }) {
  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Editorial Style (M11)</h1>
      <StylePanel projectId={params.id} />
    </div>
  );
}
