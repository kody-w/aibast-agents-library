# Model Catalog Data

> SYNTHETIC — DEMO DATA. Every model, benchmark number, and provider in this
> document is fictional. This file exists so the agent has a working world to
> answer from on day one. In production, replace this file with tools that
> read your real model registry and MLOps platform (see the README's
> production section).

## Model catalog

| ID | Name | Task | Framework | Parameters | Size (MB) | Accuracy | F1 Score | Latency (ms) | License | Provider |
|----|------|------|-----------|------------|-----------|----------|----------|--------------|---------|----------|
| MDL-001 | SentimentBERT-v3 | Sentiment Analysis | PyTorch | 110M | 438 | 0.943 | 0.938 | 45 | Apache 2.0 | Internal ML Team |
| MDL-002 | DocClassifier-XL | Document Classification | TensorFlow | 340M | 1350 | 0.967 | 0.961 | 120 | MIT | AI Research Lab |
| MDL-003 | ChurnPredictor-v2 | Churn Prediction | scikit-learn | 2.5M | 12 | 0.891 | 0.874 | 8 | Proprietary | Data Science Team |
| MDL-004 | NER-Finance-v4 | Named Entity Recognition | spaCy | 85M | 320 | 0.952 | 0.947 | 32 | Apache 2.0 | NLP Team |
| MDL-005 | ImageQuality-ResNet | Image Quality Assessment | PyTorch | 25M | 98 | 0.928 | 0.921 | 15 | MIT | Computer Vision Team |
| MDL-006 | FraudDetector-Ensemble | Fraud Detection | XGBoost + PyTorch | 50M | 215 | 0.978 | 0.965 | 25 | Proprietary | Security ML Team |

## Training data and freshness

| ID | Name | Training Data | Last Updated |
|----|------|---------------|--------------|
| MDL-001 | SentimentBERT-v3 | 200K labeled reviews | 2025-09-15 |
| MDL-002 | DocClassifier-XL | 500K documents, 45 categories | 2025-10-01 |
| MDL-003 | ChurnPredictor-v2 | 150K customer records, 24-month history | 2025-08-20 |
| MDL-004 | NER-Finance-v4 | 80K financial documents | 2025-10-15 |
| MDL-005 | ImageQuality-ResNet | 100K images with quality labels | 2025-07-10 |
| MDL-006 | FraudDetector-Ensemble | 2M transactions, 18 months | 2025-11-01 |

## Accuracy bands

Band boundaries are fixed and half-open: `95%+` is `accuracy >= 0.95`,
`90-95%` is `0.90 <= accuracy < 0.95`, `Below 90%` is `accuracy < 0.90`.

| Band | Count | Models |
|------|-------|--------|
| 95%+ | 3 | MDL-006 (97.8%), MDL-002 (96.7%), MDL-004 (95.2%) |
| 90-95% | 2 | MDL-001 (94.3%), MDL-005 (92.8%) |
| Below 90% | 1 | MDL-003 (89.1%) |
