"use client";
import React, { useEffect, useMemo, useState } from "react";

type KPI = {
  turns: number;
  rebuttal_success_rate: number;
  ng_rate: number;
  silence_ratio: number;
};

export default function MetricsPage() {
  const [kpi, setKpi] = useState<KPI | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
    fetch(`${base}/api/metrics/overview?tenant=demo`)
      .then((r) => r.json())
      .then((data) => {
        setKpi(data.kpi);
        setLoading(false);
      })
      .catch((e) => {
        setError(String(e));
        setLoading(false);
      });
  }, []);

  const heat = useMemo(() => {
    if (!kpi) return 0;
    // 簡易スコア: 反論成功高 + NG低 + 沈黙低
    const score = kpi.rebuttal_success_rate * 100 - kpi.ng_rate * 100 - kpi.silence_ratio * 100;
    // Normalize to 0-1
    return Math.max(0, Math.min(1, (score + 100) / 200));
  }, [kpi]);

  if (loading) return <div className="p-6">Loading metrics...</div>;
  if (error) return <div className="p-6 text-red-600">Error: {error}</div>;
  if (!kpi) return <div className="p-6">No data</div>;

  const color = `hsl(${Math.round(heat * 120)}, 70%, 50%)`; // red->green

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-semibold">Metrics Overview</h2>
      <div className="grid grid-cols-2 gap-4 max-w-xl">
        <Metric label="Turns" value={kpi.turns} />
        <Metric label="Rebuttal Success" value={(kpi.rebuttal_success_rate * 100).toFixed(1) + "%"} />
        <Metric label="NG Rate" value={(kpi.ng_rate * 100).toFixed(1) + "%"} />
        <Metric label="Silence Ratio" value={(kpi.silence_ratio * 100).toFixed(1) + "%"} />
      </div>

      <div>
        <h3 className="font-medium mb-2">NG率・反論成功率ヒートマップ（簡易）</h3>
        <div className="w-64 h-16 rounded" style={{ background: color }} data-testid="heatmap" />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="border rounded p-3">
      <div className="text-sm text-gray-600">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}


