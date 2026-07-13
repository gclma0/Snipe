import { DeterministicScoreResult } from "@/lib/api";

export function JobField({ label, values }: { label: string; values: string[] }) {
  return (
    <div>
      <dt className="font-medium">{label}</dt>
      <dd className="mt-1 text-muted-foreground">{values.length ? values.join(", ") : "Not found"}</dd>
    </div>
  );
}

export function MessageBlock({ title, value }: { title: string; value: string }) {
  return (
    <div className="border border-border p-3">
      <p className="font-medium">{title}</p>
      <pre className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">{value}</pre>
    </div>
  );
}

export function ScoreCard({ title, result }: { title: string; result: DeterministicScoreResult }) {
  const topFinding = result.findings[0];

  return (
    <div className="border border-border p-3">
      <p className="font-medium">{title}</p>
      <p className="mt-2 text-2xl font-semibold">{result.score}</p>
      {topFinding ? (
        <p className="mt-2 text-muted-foreground">{topFinding.recommendation}</p>
      ) : (
        <p className="mt-2 text-muted-foreground">No major readiness issues found.</p>
      )}
    </div>
  );
}
