import React from 'react';

export default function SynthesizedOutputs({ pulseText, feeExplainerText }) {
  if (!pulseText) return (
    <section className="xl:col-span-4 flex flex-col gap-4 min-w-0 opacity-50 pointer-events-none">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-sm bg-secondary"></span>
          <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">Synthesized AI Outputs</h2>
        </div>
      </div>
      <div className="bg-surface-container-low border border-outline-variant/30 rounded-lg p-6 flex flex-col items-center justify-center shadow-sm text-outline h-64">
        <span className="material-symbols-outlined text-[32px] mb-2">summarize</span>
        <span className="font-code-sm">Awaiting Output Synthesis...</span>
      </div>
    </section>
  );

  return (
    <section className="xl:col-span-4 flex flex-col gap-4 min-w-0">
      {/* Panel Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-sm bg-secondary"></span>
          <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">Synthesized AI Outputs</h2>
        </div>
        <div className="flex items-center gap-1">
          <span className="px-2 py-0.5 rounded text-code-sm font-code-sm bg-primary/10 text-primary border border-primary/20">
            Steps 2 & 3
          </span>
        </div>
      </div>

      {/* CARD A: Step 2 — Weekly Product Pulse */}
      <div className="bg-surface-container-low border border-outline-variant/30 rounded-lg p-4 flex flex-col gap-3 shadow-sm relative ambient-glow">
        <div className="flex items-start justify-between gap-2 border-b border-outline-variant/20 pb-2.5">
          <div>
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-[18px]">summarize</span>
              <h3 className="font-headline-md text-body-lg font-bold text-on-surface">Weekly Product Pulse</h3>
            </div>
            <span className="text-code-sm font-code-sm text-outline">Audience: Internal Leadership & Product Teams</span>
          </div>
          <span className="px-2 py-0.5 rounded text-code-sm font-code-sm bg-tertiary-container/30 text-tertiary border border-tertiary/30 font-medium whitespace-nowrap">
            Auto-Generated
          </span>
        </div>

        {/* Summary Content - Rendering text block */}
        <div className="flex flex-col gap-2.5 text-body-sm font-body-sm text-on-surface">
          <div className="p-3 rounded bg-surface-container-lowest/60 border border-outline-variant/20 whitespace-pre-wrap font-body-sm leading-relaxed overflow-y-auto max-h-96 custom-scroll">
            {pulseText}
          </div>
        </div>
      </div>

      {/* CARD B: Step 3 — Customer Support Fee Explainer */}
      {feeExplainerText && feeExplainerText !== "No fee confusion was identified in the reviews." && (
        <div className="bg-surface-container-low border border-outline-variant/30 rounded-lg p-4 flex flex-col gap-3 shadow-sm">
          <div className="flex items-start justify-between gap-2 border-b border-outline-variant/20 pb-2.5">
            <div>
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary text-[18px]">support_agent</span>
                <h3 className="font-headline-md text-body-lg font-bold text-on-surface">Support Fee Explainer Macro</h3>
              </div>
              <span className="text-code-sm font-code-sm text-outline">Tone: Neutral, factual, regulatory-aligned macro</span>
            </div>
            <span className="px-2 py-0.5 rounded text-code-sm font-code-sm bg-tertiary/10 text-tertiary border border-tertiary/30 font-medium">
              Verified
            </span>
          </div>

          <div className="p-3 rounded bg-surface-container-lowest/60 border border-outline-variant/20 whitespace-pre-wrap font-body-sm leading-relaxed text-on-surface-variant overflow-y-auto max-h-80 custom-scroll">
            {feeExplainerText}
          </div>
        </div>
      )}
    </section>
  );
}
