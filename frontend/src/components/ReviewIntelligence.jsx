import React from 'react';

export default function ReviewIntelligence({ clusterResult, reviewsCount }) {
  if (!clusterResult) return (
    <section className="xl:col-span-4 flex flex-col gap-4 min-w-0 opacity-50 pointer-events-none">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-sm bg-primary"></span>
          <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">Review Intelligence Layer</h2>
        </div>
      </div>
      <div className="bg-surface-container-low border border-outline-variant/30 rounded-lg p-6 flex flex-col items-center justify-center shadow-sm text-outline h-64">
        <span className="material-symbols-outlined text-[32px] mb-2">analytics</span>
        <span className="font-code-sm">Awaiting Pipeline Execution...</span>
      </div>
    </section>
  );

  const { themes, quotes, fee_confusion } = clusterResult;
  const topThemes = themes || [];

  return (
    <section className="xl:col-span-4 flex flex-col gap-4 min-w-0">
      {/* Panel Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-sm bg-primary"></span>
          <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">Review Intelligence Layer</h2>
        </div>
        <span className="text-code-sm font-code-sm text-outline px-2 py-0.5 rounded bg-surface-container-low border border-outline-variant/30">
          {topThemes.length} Clusters Identified
        </span>
      </div>

      {/* Ingest Volume & Sentiment Card */}
      <div className="bg-surface-container-low border border-outline-variant/30 rounded-lg p-3.5 flex flex-col gap-3 shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-body-sm font-body-sm text-on-surface-variant">Cluster Volume Distribution</span>
          <span className="text-code-sm font-code-sm text-outline">N = {reviewsCount}</span>
        </div>

        {/* Dynamic Cluster Bars */}
        {topThemes.map((theme, index) => {
          const isFlagged = fee_confusion && fee_confusion.related_theme === theme.name;
          // Approximate percentage (for UI only)
          const pct = Math.round((theme.count / Math.max(reviewsCount, 1)) * 100);

          if (isFlagged) {
            return (
              <div key={index} className="p-2.5 rounded-md bg-surface-container-lowest border border-error-container/60 relative overflow-hidden">
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-error"></div>
                <div className="flex justify-between items-start mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <span className="font-label-md text-label-md font-semibold text-on-surface">#{index + 1} {theme.name}</span>
                    <span className="text-code-sm font-code-sm px-1.5 py-0.2 rounded bg-error-container/30 text-error border border-error/30 font-medium">Flagged</span>
                  </div>
                  <span className="text-code-sm font-code-sm text-error font-medium">{theme.count} Reviews</span>
                </div>
                <div className="w-full bg-surface-container-highest rounded-full h-1.5 overflow-hidden flex">
                  <div className="bg-error h-full rounded-full" style={{ width: `${pct}%` }}></div>
                </div>
                <div className="flex justify-between items-center mt-1 text-code-sm font-code-sm text-outline">
                  <span>{pct}% Total Ingest Volume</span>
                </div>
              </div>
            );
          }

          // Normal bars (color alternates between primary and amber shades for visuals)
          const barColors = ['bg-primary', 'bg-amber-400', 'bg-amber-300/70', 'bg-secondary', 'bg-tertiary'];
          const barColor = barColors[index % barColors.length];

          return (
            <div key={index} className="p-2 rounded bg-surface-container-lowest/70 border border-outline-variant/20">
              <div className="flex justify-between items-center mb-1">
                <span className="font-label-md text-label-md text-on-surface truncate pr-2">#{index + 1} {theme.name}</span>
                <span className="text-code-sm font-code-sm text-on-surface-variant whitespace-nowrap">{theme.count} Reviews</span>
              </div>
              <div className="w-full bg-surface-container-highest rounded-full h-1.5 overflow-hidden flex">
                <div className={`${barColor} h-full rounded-full`} style={{ width: `${pct}%` }}></div>
              </div>
              <div className="flex justify-between items-center mt-1 text-code-sm font-code-sm text-outline">
                <span>{pct}% volume</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Specific Flagged Anomaly Callout */}
      {fee_confusion && (
        <div className="bg-surface-container-low border-l-2 border-primary border-t border-r border-b border-outline-variant/30 rounded-lg p-3">
          <div className="flex items-center gap-1.5 mb-1 text-primary">
            <span className="material-symbols-outlined text-[16px]">warning</span>
            <span className="text-label-sm font-label-sm uppercase tracking-wider font-semibold">Critical Fee Confusion Detected</span>
          </div>
          <div className="text-body-md font-body-md font-medium text-on-surface">{fee_confusion.fee_name}</div>
          <p className="text-body-sm font-body-sm text-on-surface-variant mt-1 leading-relaxed">
            {fee_confusion.user_pain}
          </p>
        </div>
      )}

      {/* Real User Verbatim Quotes Interactive Feed */}
      {quotes && quotes.length > 0 && (
        <div className="flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <span className="text-label-md font-label-md text-on-surface-variant">Verbatim Evidence (Sampled Quotes)</span>
            <span className="text-code-sm font-code-sm text-primary">{quotes.length} Selected</span>
          </div>

          {quotes.map((quote, idx) => (
            <div key={idx} className="bg-surface-container-low/80 hover:bg-surface-container-low border border-outline-variant/30 rounded-lg p-3 transition-colors">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-1 text-amber-400">
                  <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
                  <span className="text-code-sm font-code-sm text-outline">Verified Review</span>
                </div>
              </div>
              <p className="text-body-sm font-body-sm text-on-surface italic leading-relaxed">
                "{quote}"
              </p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
