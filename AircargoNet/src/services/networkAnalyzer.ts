/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Node, Edge, CentralityMetrics, NetworkStats, RobustnessPoint } from '../types';

export class NetworkAnalyzer {
  private nodes: Node[];
  private edges: Edge[];
  private adj: Map<string, Set<string>>;
  private revAdj: Map<string, Set<string>>;
  private weights: Map<string, number>;

  constructor(nodes: Node[], edges: Edge[]) {
    this.nodes = nodes;
    this.edges = edges;
    this.adj = new Map();
    this.revAdj = new Map();
    this.weights = new Map();

    nodes.forEach(n => {
      this.adj.set(n.id, new Set());
      this.revAdj.set(n.id, new Set());
    });

    edges.forEach(e => {
      this.adj.get(e.source)?.add(e.target);
      this.revAdj.get(e.target)?.add(e.source);
      this.weights.set(`${e.source}->${e.target}`, e.weight);
    });
  }

  public calculateAllMetrics(): Map<string, CentralityMetrics> {
    const metrics = new Map<string, CentralityMetrics>();
    
    const inDegrees = this.calculateInDegrees();
    const outDegrees = this.calculateOutDegrees();
    const betweenness = this.calculateBetweenness();
    const closeness = this.calculateCloseness();
    const pageRank = this.calculatePageRank();
    const domiRank = this.calculateDomiRank();

    this.nodes.forEach(node => {
      metrics.set(node.id, {
        inDegree: inDegrees.get(node.id) || 0,
        outDegree: outDegrees.get(node.id) || 0,
        degree: (inDegrees.get(node.id) || 0) + (outDegrees.get(node.id) || 0),
        betweenness: betweenness.get(node.id) || 0,
        closeness: closeness.get(node.id) || 0,
        pageRank: pageRank.get(node.id) || 0,
        domiRank: domiRank.get(node.id) || 0,
      });
    });

    return metrics;
  }

  private calculateInDegrees(): Map<string, number> {
    const map = new Map<string, number>();
    this.nodes.forEach(n => map.set(n.id, this.revAdj.get(n.id)?.size || 0));
    return map;
  }

  private calculateOutDegrees(): Map<string, number> {
    const map = new Map<string, number>();
    this.nodes.forEach(n => map.set(n.id, this.adj.get(n.id)?.size || 0));
    return map;
  }

  private calculateBetweenness(): Map<string, number> {
    const cb = new Map<string, number>();
    this.nodes.forEach(n => cb.set(n.id, 0));

    this.nodes.forEach(s => {
      const stack: string[] = [];
      const P = new Map<string, string[]>();
      const sigma = new Map<string, number>();
      const d = new Map<string, number>();
      
      this.nodes.forEach(n => {
        P.set(n.id, []);
        sigma.set(n.id, 0);
        d.set(n.id, -1);
      });

      sigma.set(s.id, 1);
      d.set(s.id, 0);

      const queue: string[] = [s.id];
      while (queue.length > 0) {
        const v = queue.shift()!;
        stack.push(v);
        this.adj.get(v)?.forEach(w => {
          if (d.get(w) === -1) {
            d.set(w, d.get(v)! + 1);
            queue.push(w);
          }
          if (d.get(w) === d.get(v)! + 1) {
            sigma.set(w, sigma.get(w)! + sigma.get(v)!);
            P.get(w)!.push(v);
          }
        });
      }

      const delta = new Map<string, number>();
      this.nodes.forEach(n => delta.set(n.id, 0));

      while (stack.length > 0) {
        const w = stack.pop()!;
        P.get(w)?.forEach(v => {
          delta.set(v, delta.get(v)! + (sigma.get(v)! / sigma.get(w)!) * (1 + delta.get(w)!));
        });
        if (w !== s.id) {
          cb.set(w, cb.get(w)! + delta.get(w)!);
        }
      }
    });

    // Normalize
    const n = this.nodes.length;
    const norm = (n - 1) * (n - 2);
    if (norm > 0) {
      this.nodes.forEach(node => cb.set(node.id, cb.get(node.id)! / norm));
    }

    return cb;
  }

