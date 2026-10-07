import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Library,
  MessageSquare,
  Search,
  BarChart3,
  Zap,
  ChevronRight,
  FlaskConical,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  to: string;
  badge?: string;
}

const navigation: NavItem[] = [
  { label: "Dashboard", icon: LayoutDashboard, to: "/" },
  { label: "Knowledge Base", icon: Library, to: "/knowledge" },
  { label: "AI Chat", icon: MessageSquare, to: "/chat" },
  { label: "Search", icon: Search, to: "/search" },
  { label: "Analytics", icon: BarChart3, to: "/analytics" },
  { label: "Evaluation", icon: FlaskConical, to: "/evaluation" },
];

export function Sidebar() {
  return (
    <aside className="w-60 shrink-0 bg-slate-950/80 border-r border-slate-800/70 flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-slate-800/70">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-900/40 shrink-0">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <div>
            <span className="text-sm font-bold text-slate-100 tracking-tight">NexusRAG</span>
            <p className="text-[10px] text-slate-500 leading-tight">Agentic Knowledge Platform</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-0.5 overflow-y-auto">
        {navigation.map(({ label, icon: Icon, to, badge }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium",
                "transition-all duration-150 relative",
                isActive
                  ? "bg-indigo-600/20 text-indigo-300 border border-indigo-600/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent"
              )
            }
          >
            {({ isActive }) => (
              <>
                <Icon className={cn("w-4 h-4 shrink-0", isActive ? "text-indigo-400" : "")} />
                <span className="flex-1 truncate">{label}</span>
                {badge && (
                  <span className="ml-auto text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-indigo-600/30 text-indigo-300">
                    {badge}
                  </span>
                )}
                {isActive && (
                  <ChevronRight className="w-3 h-3 text-indigo-400/60 ml-auto shrink-0" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-slate-800/70">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-slate-700 to-slate-600 flex items-center justify-center text-xs font-bold text-slate-200 shrink-0">
            AI
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-slate-300 truncate">AI Engineer Demo</p>
            <p className="text-[10px] text-slate-500">DecisionOpt Application</p>
          </div>
        </div>
      </div>
    </aside>
  );
}

