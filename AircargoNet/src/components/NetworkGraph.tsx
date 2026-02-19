/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { Node, Edge } from '../types';

interface Props {
  nodes: Node[];
  edges: Edge[];
  onNodeSelect: (node: Node | null) => void;
}

interface D3Node extends d3.SimulationNodeDatum, Node {}
interface D3Edge extends d3.SimulationLinkDatum<D3Node>, Omit<Edge, 'source' | 'target'> {}

export const NetworkGraph: React.FC<Props> = ({ nodes, edges, onNodeSelect }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const g = svg.append('g');

    // Zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    const d3Nodes: D3Node[] = nodes.map(n => ({ ...n }));
    const d3Edges: D3Edge[] = edges.map(e => ({ ...e }));

    const simulation = d3.forceSimulation<D3Node>(d3Nodes)
      .force('link', d3.forceLink<D3Node, D3Edge>(d3Edges).id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    // Arrow markers
    svg.append('defs').selectAll('marker')
      .data(['end'])
      .enter().append('marker')
      .attr('id', d => d)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('fill', '#94a3b8')
      .attr('d', 'M0,-5L10,0L0,5');

    const link = g.append('g')
      .selectAll('line')
      .data(d3Edges)
      .enter().append('line')
      .attr('stroke', '#cbd5e1')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => Math.sqrt(d.weight) / 2)
      .attr('marker-end', 'url(#end)');

    const node = g.append('g')
      .selectAll('g')
      .data(d3Nodes)
      .enter().append('g')
      .attr('cursor', 'pointer')
      .on('click', (event, d) => onNodeSelect(d))
      .call(d3.drag<any, any>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));

    node.append('circle')
      .attr('r', 8)
      .attr('fill', d => {
        const hubs = ['PEK', 'PVG', 'CAN', 'SZX', 'HGH', 'EHU'];
        return hubs.includes(d.id) ? '#10b981' : '#6366f1';
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);

    node.append('text')
      .attr('dx', 12)
      .attr('dy', '.35em')
      .text(d => d.id)
      .attr('font-size', '10px')
      .attr('font-family', 'sans-serif')
      .attr('fill', '#475569');

    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as any).x)
        .attr('y1', d => (d.source as any).y)
        .attr('x2', d => (d.target as any).x)
        .attr('y2', d => (d.target as any).y);

      node
        .attr('transform', d => `translate(${d.x},${d.y})`);
    });

    function dragstarted(event: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: any) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event: any) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    return () => {
      simulation.stop();
    };
  }, [nodes, edges, onNodeSelect]);

  return (
    <div className="w-full h-full bg-slate-50 rounded-xl border border-slate-200 overflow-hidden relative">
      <svg ref={svgRef} className="w-full h-full" />
      <div className="absolute bottom-4 left-4 bg-white/80 backdrop-blur-sm p-3 rounded-lg border border-slate-200 text-xs space-y-2">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#10b981]" />
          <span>Major Hubs</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#6366f1]" />
          <span>Regional Airports</span>
        </div>
      </div>
    </div>
  );
};
