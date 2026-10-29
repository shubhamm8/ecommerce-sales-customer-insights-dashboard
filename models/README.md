# Models Directory

This directory stores persisted machine learning artifacts and pipeline metadata generated during dashboard sessions (e.g., fitted Scikit-Learn KMeans clusters, scalers, and forecasting baselines).

## Storage & Git Hygiene Guidelines

- Trained model binaries (`*.joblib`, `*.pkl`) are transient and can be regenerated deterministically.
- All model binaries are excluded by `.gitignore` to prevent repository bloat and ensure zero proprietary data leaks.
- To re-fit models, run the corresponding module scripts or trigger them via the interactive dashboard interface.