  private calculateCloseness(): Map<string, number> {
    const closeness = new Map<string, number>();
    
    this.nodes.forEach(s => {
      const d = new Map<string, number>();
      this.nodes.forEach(n => d.set(n.id, -1));
      d.set(s.id, 0);

      const queue: string[] = [s.id];
      let totalDist = 0;
      let reachableCount = 0;

      while (queue.length > 0) {
        const v = queue.shift()!;
        this.adj.get(v)?.forEach(w => {
          if (d.get(w) === -1) {
            d.set(w, d.get(v)! + 1);
            totalDist += d.get(w)!;
            reachableCount++;
            queue.push(w);
          }
        });
      }

      if (reachableCount > 0) {
        closeness.set(s.id, reachableCount / totalDist);
      } else {
        closeness.set(s.id, 0);
      }
    });

    return closeness;
  }

  private calculatePageRank(alpha = 0.85, iterations = 50): Map<string, number> {
    const n = this.nodes.length;
    let pr = new Map<string, number>();
    this.nodes.forEach(node => pr.set(node.id, 1 / n));

    for (let i = 0; i < iterations; i++) {
      const nextPr = new Map<string, number>();
      let sinkPr = 0;
      
      this.nodes.forEach(node => {
        if (this.adj.get(node.id)!.size === 0) {
          sinkPr += pr.get(node.id)!;
        }
      });

      this.nodes.forEach(node => {
        let sum = 0;
        this.revAdj.get(node.id)?.forEach(neighbor => {
          sum += pr.get(neighbor)! / this.adj.get(neighbor)!.size;
        });
        nextPr.set(node.id, (1 - alpha) / n + alpha * (sum + sinkPr / n));
      });
      pr = nextPr;
    }

    return pr;
  }

  private calculateDomiRank(alpha = 0.1, beta = 0.1, iterations = 100): Map<string, number> {
    // DomiRank implementation based on the paper's equation
    // dΓi/dt = α(θki - Σ wij Γj(t)) - βΓi(t)
    // Discrete version: Γi(t+1) = Γi(t) + α(θki - Σ wij Γj(t)) - βΓi(t)
    
    const n = this.nodes.length;
    let gamma = new Map<string, number>();
    this.nodes.forEach(node => gamma.set(node.id, 1 / n));

    const theta = 1.0; // Scaling factor for degree

    for (let it = 0; it < iterations; it++) {
      const nextGamma = new Map<string, number>();
      this.nodes.forEach(node => {
        const ki = this.adj.get(node.id)!.size + this.revAdj.get(node.id)!.size;
        let sumNeighbors = 0;
        
        // Sum of connected nodes' gamma values
        this.adj.get(node.id)?.forEach(target => {
          sumNeighbors += gamma.get(target)!;
        });
        this.revAdj.get(node.id)?.forEach(source => {
          sumNeighbors += gamma.get(source)!;
        });

        const currentVal = gamma.get(node.id)!;
        const delta = alpha * (theta * ki - sumNeighbors) - beta * currentVal;
        nextGamma.set(node.id, Math.max(0, currentVal + delta));
      });
      gamma = nextGamma;
    }

    // Normalize
    let total = 0;
    gamma.forEach(v => total += v);
    if (total > 0) {
      this.nodes.forEach(node => gamma.set(node.id, gamma.get(node.id)! / total));
    }

    return gamma;
  }

