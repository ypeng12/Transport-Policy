# Air Cargo Network Analysis

This repository provides an automated pipeline based on complex network theory to analyze the structural characteristics, node importance, and robustness of air cargo networks (specifically tailored for China's domestic system).

![Network Topology](<img width="1531" height="1253" alt="image" src="https://github.com/user-attachments/assets/708f7c1b-6027-4da6-9fe9-beec404207e8" />
)

## Core Features

- **Directed Weighted Graph Construction**: Abstraction of "Airports + Routes" into a complex network, with weights integrating flight frequency, aircraft payload, and total capacity.
- **Multi-dimensional Centrality Analysis**:
  - **Degree Centrality**: Measures direct connectivity and throughput.
  - **Betweenness Centrality**: Identifies "bridge" nodes and transit hubs essential for network flow.
  - **Closeness Centrality**: Measures the average distance from an airport to all other nodes in the network.
  - **PageRank**: Identifies core nodes validated by their connection to other important hubs.
  - **DomiRank (Innovative Metric)**: Dynamically simulates competition and dominance between airports to identify local regional controllers.
- **Network Topology Statistics**: Detailed metrics including Density, Clustering Coefficient, Average Shortest Path Length, and Normalized Giant Component (NGC).
- **Robustness Simulation**: Quantitative analysis of network resilience against directed attacks (targeting core hubs) and random failures.
- **Automated Visualization**: Generation of publication-ready charts (6+ types) including network graphs, heatmap, and robustness curves.

---

## Quick Start

### 1. Installation
Ensure you have Python 3.8+ installed. Install the required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Data Preparation
Place your raw flight data (CSV format) in `data/raw/flights.csv`.

**Data Requirements:**
| Column | Description | Example |
|---|---|---|
| `date` | Timestamp (YYYY-MM) | 2024-01 |
| `origin` | Origin Airport IATA Code | PVG |
| `dest` | Destination Airport IATA Code | PEK |
| `flights` | Number of Flights (Optional) | 120 |
| `payload_tonnes` | Capacity per Flight (Optional) | 100 |

### 3. Run Analysis
Execute the full pipeline (Load -> Compute -> Simulate -> Plot):
```bash
python scripts/run_pipeline.py --config configs/config.yaml
```

---

## Project Structure

```text
air-cargo-network/
├─ configs/
│  └─ config.yaml        # Central configuration (weights, thresholds, colormaps)
├─ data/
│  ├─ raw/               # Raw input data
│  └─ processed/         # Computed results and exported visualizations
├─ src/                  # Core calculation engine
│  ├─ metrics.py         # Node & Network metrics (including DomiRank solver)
│  ├─ robustness.py      # Targeted & Random attack simulations
│  ├─ build_graph.py     # NetworkX graph construction
│  ├─ viz.py             # Matplotlib/Seaborn scientific plotting
│  └─ pipeline.py        # Workflow orchestration
└─ scripts/
   └─ run_pipeline.py    # Production entry point
```

---

## Metrics Glossary

1. **DomiRank (Dominance Rank)**:
   Unlike PageRank’s "rank transfer," DomiRank reflects the degree of dominance a node exerts within its neighborhood. If an airport is surrounded by weakly connected nodes, its dominance score increases significantly. This effectively identifies secondary regional hubs that PageRank might overlook.
2. **NGC (Normalized Giant Component)**:
   The ratio of nodes in the largest connected component to the total nodes. When the network is under attack, a slower decline in NGC indicates higher structural robustness.
3. **Clustering Coefficient**:
   Measures whether an airport’s "neighbors' neighbors" are also its neighbors. A high clustering coefficient implies tight local connections and high redundancy.

---

## Output Preview

All analysis results are automatically saved to the `data/processed/` directory:
- `node_centralities.csv`: Detailed 5-dimension scores for every airport.
- `network_stats.json`: Global network performance statistics.
- `robustness_results.csv`: Raw data from robustness simulations.
- `*.png`: Visualizations including Network Graph, Centrality Bar Charts, Heatmap, Robustness Curves, etc.

---

## Credits

Developed by **Yuliang Peng**. If you use this codebase in your academic research, please cite this repository.

---
*Design Philosophy: Data contract first, research reproducibility focus.*
