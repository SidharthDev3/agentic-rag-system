import React from "react";
import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "success" | "warning" | "error" | "info" | "outline";
  size?: "sm" | "md";
}

const variantClasses = {
  default: "bg-slate-800 text-slate-300 border-slate-700",
  success: "bg-emerald-950/60 text-emerald-400 border-emerald-800/60",
  warning: "bg-amber-950/60 text-amber-400 border-amber-800/60",
  error: "bg-red-950/60 text-red-400 border-red-800/60",
  info: "bg-indigo-950/60 text-indigo-400 border-indigo-800/60",
  outline: "bg-transparent text-slate-400 border-slate-700",
};

const sizeClasses = {
  sm: "text-xs px-1.5 py-0.5 gap-1",
  md: "text-xs px-2 py-0.5 gap-1.5",
};

export function Badge({ variant = "default", size = "md", className, children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center font-medium rounded-md border",
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}

