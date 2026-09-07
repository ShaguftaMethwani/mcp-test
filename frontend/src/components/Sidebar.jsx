import React from 'react';

export default function Sidebar({ mcpStatus }) {
  return (
    <aside className="fixed left-0 top-0 h-screen w-60 flex-col justify-between p-stack-md z-40 border-r border-outline-variant/20 bg-surface-container-lowest hidden lg:flex select-none">
      <div className="flex flex-col gap-y-4">
        {/* Organization / Header Area */}
        <div className="flex items-center gap-3 px-2 py-2 rounded-lg bg-surface-container-low/40 border border-outline-variant/20">
          <div className="w-8 h-8 rounded-md bg-gradient-to-tr from-secondary-container to-primary-container flex items-center justify-center text-white shadow-sm font-headline-md text-headline-md">
            <span className="material-symbols-outlined text-[18px]">hub</span>
          </div>
          <div className="flex flex-col min-w-0">
            <span className="font-headline-md text-body-md font-semibold text-on-surface truncate">Enterprise Intelligence</span>
            <span className="font-code-sm text-code-sm text-outline truncate">Production Pipeline v2.4</span>
          </div>
        </div>

        {/* Quick Action CTA */}
        <button className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-surface-container-high hover:bg-surface-variant text-primary border border-outline-variant/30 rounded-md font-label-md text-label-md transition-all duration-150 active:scale-[0.98]">
          <span className="material-symbols-outlined text-[16px]">bolt</span>
          <span>Trigger Ingestion</span>
        </button>

        {/* Navigation Tabs */}
        <nav className="flex flex-col gap-1 mt-1">
          <a className="flex items-center gap-3 px-3 py-2 text-on-surface-variant hover:text-on-surface rounded-lg font-label-md hover:bg-surface-container transition-all duration-150" href="#overview">
            <span className="material-symbols-outlined text-[18px]">hub</span>
            <span>Pipeline Overview</span>
          </a>
          <a className="flex items-center gap-3 px-3 py-2 text-on-surface-variant hover:text-on-surface rounded-lg font-label-md hover:bg-surface-container transition-all duration-150" href="#clustering">
            <span className="material-symbols-outlined text-[18px]">insights</span>
            <span>Signal Clustering</span>
          </a>
          {/* ACTIVE TAB */}
          <a className="flex items-center gap-3 px-3 py-2 bg-surface-container-high text-primary rounded-lg font-headline-md border-l-2 border-primary transition-all duration-150" href="#pulses">
            <span className="material-symbols-outlined text-[18px]">auto_graph</span>
            <span className="font-medium text-body-md">Weekly Pulses</span>
          </a>
          <a className="flex items-center gap-3 px-3 py-2 text-on-surface-variant hover:text-on-surface rounded-lg font-label-md hover:bg-surface-container transition-all duration-150" href="#mcp">
            <span className="material-symbols-outlined text-[18px]">integration_instructions</span>
            <span>MCP Toolchains</span>
          </a>
          <a className="flex items-center gap-3 px-3 py-2 text-on-surface-variant hover:text-on-surface rounded-lg font-label-md hover:bg-surface-container transition-all duration-150" href="#audits">
            <span className="material-symbols-outlined text-[18px]">verified_user</span>
            <span>Audit Logs</span>
          </a>
        </nav>
      </div>

      {/* Footer System Status & Workspace Config */}
      <div className="flex flex-col gap-1 pt-3 border-t border-outline-variant/20">
        <div className="flex items-center justify-between px-3 py-2 text-on-surface-variant hover:text-on-surface rounded-lg font-label-md hover:bg-surface-container transition-all">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[17px]">dns</span>
            <span className="text-body-sm font-body-sm">MCP Gateway Status</span>
          </div>
          {mcpStatus === 'approved' ? (
             <span className="w-2 h-2 rounded-full bg-tertiary"></span>
          ) : mcpStatus === 'error' ? (
             <span className="w-2 h-2 rounded-full bg-error"></span>
          ) : (
             <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
          )}
        </div>
        <a className="flex items-center gap-3 px-3 py-2 text-on-surface-variant hover:text-on-surface rounded-lg font-label-md hover:bg-surface-container transition-all" href="#settings">
          <span className="material-symbols-outlined text-[17px]">settings</span>
          <span className="text-body-sm font-body-sm">Workspace Settings</span>
        </a>
      </div>
    </aside>
  );
}