  public getStats(): NetworkStats {
    const nodeCount = this.nodes.length;
    const edgeCount = this.edges.length;
    const density = edgeCount / (nodeCount * (nodeCount - 1));
    
    // Avg Clustering
    let totalClustering = 0;
    this.nodes.forEach(node => {
      const neighbors = new Set([...this.adj.get(node.id)!, ...this.revAdj.get(node.id)!]);
      const k = neighbors.size;
      if (k < 2) return;

      let actualEdges = 0;
      const neighborList = Array.from(neighbors);
      for (let i = 0; i < neighborList.length; i++) {
        for (let j = 0; j < neighborList.length; j++) {
          if (i === j) continue;
          if (this.adj.get(neighborList[i])?.has(neighborList[j])) {
            actualEdges++;
          }
        }
      }
      totalClustering += actualEdges / (k * (k - 1));
    });

    // Avg Shortest Path (using BFS for unweighted)
    let totalPath = 0;
    let pathCount = 0;
    this.nodes.forEach(s => {
      const d = new Map<string, number>();
      this.nodes.forEach(n => d.set(n.id, -1));
      d.set(s.id, 0);
      const queue = [s.id];
      while (queue.length > 0) {
        const v = queue.shift()!;
        this.adj.get(v)?.forEach(w => {
          if (d.get(w) === -1) {
            d.set(w, d.get(v)! + 1);
            totalPath += d.get(w)!;
            pathCount++;
            queue.push(w);
          }
        });
      }
    });

    return {
      nodeCount,
      edgeCount,
      density,
      avgClustering: totalClustering / nodeCount,
      avgShortestPath: pathCount > 0 ? totalPath / pathCount : 0,
      ngc: this.calculateNGC(this.nodes, this.edges),
    };
  }

  private calculateNGC(nodes: Node[], edges: Edge[]): number {
    if (nodes.length === 0) return 0;
    
    const adj = new Map<string, Set<string>>();
    nodes.forEach(n => adj.set(n.id, new Set()));
    edges.forEach(e => {
      // For NGC we treat it as undirected connectivity
      adj.get(e.source)?.add(e.target);
      adj.get(e.target)?.add(e.source);
    });

    const visited = new Set<string>();
    let maxComponentSize = 0;

    nodes.forEach(node => {
      if (!visited.has(node.id)) {
        let currentSize = 0;
        const queue = [node.id];
        visited.add(node.id);
        while (queue.length > 0) {
          const v = queue.shift()!;
          currentSize++;
          adj.get(v)?.forEach(neighbor => {
            if (!visited.has(neighbor)) {
              visited.add(neighbor);
              queue.push(neighbor);
            }
          });
        }
        maxComponentSize = Math.max(maxComponentSize, currentSize);
      }
    });

    return maxComponentSize / nodes.length;
  }

  public simulateRobustness(strategy: 'random' | 'degree' | 'betweenness' | 'pageRank' | 'domiRank'): RobustnessPoint[] {
    const points: RobustnessPoint[] = [];
    const steps = 20;
    
    // Pre-calculate metrics for targeted attacks
    let sortedNodeIds: string[] = [];
    if (strategy === 'random') {
      sortedNodeIds = [...this.nodes.map(n => n.id)].sort(() => Math.random() - 0.5);
    } else {
      const metrics = this.calculateAllMetrics();
      sortedNodeIds = [...this.nodes.map(n => n.id)].sort((a, b) => {
        const ma = metrics.get(a)!;
        const mb = metrics.get(b)!;
        if (strategy === 'degree') return mb.degree - ma.degree;
        if (strategy === 'betweenness') return mb.betweenness - ma.betweenness;
        if (strategy === 'pageRank') return mb.pageRank - ma.pageRank;
        if (strategy === 'domiRank') return mb.domiRank - ma.domiRank;
        return 0;
      });
    }

    for (let i = 0; i <= steps; i++) {
      const ratio = i / steps;
      const nodesToRemove = Math.floor(ratio * this.nodes.length);
      const remainingNodeIds = new Set(sortedNodeIds.slice(nodesToRemove));
      
      const remainingNodes = this.nodes.filter(n => remainingNodeIds.has(n.id));
      const remainingEdges = this.edges.filter(e => remainingNodeIds.has(e.source) && remainingNodeIds.has(e.target));
      
      points.push({
        removalRatio: ratio,
        ngc: this.calculateNGC(remainingNodes, remainingEdges),
        strategy
      });
    }

    return points;
  }
}
