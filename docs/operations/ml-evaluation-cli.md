# ML evaluation CLI

The Phase 4 evaluation runner is available as a project command:

```powershell
uv run sentinel-ml-evaluate tests/fixtures/behavioral_evaluation.jsonl `
  --training-count 2 `
  --output artifacts/behavioral-evaluation.json
```

Without `--output`, the report is printed as sorted, indented JSON. The report includes training and evaluation sample counts, per-detector metrics, the selected model by F1, and any estimator skipped because its runtime dependency is unavailable.

The output file is intended for CI artifacts and recruiter-readable evidence. It should be accompanied by the fixture version and configuration used for the run.
