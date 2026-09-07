import React from 'react';

export default function PipelineStepper({ status, mcpStatus }) {
  const isCompleted = status === 'completed';
  const isRunning = status === 'running';

  // Step 1: Review Intelligence
  let step1State = 'pending';
  if (isRunning || isCompleted) step1State = 'done';

  // Step 2 & 3: Synthesis
  let step23State = 'pending';
  if (isCompleted) step23State = 'done';

  // Step 4: MCP Gate
  let step4State = 'pending';
  if (isCompleted && mcpStatus === 'pending') step4State = 'active';
  if (mcpStatus === 'approved') step4State = 'done';
  if (mcpStatus === 'rejected') step4State = 'rejected';

  return (
    <div className="px-layout-margin-desktop py-3 bg-surface-container-low/40 border-b border-outline-variant/20">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        
        {/* Step 1: Review Intelligence Layer */}
        <div className={`relative p-2.5 rounded-lg border flex items-center justify-between shadow-sm transition-colors ${step1State === 'done' ? 'bg-surface-container-low border-tertiary/40' : 'bg-surface-container-lowest border-outline-variant/30 opacity-60'}`}>
          <div className="flex items-center gap-2.5 min-w-0">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${step1State === 'done' ? 'bg-tertiary/20 text-tertiary' : 'bg-surface-container-high text-outline'}`}>
              <span className="material-symbols-outlined text-[14px]">check</span>
            </div>
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-code-sm text-code-sm text-outline">STEP 01</span>
                <span className={`font-label-sm text-label-sm font-semibold uppercase ${step1State === 'done' ? 'text-tertiary' : 'text-outline'}`}>
                  {step1State === 'done' ? 'Clustered' : 'Pending'}
                </span>
              </div>
              <span className="font-headline-md text-body-sm font-semibold text-on-surface truncate">Review Intelligence Layer</span>
            </div>
          </div>
          <span className="material-symbols-outlined text-outline-variant hidden xl:block text-[18px]">arrow_forward</span>
        </div>

        {/* Step 2: Weekly Pulse Synthesis */}
        <div className={`relative p-2.5 rounded-lg border flex items-center justify-between shadow-sm transition-colors ${step23State === 'done' ? 'bg-surface-container-low border-tertiary/40' : 'bg-surface-container-lowest border-outline-variant/30 opacity-60'}`}>
          <div className="flex items-center gap-2.5 min-w-0">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${step23State === 'done' ? 'bg-tertiary/20 text-tertiary' : 'bg-surface-container-high text-outline'}`}>
              <span className="material-symbols-outlined text-[14px]">check</span>
            </div>
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-code-sm text-code-sm text-outline">STEP 02</span>
                <span className={`font-label-sm text-label-sm font-semibold uppercase ${step23State === 'done' ? 'text-tertiary' : 'text-outline'}`}>
                  {step23State === 'done' ? 'Verified' : 'Pending'}
                </span>
              </div>
              <span className="font-headline-md text-body-sm font-semibold text-on-surface truncate">Weekly Pulse Synthesis</span>
            </div>
          </div>
          <span className="material-symbols-outlined text-outline-variant hidden xl:block text-[18px]">arrow_forward</span>
        </div>

        {/* Step 3: Support Fee Explainer */}
        <div className={`relative p-2.5 rounded-lg border flex items-center justify-between shadow-sm transition-colors ${step23State === 'done' ? 'bg-surface-container-low border-tertiary/40' : 'bg-surface-container-lowest border-outline-variant/30 opacity-60'}`}>
          <div className="flex items-center gap-2.5 min-w-0">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${step23State === 'done' ? 'bg-tertiary/20 text-tertiary' : 'bg-surface-container-high text-outline'}`}>
              <span className="material-symbols-outlined text-[14px]">check</span>
            </div>
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-code-sm text-code-sm text-outline">STEP 03</span>
                <span className={`font-label-sm text-label-sm font-semibold uppercase ${step23State === 'done' ? 'text-tertiary' : 'text-outline'}`}>
                  {step23State === 'done' ? 'Fact-Checked' : 'Pending'}
                </span>
              </div>
              <span className="font-headline-md text-body-sm font-semibold text-on-surface truncate">Support Fee Explainer</span>
            </div>
          </div>
          <span className="material-symbols-outlined text-outline-variant hidden xl:block text-[18px]">arrow_forward</span>
        </div>

        {/* Step 4: MCP Action & Approval Gating */}
        <div className={`relative p-2.5 rounded-lg border-2 flex items-center justify-between shadow-md transition-all ${
          step4State === 'active' ? 'bg-surface-container-high border-primary-container active-glow-pulse' :
          step4State === 'done' ? 'bg-surface-container-low border-tertiary/40' :
          step4State === 'rejected' ? 'bg-surface-container-low border-error/40' :
          'bg-surface-container-lowest border-outline-variant/30 opacity-60'
        }`}>
          <div className="flex items-center gap-2.5 min-w-0">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
              step4State === 'active' ? 'bg-primary-container text-on-primary-container animate-pulse' :
              step4State === 'done' ? 'bg-tertiary/20 text-tertiary' :
              step4State === 'rejected' ? 'bg-error/20 text-error' :
              'bg-surface-container-high text-outline'
            }`}>
              <span className="material-symbols-outlined text-[15px]">
                {step4State === 'done' ? 'check' : step4State === 'rejected' ? 'close' : 'lock_clock'}
              </span>
            </div>
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-1.5">
                <span className={`font-code-sm text-code-sm font-semibold ${step4State === 'active' ? 'text-primary' : 'text-outline'}`}>STEP 04</span>
                <span className={`font-label-sm text-label-sm font-semibold uppercase ${
                  step4State === 'active' ? 'text-amber-400' :
                  step4State === 'done' ? 'text-tertiary' :
                  step4State === 'rejected' ? 'text-error' :
                  'text-outline'
                }`}>
                  {step4State === 'active' ? 'Approval Gate' : step4State === 'done' ? 'Dispatched' : step4State === 'rejected' ? 'Halted' : 'Pending'}
                </span>
              </div>
              <span className="font-headline-md text-body-sm font-bold text-on-surface truncate">MCP Dispatch</span>
            </div>
          </div>
          {step4State === 'active' && (
            <span className="px-2 py-0.5 rounded text-code-sm font-code-sm bg-amber-400/10 text-amber-300 border border-amber-400/30">Action Needed</span>
          )}
        </div>

      </div>
    </div>
  );
}
