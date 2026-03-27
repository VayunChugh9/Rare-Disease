import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide transition-colors",
  {
    variants: {
      variant: {
        default: "bg-slate-100 text-slate-700",
        urgent: "bg-[#DC2626] text-white shadow-[0_0_12px_rgba(220,38,38,0.3)]",
        semi_urgent: "bg-[#EA580C] text-white shadow-[0_0_12px_rgba(234,88,12,0.3)]",
        routine: "bg-[#0D9488] text-white shadow-[0_0_12px_rgba(13,148,136,0.3)]",
        needs_clarification: "bg-[#CA8A04] text-white shadow-[0_0_12px_rgba(202,138,4,0.3)]",
        inappropriate: "bg-[#6B7280] text-white shadow-[0_0_12px_rgba(107,114,128,0.3)]",
        outline: "border border-current bg-transparent",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}
export { Badge, badgeVariants };
