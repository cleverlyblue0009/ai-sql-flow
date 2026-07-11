# Results Manifest — Phase 2 Rebuild

> Every artefact promised by the rebuild lives here with a path, generator
> script, and current status. Empty rows are intentional: they document what
> has *not* yet been produced. Phase N updates fill in the corresponding rows
> rather than retro-actively rewriting earlier entries.

| Category | Artefact | Path | Generator | Status |
|---|---|---|---|---|
| Raw data | SEC EDGAR 2024Q4 ZIP | `phase2_rebuild/data/raw/sec_edgar/2024q4.zip` | `scripts/00_download_datasets.py` | **on disk (Phase 1)** |
| Raw data | NYC Payroll CSV | `phase2_rebuild/data/raw/nyc_payroll/citywide_payroll.csv` | `scripts/00_download_datasets.py` | **on disk (Phase 1)** |
| Raw data | UCI Credit Default XLS | `phase2_rebuild/data/raw/uci_credit_default/default_of_credit_card_clients.zip` | `scripts/00_download_datasets.py` | **on disk (Phase 1)** |
| Provenance | Download manifest | `phase2_rebuild/data/download_manifest.json` | `scripts/00_download_datasets.py` | **on disk (Phase 1)** |
| Plan | Anomaly injection plan | `phase2_rebuild/anomaly_injection_plan.md` | hand-authored | **complete (Phase 1)** |
| Plan | Dataset registry | `phase2_rebuild/dataset_registry.md` | hand-authored | **complete (Phase 1)** |
| Log | Experiment log | `phase2_rebuild/experiment_log.md` | hand-authored, append-only | **active** |
| Processed | D1 sampled GL slice (parquet) | `phase2_rebuild/data/processed/D1_sec_gl.parquet` | `scripts/01_extract_and_sample.py` | **on disk (Phase 2)** |
| Processed | D2 NYC FY2024 slice (parquet) | `phase2_rebuild/data/processed/D2_nyc_fy2024.parquet` | `scripts/01_extract_and_sample.py` | **on disk (Phase 2)** |
| Processed | D3 UCI parquet | `phase2_rebuild/data/processed/D3_uci_credit.parquet` | `scripts/01_extract_and_sample.py` | **on disk (Phase 2)** |
| Processed | D1 injected (real + anomalies) | `phase2_rebuild/data/processed/D1_injected.parquet` | `scripts/02_inject_anomalies.py` | **on disk (Phase 2)** |
| Processed | D2 injected (real + anomalies) | `phase2_rebuild/data/processed/D2_injected.parquet` | `scripts/02_inject_anomalies.py` | **on disk (Phase 2)** |
| Processed | D3 injected (real + anomalies) | `phase2_rebuild/data/processed/D3_injected.parquet` | `scripts/02_inject_anomalies.py` | **on disk (Phase 2)** |
| Labels | D1 anomaly mask | `phase2_rebuild/data/labels/D1_mask.parquet` | `scripts/02_inject_anomalies.py` | **on disk (Phase 2)** |
| Labels | D2 anomaly mask | `phase2_rebuild/data/labels/D2_mask.parquet` | `scripts/02_inject_anomalies.py` | **on disk (Phase 2)** |
| Labels | D3 anomaly mask | `phase2_rebuild/data/labels/D3_mask.parquet` | `scripts/02_inject_anomalies.py` | **on disk (Phase 2)** |
| Provenance | Extract manifest | `phase2_rebuild/data/extract_manifest.json` | `scripts/01_extract_and_sample.py` | **on disk (Phase 2)** |
| Provenance | Injection manifest (counts + SHA256) | `phase2_rebuild/data/injection_manifest.json` | `scripts/02_inject_anomalies.py` | **on disk (Phase 2)** |
| Metrics | Baseline comparison table | `phase2_rebuild/results/tables/baseline.csv` | `scripts/10_run_baseline.py` | pending (Phase 3) |
| Metrics | Ablation table | `phase2_rebuild/results/tables/ablation.csv` | `scripts/11_run_ablation.py` | pending (Phase 3) |
| Metrics | Cross-validation table | `phase2_rebuild/results/tables/cv.csv` | `scripts/12_run_cv.py` | pending (Phase 3) |
| Metrics | Scalability table | `phase2_rebuild/results/tables/scalability.csv` | `scripts/13_run_scalability.py` | pending (Phase 3) |
| Metrics | Threshold sweep table | `phase2_rebuild/results/tables/threshold_sweep.csv` | `scripts/14_run_threshold_sweep.py` | pending (Phase 3) |
| Metrics | Operating-mode summary (recall / balanced / precision) | `phase2_rebuild/results/tables/operating_modes.csv` | `scripts/15_run_operating_modes.py` | pending (Phase 3) |
| Figures | Baseline bar chart | `phase2_rebuild/results/figures/fig2_baseline_comparison.pdf` | `scripts/20_make_baseline_fig.py` | pending (Phase 4) |
| Figures | Ablation chart | `phase2_rebuild/results/figures/fig1_ablation_study.pdf` | `scripts/21_make_ablation_fig.py` | pending (Phase 4) |
| Figures | Scalability plot | `phase2_rebuild/results/figures/fig3_scalability.pdf` | `scripts/22_make_scalability_fig.py` | pending (Phase 4) |
| Figures | Confusion matrices | `phase2_rebuild/results/figures/fig6_confusion_matrices.pdf` | `scripts/23_make_confusion_fig.py` | pending (Phase 4) |
| Figures | Confidence distributions | `phase2_rebuild/results/figures/fig5_confidence_distributions.pdf` | `scripts/24_make_confidence_fig.py` | pending (Phase 4) |
| Figures | PR curves (NEW per rebuild spec) | `phase2_rebuild/results/figures/figN_pr_curves.pdf` | `scripts/25_make_pr_curves.py` | pending (Phase 4) |
| Figures | Threshold vs F1 / FPR / review-workload (NEW per rebuild spec) | `phase2_rebuild/results/figures/figN_threshold_sweep.pdf` | `scripts/26_make_threshold_sweep_fig.py` | pending (Phase 4) |
| Figures | Robustness under noise | `phase2_rebuild/results/figures/fig4_robustness.pdf` | `scripts/27_make_robustness_fig.py` | pending (Phase 4) |
| Figures | Security / adversarial | `phase2_rebuild/results/figures/fig9_security_validation.pdf` | `scripts/28_make_security_fig.py` | pending (Phase 4) |
| Figures | Enterprise pipeline waterfall | `phase2_rebuild/results/figures/fig8_enterprise_pipeline.pdf` | `scripts/29_make_enterprise_fig.py` | pending (Phase 4) |
| Paper | Rebuilt IEEE Access .tex | `paper/dataflow_ai_v2.tex` | hand-authored against new tables/figures | pending (Phase 4) |
| Paper | Citation-order audit | `phase2_rebuild/audit/citation_order.json` | `scripts/40_audit_citations.py` | pending (Phase 5) |
| Paper | Metric-consistency audit | `phase2_rebuild/audit/metric_consistency.json` | `scripts/41_audit_metrics.py` | pending (Phase 5) |
| Paper | Figure↔table cross-ref audit | `phase2_rebuild/audit/figure_table_xref.json` | `scripts/42_audit_xref.py` | pending (Phase 5) |
| Repro | Reproducibility report | `phase2_rebuild/reproducibility_report.md` | hand-authored | pending (Phase 5) |
