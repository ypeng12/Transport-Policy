/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useMemo, useEffect } from 'react';
import { NetworkAnalyzer } from './services/networkAnalyzer';
import { MOCK_AIRPORTS, generateMockEdges } from './mockData';
import { Node, Edge, CentralityMetrics, NetworkStats, RobustnessPoint } from './types';
import { NetworkGraph } from './components/NetworkGraph';
import { RobustnessChart } from './components/RobustnessChart';
import { 
  Activity, 
  BarChart3, 
  Network, 
  ShieldAlert, 
  Plane, 
  Map as MapIcon,
  Search,
  Info,
  ChevronRight,
  RefreshCw
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

export default function App() {
  const [nodes] = useState<Node[]>(MOCK_AIRPORTS);
  const [edges, setEdges] = useState<Edge[]>(generateMockEdges());
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [robustnessData, setRobustnessData] = useState<RobustnessPoint[][]>([]);
  const [isSimulating, setIsSimulating] = useState(false);

  const analyzer = useMemo(() => new NetworkAnalyzer(nodes, edges), [nodes, edges]);
  const metrics = useMemo(() => analyzer.calculateAllMetrics(), [analyzer]);
  const stats = useMemo(() => analyzer.getStats(), [analyzer]);

  const sortedNodes = useMemo(() => {
    return [...nodes].sort((a, b) => {
      const ma = metrics.get(a.id)!;
      const mb = metrics.get(b.id)!;
      return mb.domiRank - ma.domiRank;
    });
  }, [nodes, metrics]);

  const runSimulations = () => {
    setIsSimulating(true);
    // Use setTimeout to allow UI to update before heavy calculation
    setTimeout(() => {
      const strategies: ('random' | 'degree' | 'betweenness' | 'pageRank' | 'domiRank')[] = 
        ['random', 'degree', 'betweenness', 'pageRank', 'domiRank'];
      const results = strategies.map(s => analyzer.simulateRobustness(s));
      setRobustnessData(results);
      setIsSimulating(false);
    }, 100);
  };

  useEffect(() => {
    runSimulations();
  }, [analyzer]);

  const regenerateData = () => {
    setEdges(generateMockEdges());
    setSelectedNode(null);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 sticky top-0 z-10">
        <div className="max-w-[1600px] mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-600 p-2 rounded-lg">
              <Network className="text-white w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">AirCargoNet</h1>
              <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Complex Network Analysis Tool</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={regenerateData}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Regenerate Network
            </button>
            <div className="h-8 w-px bg-slate-200" />
            <div className="text-right">
              <p className="text-xs text-slate-500">Analysis Mode</p>
              <p className="text-sm font-semibold">China Domestic Cargo (CACN)</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto p-6 grid grid-cols-12 gap-6">
        {/* Left Column: Stats & Rankings */}
        <div className="col-span-12 lg:col-span-3 space-y-6">
          {/* Network Stats */}
          <section className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
            <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Network Topology
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-slate-50 rounded-xl">
                <p className="text-xs text-slate-500 mb-1">Nodes</p>
                <p className="text-2xl font-bold">{stats.nodeCount}</p>
              </div>
              <div className="p-3 bg-slate-50 rounded-xl">
                <p className="text-xs text-slate-500 mb-1">Edges</p>
                <p className="text-2xl font-bold">{stats.edgeCount}</p>
              </div>
              <div className="p-3 bg-slate-50 rounded-xl">
                <p className="text-xs text-slate-500 mb-1">Density</p>
                <p className="text-lg font-bold">{(stats.density * 100).toFixed(2)}%</p>
              </div>
              <div className="p-3 bg-slate-50 rounded-xl">
                <p className="text-xs text-slate-500 mb-1">Avg Path</p>
                <p className="text-lg font-bold">{stats.avgShortestPath.toFixed(2)}</p>
              </div>
            </div>
            <div className="mt-4 p-3 bg-indigo-50 border border-indigo-100 rounded-xl">
              <div className="flex justify-between items-center mb-1">
                <p className="text-xs text-indigo-600 font-bold uppercase tracking-wider">Giant Component (NGC)</p>
                <p className="text-sm font-bold text-indigo-700">{(stats.ngc * 100).toFixed(1)}%</p>
              </div>
              <div className="w-full bg-indigo-200 h-2 rounded-full overflow-hidden">
                <div className="bg-indigo-600 h-full" style={{ width: `${stats.ngc * 100}%` }} />
              </div>
            </div>
          </section>

          {/* Hub Rankings */}
          <section className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                Hub Rankings
              </h2>
              <span className="text-[10px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-bold">DomiRank</span>
            </div>
            <div className="max-h-[400px] overflow-y-auto">
              {sortedNodes.slice(0, 10).map((node, idx) => {
                const m = metrics.get(node.id)!;
                return (
                  <button 
                    key={node.id}
                    onClick={() => setSelectedNode(node)}
                    className={`w-full flex items-center gap-3 p-4 hover:bg-slate-50 transition-colors border-b border-slate-50 last:border-0 ${selectedNode?.id === node.id ? 'bg-indigo-50 hover:bg-indigo-50' : ''}`}
                  >
                    <span className="text-sm font-bold text-slate-300 w-4">{idx + 1}</span>
                    <div className="flex-1 text-left">
                      <p className="text-sm font-bold">{node.id}</p>
                      <p className="text-[10px] text-slate-500">{node.city}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs font-mono font-bold text-indigo-600">{m.domiRank.toFixed(4)}</p>
                      <p className="text-[10px] text-slate-400">Deg: {m.degree}</p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-300" />
                  </button>
                );
              })}
            </div>
          </section>
        </div>

        {/* Middle Column: Graph & Robustness */}
        <div className="col-span-12 lg:col-span-6 space-y-6">
          {/* Network Visualization */}
          <div className="h-[500px] relative">
            <NetworkGraph 
              nodes={nodes} 
              edges={edges} 
              onNodeSelect={setSelectedNode} 
            />
            <div className="absolute top-4 left-4 flex gap-2">
              <div className="bg-white/90 backdrop-blur-sm px-3 py-1.5 rounded-full border border-slate-200 text-[10px] font-bold flex items-center gap-2">
                <MapIcon className="w-3 h-3" />
                Spatial Topology
              </div>
            </div>
          </div>

          {/* Robustness Analysis */}
          <section className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-bold flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-amber-500" />
                  Network Robustness Analysis
                </h2>
                <p className="text-sm text-slate-500">Simulated impact of node removal on connectivity (NGC)</p>
              </div>
              <button 
                onClick={runSimulations}
                disabled={isSimulating}
                className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 disabled:opacity-50 flex items-center gap-2"
              >
                {isSimulating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Activity className="w-4 h-4" />}
                Run Simulation
              </button>
            </div>
            <RobustnessChart data={robustnessData} />
            <div className="mt-4 grid grid-cols-5 gap-2">
              {[
                { label: 'Random', color: 'bg-slate-400' },
                { label: 'Degree', color: 'bg-indigo-500' },
                { label: 'Betweenness', color: 'bg-amber-500' },
                { label: 'PageRank', color: 'bg-pink-500' },
                { label: 'DomiRank', color: 'bg-emerald-500' },
              ].map(s => (
                <div key={s.label} className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${s.color}`} />
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">{s.label}</span>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Right Column: Node Details */}
        <div className="col-span-12 lg:col-span-3">
          <AnimatePresence mode="wait">
            {selectedNode ? (
              <motion.div 
                key={selectedNode.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden sticky top-24"
              >
                <div className="bg-indigo-600 p-6 text-white">
                  <div className="flex justify-between items-start mb-4">
                    <Plane className="w-8 h-8 opacity-50" />
                    <button 
                      onClick={() => setSelectedNode(null)}
                      className="text-white/60 hover:text-white"
                    >
                      <ChevronRight className="w-6 h-6 rotate-180" />
                    </button>
                  </div>
                  <h3 className="text-2xl font-bold leading-tight">{selectedNode.name}</h3>
                  <p className="text-indigo-100 font-medium">{selectedNode.city}, China ({selectedNode.id})</p>
                </div>

                <div className="p-6 space-y-6">
                  {/* Centrality Grid */}
                  <div>
                    <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                      <BarChart3 className="w-3 h-3" />
                      Centrality Metrics
                    </h4>
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { label: 'DomiRank', value: metrics.get(selectedNode.id)!.domiRank.toFixed(4) },
                        { label: 'PageRank', value: metrics.get(selectedNode.id)!.pageRank.toFixed(4) },
                        { label: 'Betweenness', value: metrics.get(selectedNode.id)!.betweenness.toFixed(4) },
                        { label: 'Closeness', value: metrics.get(selectedNode.id)!.closeness.toFixed(4) },
                        { label: 'In-Degree', value: metrics.get(selectedNode.id)!.inDegree },
                        { label: 'Out-Degree', value: metrics.get(selectedNode.id)!.outDegree },
                      ].map(m => (
                        <div key={m.label} className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                          <p className="text-[10px] text-slate-500 mb-0.5">{m.label}</p>
                          <p className="text-sm font-bold text-slate-900">{m.value}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Context Info */}
                  <div className="p-4 bg-amber-50 border border-amber-100 rounded-xl">
                    <div className="flex gap-3">
                      <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      <p className="text-xs text-amber-800 leading-relaxed">
                        {selectedNode.id === 'EHU' ? 
                          "Ezhou Huahu Airport (EHU) is China's first dedicated air cargo hub. Our analysis shows it exhibits high DomiRank, indicating strong local influence despite being a newer node." :
                          `As a key node in the CACN, ${selectedNode.name} plays a vital role in regional cargo distribution and network connectivity.`
                        }
                      </p>
                    </div>
                  </div>

                  {/* Connections */}
                  <div>
                    <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Direct Connections</h4>
                    <div className="flex flex-wrap gap-2">
                      {edges
                        .filter(e => e.source === selectedNode.id)
                        .slice(0, 12)
                        .map(e => (
                          <span key={e.target} className="px-2 py-1 bg-slate-100 text-slate-600 rounded text-[10px] font-bold">
                            {e.target}
                          </span>
                        ))}
                      {edges.filter(e => e.source === selectedNode.id).length > 12 && (
                        <span className="text-[10px] text-slate-400 font-medium">
                          +{edges.filter(e => e.source === selectedNode.id).length - 12} more
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            ) : (
              <div className="bg-white rounded-2xl border border-slate-200 border-dashed p-12 text-center sticky top-24">
                <div className="bg-slate-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Search className="text-slate-300 w-8 h-8" />
                </div>
                <h3 className="text-slate-900 font-bold mb-2">No Airport Selected</h3>
                <p className="text-sm text-slate-500">Click on a node in the graph or a hub in the rankings to view detailed analysis.</p>
              </div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Footer */}
      <footer className="max-w-[1600px] mx-auto px-6 py-12 border-t border-slate-200 mt-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="bg-slate-900 p-1.5 rounded">
                <Network className="text-white w-4 h-4" />
              </div>
              <span className="font-bold text-lg">AirCargoNet</span>
            </div>
            <p className="text-sm text-slate-500 leading-relaxed">
              Inspired by the research paper: "Complex network analysis of China’s domestic air cargo network based on actual flight data" (Transport Policy, 2025).
            </p>
          </div>
          <div>
            <h4 className="font-bold mb-4">Methodology</h4>
            <ul className="text-sm text-slate-500 space-y-2">
              <li>• Complex Network Theory (CNT)</li>
              <li>• Multi-Centrality Evaluation</li>
              <li>• DomiRank Dominance Metric</li>
              <li>• Network Robustness Simulation</li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold mb-4">Key Insights</h4>
            <p className="text-sm text-slate-500 leading-relaxed">
              The network exhibits scale-free and small-world characteristics. Hubs like HGH, SZX, and the emerging EHU are critical for system resilience.
            </p>
          </div>
        </div>
        <div className="mt-12 pt-8 border-t border-slate-100 text-center">
          <p className="text-xs text-slate-400">© 2026 AirCargoNet Analysis Tool. Built for Research & Optimization.</p>
        </div>
      </footer>
    </div>
  );
}
