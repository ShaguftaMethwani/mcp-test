import React from 'react';

export default function TopBar({ reviewsCount, status }) {
  return (
    <>
      <header className="flex justify-between items-center w-full px-layout-margin-desktop py-2 border-b border-outline-variant/20 bg-surface-container-low sticky top-0 z-30 backdrop-blur-md">
        {/* Left: Logo & Search Bar */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-md bg-primary-container text-on-primary-container flex items-center justify-center font-bold">
              <span className="material-symbols-outlined text-[18px]">dynamic_feed</span>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="font-headline-md text-headline-md font-semibold text-on-surface tracking-tight">PulseFlow AI</span>
                <span className="hidden sm:inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-code-sm font-code-sm bg-tertiary-container/30 text-tertiary border border-tertiary/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-tertiary animate-ping"></span>
                  Live Pipeline • Production v2.4
                </span>
              </div>
            </div>
          </div>
          {/* Search Bar Input on left */}
          <div className="relative hidden md:block w-72">
            <span className="material-symbols-outlined absolute left-2.5 top-2 text-[16px] text-outline">search</span>
            <input className="w-full bg-surface-container-lowest border border-outline-variant/30 rounded-md pl-8 pr-3 py-1 text-body-sm font-body-sm text-on-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/40 placeholder-outline/60" placeholder="Search clusters, signals, MCP tools..." type="text"/>
          </div>
        </div>
        {/* Center-Right Navigation Links */}
        <div className="hidden xl:flex items-center gap-6">
          <a className="text-on-surface-variant font-label-md hover:text-on-surface transition-colors duration-150" href="#">Pipelines</a>
          <a className="text-primary border-b-2 border-primary pb-1 font-headline-md font-medium text-body-md" href="#">Insights Pulse</a>
          <a className="text-on-surface-variant font-label-md hover:text-on-surface transition-colors duration-150" href="#">MCP Toolchains</a>
          <a className="text-on-surface-variant font-label-md hover:text-on-surface transition-colors duration-150" href="#">Audits</a>
        </div>
        {/* Trailing Action Toolbar & Avatar */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 text-on-surface-variant">
            <button className="p-1.5 rounded hover:bg-surface-container-high hover:text-on-surface transition-colors duration-150" title="Notifications">
              <span className="material-symbols-outlined text-[18px]">notifications</span>
            </button>
            <button className="p-1.5 rounded hover:bg-surface-container-high hover:text-on-surface transition-colors duration-150" title="Terminal Log">
              <span className="material-symbols-outlined text-[18px]">terminal</span>
            </button>
            <button className="p-1.5 rounded hover:bg-surface-container-high hover:text-on-surface transition-colors duration-150" title="Configuration">
              <span className="material-symbols-outlined text-[18px]">tune</span>
            </button>
          </div>
          <div className="h-4 w-px bg-outline-variant/30 mx-1"></div>
          <button className="px-2.5 py-1 text-label-md font-label-md text-on-surface bg-surface-container-high hover:bg-surface-variant border border-outline-variant/30 rounded transition-all">
            Staging
          </button>
          <button className="flex items-center gap-1.5 px-3 py-1 text-label-md font-label-md text-on-primary bg-primary-container hover:bg-primary font-medium rounded transition-all shadow-sm">
            <span className="material-symbols-outlined text-[16px]">cloud_upload</span>
            Deploy Changes
          </button>
          <div className="w-7 h-7 rounded-full bg-surface-variant border border-primary/40 flex items-center justify-center text-primary font-code-sm text-code-sm ml-1">
            PF
          </div>
        </div>
      </header>

      {/* WORKBENCH SUB-HEADER / ACTIVE DATASET BAR */}
      <div className="px-layout-margin-desktop py-2.5 bg-surface-container-lowest/60 border-b border-outline-variant/20 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-2.5 py-1 bg-surface-container-low border border-outline-variant/30 rounded">
            <span className="material-symbols-outlined text-primary text-[16px]">dataset</span>
            <span className="font-code-sm text-code-sm text-on-surface font-medium">reviews_last_4_weeks_groww.csv</span>
            <span className="text-outline text-code-sm font-code-sm">• {reviewsCount || 0} public reviews analyzed</span>
          </div>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-code-sm font-code-sm bg-tertiary/10 text-tertiary border border-tertiary/20">
            <span className="material-symbols-outlined text-[13px]">verified</span> {status === 'completed' ? 'Analysis Complete' : (status === 'running' ? 'Running...' : 'Idle')}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container border border-outline-variant/30 hover:border-outline text-on-surface text-label-md font-label-md transition-all">
            <span className="material-symbols-outlined text-[15px]">refresh</span>
            Re-run Analysis
          </button>
          <button className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container border border-outline-variant/30 hover:border-outline text-on-surface text-label-md font-label-md transition-all">
            <span className="material-symbols-outlined text-[15px]">settings_input_component</span>
            Pipeline Config
          </button>
        </div>
      </div>
    </>
  );
}
