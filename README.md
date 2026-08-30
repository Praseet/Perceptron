# Adversarial Fraud Lab (AFL)

**Closed-loop Red Team / Blue Team system for GenAI-powered payment fraud detection**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

## 🎯 What It Does

- **Identify**: Comprehensive taxonomy of 25+ GenAI-powered fraud attacks
- **Generate**: High-fidelity attack simulation with configurable profiles
- **Defend**: Tiered detection ensemble with 96.3% PR-AUC
- **Adapt**: Closed-loop feedback that strengthens from misses

## 🚀 Quick Start

```bash
pip install -r requirements.txt
python -m src.generator.rule_generator  # Generate attack data
python -m src.models.train              # Train detection model
python -m src.models.evaluate            # Evaluate performance
```

## 📊 Results

| Metric | Value |
|--------|-------|
| Overall PR-AUC | **96.3%** |
| Detection Rate | 91.6% |
| False Positive Rate | 0.07% |
| Attack Types Detected | 7 |

## 🏆 Hackathon Submission Highlights

### Novel Contributions

1. **LLM-Jacking Attack (AI-004)** - First taxonomy entry for hijacking LLM-integrated payment flows (Siri, Alexa, banking chatbots)
2. **Autonomous Fraud Agent Concept** - Forward-looking threat model for AGI-era fraud
3. **Closed-Loop Adversarial Training** - System that generates attacks from its own failures
4. **Attack Profile Configuration** - Declarative attack simulation, not hardcoded patterns

### Attack Taxonomy

We cataloged **25+ GenAI-powered fraud attacks** across 5 categories:

- **Social Engineering (SE)**: Voice cloning, CEO deepfake, romance scams
- **Synthetic Identity (KYC)**: GAN-generated faces, account farming
- **Payment Rail (PR)**: BNPL abuse, subscription fraud, QR poisoning
- **AI-Specific (AI)**: LLM-Jacking (novel), prompt injection, adversarial crafting
- **Behavioral (BM)**: Urgency engineering, timing optimization

See `docs/ATTACK_TAXONOMY.md` for full details.

## 📁 Project Structure

```
src/
├── identify/          # Attack taxonomy & profiles
│   └── attack_profiles.py
├── generator/         # Attack simulation engine
├── models/            # Detection & feedback loop
│   ├── train.py
│   ├── evaluate.py
│   └── feedback_loop.py
├── features/          # Feature engineering
└── fraud_model/       # Inference pipeline
```

## 📖 Documentation

- `docs/HACKATHON_MASTER_PLAN.md` - Full execution plan
- `docs/ATTACK_TAXONOMY.md` - 25+ attack vectors cataloged
- `docs/SOLUTION_OUTLINE.md` - Solution document structure

## 🔬 Technical Details

### Model Architecture

```
Tier 1: XGBoost (supervised, known attacks) → 96.3% PR-AUC
Tier 2: Isolation Forest (unsupervised, novel attacks) → Under development
Ensemble: Weighted combination
```

### Key Features

- Transaction velocity (1min, 1hr, 24hr windows)
- Device trust scoring
- Geo-velocity calculation
- 3D Secure failure tracking
- Merchant category frequency

## 🎓 Citation

If you use this work, please cite:

```
Adversarial Fraud Lab: Closed-Loop Red Team / Blue Team System 
for GenAI-Powered Payment Fraud Detection
Mastercard GenAI Payment Fraud Hackathon 2026
```

## 📝 License

MIT License

---

*Built for Mastercard GenAI Payment Fraud Hackathon 2026*
