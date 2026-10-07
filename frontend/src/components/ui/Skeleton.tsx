import React from "react";
import { cn } from "@/lib/utils";

function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-slate-800/60", className)}
      {...props}
    />
  );
}

export function SkeletonStatCard() {
  return (
    <div className="bg-slate-900/70 border border-slate-800/80 rounded-xl p-5 space-y-3">
      <Skeleton className="h-3.5 w-24" />
      <Skeleton className="h-7 w-16" />
      <Skeleton className="h-2.5 w-32" />
    </div>
  );
}

export function SkeletonDocumentRow() {
  return (
    <div className="flex items-center gap-4 py-3 px-4 border-b border-slate-800/60">
      <Skeleton className="h-8 w-8 rounded-lg shrink-0" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-3.5 w-48" />
        <Skeleton className="h-2.5 w-32" />
      </div>
      <Skeleton className="h-5 w-16 rounded-md" />
      <Skeleton className="h-5 w-20 rounded-md" />
    </div>
  );
}

export function SkeletonChatMessage({ align = "right" }: { align?: "left" | "right" }) {
  return (
    <div className={cn("flex gap-3", align === "right" ? "justify-end" : "justify-start")}>
      {align === "left" && <Skeleton className="h-8 w-8 rounded-full shrink-0" />}
      <div className="space-y-2 max-w-sm w-full">
        <Skeleton className="h-3.5 w-full" />
        <Skeleton className="h-3.5 w-4/5" />
        <Skeleton className="h-3.5 w-3/5" />
      </div>
    </div>
  );
}

export { Skeleton };

