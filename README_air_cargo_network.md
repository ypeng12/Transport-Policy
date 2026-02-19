# Air Cargo Network Analysis (China) --- Research Codebase

This repository provides a structured and future-proof pipeline for
constructing and analyzing a **directed weighted air cargo network**
using complex network theory.

It is designed so that: - You can run it now with sample or partial
data - You can later plug in full real operational data - You will NOT
need to refactor the core architecture

------------------------------------------------------------------------

## Research Goal

Reproduce and extend complex network analysis of a domestic air cargo
system including:

-   Directed weighted graph construction
-   Node centrality analysis (Degree, Betweenness, Closeness, PageRank,
    DomiRank placeholder)
-   Network-level statistics (Density, Clustering, Shortest Path, NGC)
-   Targeted robustness simulations
-   Temporal aggregation (Monthly → Quarterly)

------------------------------------------------------------------------

## Data Requirement (Future-Ready Schema)

Place your dataset in:

    data/raw/flights.csv

Minimum required columns:

  Column   Description
  -------- ------------------------------------
  date     ISO format (YYYY-MM-DD or YYYY-MM)
  origin   IATA airport code
  dest     IATA airport code

Optional but recommended:

  Column           Description
  ---------------- --------------------
  flights          Number of flights
  aircraft_type    Aircraft model
  payload_tonnes   Payload per flight
  distance_km      Route distance

The pipeline will auto-handle missing optional fields when possible.

------------------------------------------------------------------------

## Project Structure

    air-cargo-network/
    ├─ README.md
    ├─ requirements.txt
    ├─ configs/config.yaml
    ├─ data/
    │  ├─ raw/
    │  ├─ processed/
    │  └─ sample/
    ├─ src/
    │  ├─ schemas.py
    │  ├─ io.py
    │  ├─ preprocess.py
    │  ├─ build_graph.py
    │  ├─ metrics.py
    │  ├─ robustness.py
    │  ├─ viz.py
    │  └─ pipeline.py
    └─ scripts/run_pipeline.py

------------------------------------------------------------------------

## How to Run

1.  Install dependencies:

```{=html}
<!-- -->
```
    pip install -r requirements.txt

2.  Place your data in:

```{=html}
<!-- -->
```
    data/raw/flights.csv

3.  Update configuration if needed:

```{=html}
<!-- -->
```
    configs/config.yaml

4.  Run:

```{=html}
<!-- -->
```
    python scripts/run_pipeline.py --config configs/config.yaml

------------------------------------------------------------------------

## Outputs

Saved automatically in:

    data/processed/

Includes:

-   Aggregated OD edges
-   Node centrality tables
-   Network statistics
-   Robustness simulation results
-   Plots (PNG)

------------------------------------------------------------------------

## Robustness Simulation

Supports targeted removal strategies:

-   degree
-   betweenness
-   pagerank
-   domirank (placeholder for future implementation)

Removes nodes progressively and tracks:

NGC (Normalized Giant Component)

------------------------------------------------------------------------

## Extension Roadmap

Future improvements may include:

-   Full DomiRank dynamical implementation
-   PyTorch Geometric integration
-   Link prediction models
-   Flow forecasting
-   Graph embedding experiments

------------------------------------------------------------------------

## Design Philosophy

-   Data contract first
-   Modular architecture
-   No refactor when real data arrives
-   Paper-ready structure
-   Research reproducibility focus

------------------------------------------------------------------------

Author: (Your Name)
