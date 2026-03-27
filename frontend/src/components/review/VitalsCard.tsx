import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import type { RecentVitals } from "../../types/referral";

interface VitalsCardProps {
  vitals?: RecentVitals;
}

function isAbnormal(key: string, value: string): boolean {
  const num = parseFloat(value);
  if (isNaN(num)) return false;
  if (key === "bmi" && num > 30) return true;
  if (key === "heart_rate" && num > 100) return true;
  if (key === "blood_pressure") {
    const parts = value.split("/");
    if (parts.length === 2) {
      const sys = parseFloat(parts[0]);
      const dia = parseFloat(parts[1]);
      return sys > 140 || dia > 90;
    }
  }
  return false;
}

interface VitalTileProps {
  label: string;
  value: string;
  unit?: string;
  abnormal?: boolean;
  trend?: string;
  priorValue?: string;
}

function VitalTile({ label, value, unit, abnormal, trend, priorValue }: VitalTileProps) {
  return (
    <div className={`p-3 rounded-xl ${abnormal ? "bg-red-50/60 border border-red-200/30" : "bg-slate-50/50"}`}>
      <span className={`section-label block mb-1 ${abnormal ? "text-[#DC2626]/70" : ""}`}>{label}</span>
      <div className="flex items-baseline gap-2">
        <span className={`text-xl font-bold ${abnormal ? "text-[#DC2626]" : "text-[#0F172A]"}`}>{value}</span>
        {unit && <span className="text-xs text-[#64748B]">{unit}</span>}
        {trend && <span className={`text-xs font-bold ${abnormal ? "text-[#DC2626]" : "text-[#64748B]"}`}>{trend}</span>}
      </div>
      {priorValue && <span className="text-[10px] text-[#64748B]/60">Prev: {priorValue}</span>}
    </div>
  );
}

export function VitalsCard({ vitals }: VitalsCardProps) {
  if (!vitals) return null;

  const tiles: VitalTileProps[] = [];

  if (vitals.weight) {
    const weightTrend = vitals.trends?.weight_3_visits;
    tiles.push({
      label: "Weight",
      value: vitals.weight,
      unit: vitals.weight.includes("kg") ? "" : "kg",
      abnormal: false,
      trend: weightTrend && weightTrend.length > 1
        ? `${parseFloat(vitals.weight) > parseFloat(weightTrend[weightTrend.length - 2]) ? "↑" : "↓"} ${Math.abs(parseFloat(vitals.weight) - parseFloat(weightTrend[weightTrend.length - 2])).toFixed(1)}`
        : undefined,
      priorValue: weightTrend && weightTrend.length > 1 ? `${weightTrend[weightTrend.length - 2]} kg` : undefined,
    });
  }
  if (vitals.bmi) tiles.push({ label: "BMI", value: vitals.bmi, abnormal: isAbnormal("bmi", vitals.bmi) });
  if (vitals.heart_rate) tiles.push({ label: "Heart Rate", value: vitals.heart_rate, unit: "bpm", abnormal: isAbnormal("heart_rate", vitals.heart_rate) });
  if (vitals.blood_pressure) tiles.push({ label: "Blood Pressure", value: vitals.blood_pressure, unit: "mmHg", abnormal: isAbnormal("blood_pressure", vitals.blood_pressure) });
  if (vitals.respiratory_rate) tiles.push({ label: "Resp. Rate", value: vitals.respiratory_rate, unit: "/min" });
  if (vitals.height) tiles.push({ label: "Height", value: vitals.height });
  if (vitals.temperature) tiles.push({ label: "Temperature", value: vitals.temperature });
  if (vitals.pain_score) tiles.push({ label: "Pain Score", value: `${vitals.pain_score}/10` });
  if (vitals.oxygen_saturation) tiles.push({ label: "SpO2", value: vitals.oxygen_saturation, unit: "%" });

  if (tiles.length === 0) return null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <CardTitle>Recent Vitals</CardTitle>
        {vitals.date && <span className="text-[10px] uppercase font-bold text-[#64748B]">Updated {vitals.date}</span>}
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
          {tiles.map((tile, i) => <VitalTile key={i} {...tile} />)}
        </div>
      </CardContent>
    </Card>
  );
}
