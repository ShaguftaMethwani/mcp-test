import React, { useState } from 'react';

export default function McpDispatcher({ status, mcpStatus, mcpResults, onApprove, onReject }) {
  const [isApproving, setIsApproving] = useState(false);

  const handleApprove = async () => {
    setIsApproving(true);
    await onApprove();
    setIsApproving(false);
  };

  if (status !== 'completed') {
    return (
      <section className="xl:col-span-4 flex flex-col gap-4 min-w-0 opacity-50 pointer-events-none">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-sm bg-amber-400"></span>
            <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">MCP Tool Dispatcher</h2>
          </div>
        </div>
        <div className="bg-surface-container-low border border-outline-variant/30 rounded-lg p-6 flex flex-col items-center justify-center shadow-sm text-outline h-64">
          <span className="material-symbols-outlined text-[32px] mb-2">gavel</span>
          <span className="font-code-sm">Awaiting Pipeline Completion...</span>
        </div>
      </section>
    );
  }

  return (
    <section className="xl:col-span-4 flex flex-col gap-4 min-w-0">
      {/* Panel Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-sm bg-amber-400"></span>
          <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">MCP Tool Dispatcher</h2>
        </div>
        <span className="px-2 py-0.5 rounded text-code-sm font-code-sm bg-amber-400/10 text-amber-300 border border-amber-400/30 flex items-center gap-1">
          <span className="material-symbols-outlined text-[13px]">gavel</span>
          {mcpStatus === 'approved' ? 'Approved & Executed' : mcpStatus === 'rejected' ? 'Rejected' : 'Human Gate Required'}
        </span>
      </div>

      {/* Security & Compliance Warning Banner */}
      {mcpStatus === 'pending' && (
        <div className="bg-surface-container-low border border-amber-400/30 rounded-lg p-3 flex items-start gap-2.5">
          <span className="material-symbols-outlined text-amber-400 text-[18px] shrink-0 mt-0.5">security</span>
          <div className="flex flex-col">
            <span className="font-label-md text-label-md text-amber-300 font-semibold">Simulated Execution Gate</span>
            <span className="text-body-sm font-body-sm text-on-surface-variant">MCP actions will only execute after explicit human review. No automated writes occur without operator sign-off.</span>
          </div>
        </div>
      )}

      {/* Action 1: Notion / Workspace Docs Block Push */}
      <div className="bg-surface-container-low border border-outline-variant/30 rounded-lg p-3.5 flex flex-col gap-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-surface-container-highest flex items-center justify-center text-primary font-bold text-code-sm">
              N
            </div>
            <div>
              <div className="font-headline-md text-body-md font-bold text-on-surface">Append to Notion Workspace</div>
              <div className="text-code-sm font-code-sm text-outline">Target: Product Intelligence / 2024 Weekly Pulses</div>
            </div>
          </div>
          <span className={`text-code-sm font-code-sm px-2 py-0.5 rounded ${mcpStatus === 'approved' ? 'bg-tertiary-container/30 text-tertiary border border-tertiary/20' : 'bg-surface-container-high text-outline border border-outline-variant/30'}`}>
            {mcpStatus === 'approved' ? 'Pushed' : 'Ready for Push'}
          </span>
        </div>
      </div>

      {/* Action 2: Gmail / Support Draft Generation */}
      <div className="bg-surface-container-low border border-outline-variant/30 rounded-lg p-3.5 flex flex-col gap-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-red-950/60 border border-red-500/30 flex items-center justify-center text-red-300 font-bold text-code-sm">
              M
            </div>
            <div>
              <div className="font-headline-md text-body-md font-bold text-on-surface">Create Gmail / Email Draft</div>
              <div className="text-code-sm font-code-sm text-outline">Target: Support Team & Product Leads</div>
            </div>
          </div>
          <span className={`text-code-sm font-code-sm px-2 py-0.5 rounded ${mcpStatus === 'approved' ? 'bg-tertiary/10 text-tertiary border border-tertiary/20' : 'bg-primary/10 text-primary border border-primary/20'}`}>
            {mcpStatus === 'approved' ? 'Draft Created' : 'Draft Only'}
          </span>
        </div>
        
        {mcpStatus === 'approved' && mcpResults && mcpResults.gmail && (
          <div className="bg-surface-container-lowest border border-outline-variant/30 rounded p-2 text-code-sm font-code-sm text-tertiary whitespace-pre-wrap">
            {mcpResults.gmail}
          </div>
        )}
      </div>

      {/* MCP GATEWAY TELEMETRY CONSOLE */}
      <div className="bg-surface-container-lowest border border-outline-variant/30 rounded-lg p-3 flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${mcpStatus === 'error' ? 'bg-error' : 'bg-tertiary'}`}></span>
            <span className="font-code-sm text-code-sm text-on-surface font-medium">MCP Gateway: Online (2 tools connected)</span>
          </div>
          <span className="text-code-sm font-code-sm text-outline">Latency: ~42ms</span>
        </div>
        <div className="font-code-sm text-code-sm text-outline/80 bg-surface-container-low/90 p-2 rounded flex flex-col gap-1">
          <div className="flex items-center justify-between text-on-surface-variant">
            <span>[SYS] mcp:google_docs_append</span>
            <span className={mcpStatus === 'approved' ? 'text-tertiary' : 'text-outline'}>{mcpStatus === 'approved' ? 'SUCCESS' : 'READY'}</span>
          </div>
          <div className="flex items-center justify-between text-on-surface-variant">
            <span>[SYS] mcp:gmail_create_draft</span>
            <span className={mcpStatus === 'approved' ? 'text-tertiary' : 'text-outline'}>{mcpStatus === 'approved' ? 'SUCCESS' : 'READY'}</span>
          </div>
          {mcpStatus === 'pending' && (
            <div className="flex items-center justify-between text-amber-300">
              <span>[SYS] auth_gate:human_signature</span>
              <span className="animate-pulse">AWAITING_INPUT</span>
            </div>
          )}
        </div>
      </div>

      {/* PRIMARY APPROVAL CONTROLS */}
      {mcpStatus === 'pending' && (
        <div className="flex flex-col gap-2 mt-auto pt-2">
          <button 
            className="w-full py-2.5 px-4 rounded-md bg-primary hover:bg-primary-container text-on-primary font-headline-md text-body-md font-bold flex items-center justify-center gap-2 shadow-lg transition-all duration-150 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none" 
            onClick={handleApprove}
            disabled={isApproving}
          >
            {isApproving ? (
               <>
                 <span className="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
                 <span>Executing MCP Tool Calls...</span>
               </>
            ) : (
               <>
                 <span className="material-symbols-outlined text-[18px]">bolt</span>
                 <span>Approve & Trigger MCP Actions</span>
               </>
            )}
          </button>
          <div className="flex gap-2">
            <button 
              className="flex-1 py-1.5 px-3 rounded-md bg-surface-container hover:bg-surface-container-high border border-outline-variant/30 text-error hover:text-error/80 font-label-md text-label-md transition-all text-center"
              onClick={onReject}
              disabled={isApproving}
            >
              Reject / Halt
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
