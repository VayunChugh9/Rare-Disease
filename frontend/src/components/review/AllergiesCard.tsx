import { Check } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import type { Allergies } from "../../types/referral";

export function AllergiesCard({ allergies }: { allergies?: Allergies }) {
  return (
    <Card>
      <CardHeader><CardTitle>Allergies</CardTitle></CardHeader>
      <CardContent>
        {allergies?.no_known_allergies ? (
          <div className="flex items-center gap-2 bg-[#0D9488]/10 text-[#0D9488] px-4 py-2 rounded-xl text-sm font-bold">
            <Check className="h-4 w-4" /> No known allergies
          </div>
        ) : allergies?.known_allergies && allergies.known_allergies.length > 0 ? (
          <div className="space-y-2">
            {allergies.known_allergies.map((allergy, i) => (
              <div key={i} className="text-sm">
                <span className="font-semibold text-[#0F172A]">{allergy.substance}</span>
                {allergy.reaction && <span className="text-[#64748B] ml-2">— {allergy.reaction}</span>}
                {allergy.severity && <span className="ml-2 text-[10px] font-bold uppercase text-[#DC2626]">{allergy.severity}</span>}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm italic text-[#64748B]">No allergy information available</p>
        )}
      </CardContent>
    </Card>
  );
}
