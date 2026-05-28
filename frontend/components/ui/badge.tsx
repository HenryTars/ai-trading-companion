import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded px-1.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default: "bg-terminal-accent/20 text-terminal-accent border border-terminal-accent/30",
        bull: "bg-terminal-bull/20 text-terminal-bull border border-terminal-bull/30",
        bear: "bg-terminal-bear/20 text-terminal-bear border border-terminal-bear/30",
        warning: "bg-terminal-warning/20 text-terminal-warning border border-terminal-warning/30",
        muted: "bg-terminal-hover text-terminal-muted border border-terminal-border",
        outline: "border border-terminal-border text-terminal-text-secondary bg-transparent",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
