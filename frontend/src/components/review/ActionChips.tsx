import { Send, CalendarPlus, Flag, FlaskConical, FileQuestion } from "lucide-react";

interface ActionChipsProps {
  items: string[];
}

type ActionCategory = {
  label: string;
  icon: React.ElementType;
  color: string;
  bg: string;
  border: string;
};

const CATEGORIES: ActionCategory[] = [
  { label: "Request Info from Referrer", icon: Send, color: "text-blue-700", bg: "bg-blue-50", border: "border-blue-200" },
  { label: "Schedule Appointment", icon: CalendarPlus, color: "text-teal-700", bg: "bg-teal-50", border: "border-teal-200" },
  { label: "Flag for Physician Review", icon: Flag, color: "text-amber-700", bg: "bg-amber-50", border: "border-amber-200" },
  { label: "Review Clinical Trial Eligibility", icon: FlaskConical, color: "text-purple-700", bg: "bg-purple-50", border: "border-purple-200" },
  { label: "Request Additional Records", icon: FileQuestion, color: "text-slate-700", bg: "bg-slate-50", border: "border-slate-200" },
];

function categorize(items: string[]): ActionCategory[] {
  const matched = new Set<number>();

  for (const item of items) {
    const lower = item.toLowerCase();
    if (/request.*(?:lab|med|info|record|a1c|result|document|metabolic).*(?:from|refer)/.test(lower) || /request.*(?:from|refer)/.test(lower)) {
      matched.add(0); // Request info
    }
    if (/schedul|appoint|within|evaluat/.test(lower)) {
      matched.add(1); // Schedule
    }
    if (/flag|physician|review|social|safety|concern|abuse|violen/.test(lower)) {
      matched.add(2); // Flag
    }
    if (/trial|eligib/.test(lower)) {
      matched.add(3); // Trials
    }
    if (/additional|record|missing|obtain/.test(lower)) {
      matched.add(4); // Additional records
    }
  }

  // Always include Request Info and Schedule if there are any items
  if (items.length > 0 && matched.size === 0) {
    matched.add(0);
    matched.add(1);
  }

  return Array.from(matched).sort().map((i) => CATEGORIES[i]);
}

export function ActionChips({ items }: ActionChipsProps) {
  if (items.length === 0) return null;

  const chips = categorize(items);

  return (
    <div className="flex gap-3 mx-6 mb-4 flex-wrap">
      {chips.map((chip, i) => {
        const Icon = chip.icon;
        return (
          <button
            key={i}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg border ${chip.border} ${chip.bg} ${chip.color} text-xs font-semibold hover:opacity-80 transition-all duration-150`}
          >
            <Icon className="h-3.5 w-3.5" />
            {chip.label}
          </button>
        );
      })}
    </div>
  );
}
