/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export interface Node {
  id: string;
  name: string;
  city: string;
  lat: number;
  lng: number;
}

export interface Edge {
  source: string;
  target: string;
  weight: number; // e.g., flight frequency or cargo capacity
}

export interface CentralityMetrics {
  degree: number;
  inDegree: number;
  outDegree: number;
  betweenness: number;
  closeness: number;
  pageRank: number;
  domiRank: number;
}

export interface NetworkStats {
  nodeCount: number;
  edgeCount: number;
  density: number;
  avgClustering: number;
  avgShortestPath: number;
  ngc: number; // Normalized Giant Component size
}

export interface RobustnessPoint {
  removalRatio: number;
  ngc: number;
  strategy: string;
}
