import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import PipelineStepper from './components/PipelineStepper';
import ReviewIntelligence from './components/ReviewIntelligence';
import SynthesizedOutputs from './components/SynthesizedOutputs';
import McpDispatcher from './components/McpDispatcher';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export default function App() {
  const [pipelineState, setPipelineState] = useState({
    status: 'idle',
    reviewsCount: 0,
    clusterResult: null,
    pulseText: null,
    feeExplainerText: null,
    mcpStatus: 'pending',
    mcpResults: null,
    error: null,
  });

  // Fetch status on load
  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/status`);
      const data = await res.json();
      setPipelineState(prev => ({ ...prev, ...data }));
    } catch (err) {
      console.error("Failed to fetch status:", err);
    }
  };

  const handleRunPipeline = async () => {
    setPipelineState(prev => ({
      ...prev,
      status: 'running',
      error: null,
      clusterResult: null,
      pulseText: null,
      feeExplainerText: null,
      mcpStatus: 'pending',
      mcpResults: null,
    }));

    try {
      const res = await fetch(`${API_BASE}/api/run-pipeline`, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Pipeline failed');
      
      setPipelineState(prev => ({
        ...prev,
        status: data.status,
        reviewsCount: data.reviews_count,
        clusterResult: data.cluster_result,
        pulseText: data.pulse_text,
        feeExplainerText: data.fee_explainer_text,
        mcpStatus: data.mcp_status,
      }));
    } catch (err) {
      setPipelineState(prev => ({ ...prev, status: 'error', error: err.message }));
    }
  };

  const handleApproveMcp = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/approve`, { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Approval failed');
      
      setPipelineState(prev => ({
        ...prev,
        mcpStatus: data.status,
        mcpResults: { docs: data.docs_result, gmail: data.gmail_result },
      }));
    } catch (err) {
      alert(`Error approving MCP: ${err.message}`);
    }
  };

  const handleRejectMcp = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/reject`, { method: 'POST' });
      const data = await res.json();
      setPipelineState(prev => ({ ...prev, mcpStatus: data.status }));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="bg-background text-on-surface font-body-md text-body-md antialiased min-h-screen overflow-x-hidden flex selection:bg-primary/30">
      
      <Sidebar mcpStatus={pipelineState.mcpStatus} />
      
      <div className="flex-1 flex flex-col min-w-0 lg:pl-60">
        <TopBar reviewsCount={pipelineState.reviewsCount} status={pipelineState.status} />
        
        {pipelineState.error && (
          <div className="px-layout-margin-desktop py-2 bg-error-container text-on-error-container text-body-sm">
            <strong>Error:</strong> {pipelineState.error}
          </div>
        )}

        {pipelineState.status === 'idle' && (
          <div className="px-layout-margin-desktop py-4 bg-surface-container-low/40 border-b border-outline-variant/20 flex justify-center">
            <button 
              onClick={handleRunPipeline}
              className="py-2.5 px-6 rounded-md bg-primary hover:bg-primary-container text-on-primary font-headline-md text-body-md font-bold flex items-center justify-center gap-2 shadow-lg transition-all"
            >
              <span className="material-symbols-outlined text-[18px]">play_arrow</span>
              <span>Trigger Pipeline</span>
            </button>
          </div>
        )}

        {pipelineState.status !== 'idle' && (
          <PipelineStepper status={pipelineState.status} mcpStatus={pipelineState.mcpStatus} />
        )}

        <main className="flex-1 p-layout-margin-desktop grid grid-cols-1 xl:grid-cols-12 gap-5 overflow-hidden">
          <ReviewIntelligence 
            clusterResult={pipelineState.clusterResult} 
            reviewsCount={pipelineState.reviewsCount} 
          />
          <SynthesizedOutputs 
            pulseText={pipelineState.pulseText} 
            feeExplainerText={pipelineState.feeExplainerText} 
          />
          <McpDispatcher 
            status={pipelineState.status} 
            mcpStatus={pipelineState.mcpStatus}
            mcpResults={pipelineState.mcpResults}
            onApprove={handleApproveMcp}
            onReject={handleRejectMcp}
          />
        </main>
      </div>

    </div>
  );
}
