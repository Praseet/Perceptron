# Mastercard GenAI Payment Fraud Hackathon - Master Execution Plan
## Deadline: August 31, 2026 | Current: August 28, 2026 | Time Remaining: 3 Days

---

## Project Identity: "Adversarial Fraud Lab (AFL)"

**Tagline**: *Closed-loop Red Team / Blue Team system for GenAI-powered payment fraud*

**Elevator Pitch**: 
AFL is an end-to-end adversarial AI system that doesn't just detect fraud — it **simulates evolving attack patterns** using GenAI, **hardens defenses** through continuous stress-testing, and **closes the loop** by feeding detection gaps back into attack generation. This is the future of fraud prevention: an AI that thinks like a fraudster to outsmart fraudsters.

---

## Hackathon Requirements Checklist

| Requirement | Status | Priority | Target Date |
|-------------|--------|----------|-------------|
| Identify - Novel GenAI fraud taxonomy | 🔴 Not Started | P0 | Day 1 |
| Generate - Attack simulation engine | 🟡 Partial | P0 | Day 1-2 |
| Defend - Detection model | 🟢 Strong | P1 | Day 2 |
| Closed-loop feedback system | 🟡 Partial | P0 | Day 2 |
| Code Repository (clean, documented) | 🟡 Partial | P1 | Day 3 |
| Solution Walkthrough (.docx) | 🔴 Not Started | P0 | Day 2-3 |
| Web Prototype (Streamlit) | 🔴 Not Started | P2 | Day 3 |

---

## PHASE 1: IDENTIFY - Attack Taxonomy (Day 1)
### Goal: Comprehensive GenAI-powered fraud attack catalog

### 1.1 Attack Categories

**CATEGORY A: AI-Generated Social Engineering**
| Attack ID | Attack Name | Description | Feasibility |
|-----------|-------------|-------------|-------------|
| SE-001 | Voice Clone Impersonation | Deepfake voice of family member requesting urgent payment | High |
| SE-002 | CEO Fraud Deepfake | Video deepfake of executive authorizing wire transfer | Medium |
| SE-003 | Romance Scam Automation | AI chatbot nurturing multiple victims simultaneously | High |
| SE-004 | Customer Service Impersonation | AI voice bot extracting credentials during fake support call | High |
| SE-005 | Investment Scam Bot | AI generating personalized crypto investment pitches | High |
| SE-006 | Charity Fraud at Scale | AI generating urgent donation requests for fake causes | High |

**CATEGORY B: Synthetic Identity & KYC Fraud**
| Attack ID | Attack Name | Description | Feasibility |
|-----------|-------------|-------------|-------------|
| KYC-001 | Deepfake Identity Verification | AI-generated face during video KYC | Medium |
| KYC-002 | Synthetic Identity Creation | GAN-generated faces + AI-written profiles | High |
| KYC-003 | Document Forgery Automation | AI generating realistic fake IDs/passports | Medium |
| KYC-004 | Account Farming Botnet | AI creating and aging multiple synthetic accounts | High |
| KYC-005 | Biometric Spoofing | Presentation attacks on fingerprint/face auth | Low |

**CATEGORY C: Payment Rail Exploitation**
| Attack ID | Attack Name | Description | Feasibility |
|-----------|-------------|-------------|-------------|
| PR-001 | UPI Intent Hijacking | Malicious apps intercepting UPI payment intents | Medium |
| PR-002 | QR Code Poisoning | AI-generated malicious QR codes for payment redirect | Medium |
| PR-003 | BNPL Identity Abuse | Using synthetic identities for buy-now-pay-later | High |
| PR-004 | Cross-Border Arbitrage | Exploiting FX rates across payment rails | Medium |
| PR-005 | Subscription Creep | Gradual unauthorized subscription enrollments | High |

**CATEGORY D: AI-Specific Attacks (NOVEL - Key Differentiator)**
| Attack ID | Attack Name | Description | Feasibility |
|-----------|-------------|-------------|-------------|
| AI-001 | Prompt Injection Fraud | Manipulating AI chatbot to reveal payment credentials | High |
| AI-002 | Model Extraction Attack | Stealing fraud detection model via API probing | Low |
| AI-003 | Adversarial Transaction Crafting | ML-evasive transaction patterns | Medium |
| AI-004 | LLM-Jacking | Hijacking LLM-integrated payment flows | High |
| AI-005 | Autonomous Fraud Agent | AI agent autonomously executing multi-step fraud | High |

**CATEGORY E: Behavioral Manipulation**
| Attack ID | Attack Name | Description | Feasibility |
|-----------|-------------|-------------|-------------|
| BM-001 | Urgency Engineering | AI optimizing pressure tactics for maximum compliance | High |
| BM-002 | Trust Calibration | AI matching communication style to victim profile | Medium |
| BM-003 | Timing Optimization | AI identifying optimal moment for fraud attempt | High |
| BM-004 | Multi-Channel Orchestration | Coordinated attack across SMS, email, phone | High |

### 1.2 Novel Contributions (Our Differentiators)

1. **LLM-Jacking Attack (AI-004)** - Novel attack where fraudsters hijack LLM-integrated payment assistants (Siri, Alexa, banking chatbots) via voice injection or prompt manipulation
2. **Autonomous Fraud Agent (AI-005)** - Concept of AI agent that can plan, execute, and adapt fraud campaigns without human intervention
3. **Closed-Loop Adversarial Training** - System that generates attacks from its own failures

---

## PHASE 2: GENERATE - Attack Simulation Engine (Day 1-2)
### Goal: High-fidelity, configurable attack generation

### 2.1 Current Generator Assessment
**Strengths:** 5 fraud types, temporal consistency, user behavior modeling
**Weaknesses:** Limited diversity, LLM disconnected, no attack configuration API

### 2.2 Required New Fraud Types

| New Fraud Type | Key Features | Priority |
|----------------|--------------|----------|
| `synthetic_identity` | New identity, no history, gradual buildup | P0 |
| `account_farming` | Multiple accounts from same device/IP | P1 |
| `bnpl_abuse` | High-value purchases, default pattern | P0 |
| `subscription_fraud` | Small recurring charges, long duration | P1 |

### 2.3 Attack Profile Configuration
```python
ATTACK_PROFILES = {
    "voice_clone_scam": {
        "fraud_type": "ai_impersonation",
        "urgency": "high",
        "amount_range": (500, 5000),
        "detection_evasion": ["normal_device", "normal_geo"]
    }
}
```

### 2.4 LLM Strategy (Real-World Ready)
Use LLM for **attack pattern generation**, not runtime detection:
1. Generate attack scripts → encode into transaction patterns
2. Create behavioral profiles → inform amount/timing
3. Simulate fraudster adaptation → feedback loop

---

## PHASE 3: DEFEND - Detection Model (Day 2)

### 3.1 Current Performance
- Tier 1 XGBoost: 96.3% PR-AUC ✅
- Tier 2 Isolation Forest: 6.2% PR-AUC ❌

### 3.2 Improvements
**Replace Tier 2 with Autoencoder** for unsupervised novel attack detection

### 3.3 Explainability
- SHAP values for every prediction
- Natural language explanations
- "Red flags" highlighting

---

## PHASE 4: CLOSED-LOOP FEEDBACK (Day 2)

### 4.1 System Design
```
DEFEND → DETECT → ANALYZE → GENERATE → RETRAIN
    ▲                                    │
    └────────────────────────────────────┘
```

### 4.2 Implementation
1. Detect false negatives on validation
2. Analyze failure patterns
3. Generate evasive attacks
4. Retrain and measure improvement

---

## PHASE 5: SOLUTION DOCUMENT (Day 2-3)

### 5.1 Document Structure
```
SOLUTION_WALKTHROUGH.docx
├── 1. Executive Summary (1 page)
├── 2. Identify: Attack Taxonomy (3-4 pages)
├── 3. Generate: Attack Simulation (2-3 pages)
├── 4. Defend: Detection System (2-3 pages)
├── 5. Closed-Loop Feedback (2 pages)
├── 6. Real-World Feasibility (1-2 pages)
├── 7. Novel Contributions (1 page)
└── 8. Appendices
```

### 5.2 Key Narrative
1. "We simulate the attacker's mind, not just detect their actions"
2. "Every miss makes the system stronger"
3. "Designed for 2026+ GenAI fraud era"
4. "Novel: LLM-Jacking attack vector"

---

## PHASE 6: CODE RESTRUCTURE (Day 3)

### 6.1 New Structure
```
src/
├── identify/        # Attack taxonomy & profiles
├── generate/        # Attack simulation engine
├── defend/          # Detection & inference
├── feedback/        # Closed-loop system
└── api/             # Web prototype
```

---

## EXECUTION CHECKPOINTS

### ✅ Checkpoint 1: End of Day 1 (Aug 28)
- [ ] Attack taxonomy document (15+ attacks)
- [ ] 2-3 new fraud types implemented
- [ ] Attack profile system
- [ ] LLM reframed for attack generation

### ✅ Checkpoint 2: End of Day 2 (Aug 29)
- [ ] Enhanced feedback loop
- [ ] Tier 2 replaced (Autoencoder)
- [ ] Solution document draft
- [ ] Code restructured

### ✅ Checkpoint 3: End of Day 3 (Aug 30)
- [ ] Web prototype functional
- [ ] README professional
- [ ] All tests passing

### ✅ Checkpoint 4: Submission (Aug 31)
- [ ] Final testing
- [ ] Demo video backup
- [ ] All artifacts submitted

---

## SUCCESS METRICS

| Metric | Target | Current |
|--------|--------|---------|
| Attack types identified | 15+ | 5 |
| Attack types simulated | 8+ | 5 |
| Overall PR-AUC | 95%+ | 96.3% ✅ |
| FN reduction via feedback | 30%+ | ~10% |
| Novel contributions | 3+ | 0 |

---

## IMMEDIATE ACTION ORDER

1. **NOW**: Create `docs/ATTACK_TAXONOMY.md` (full catalog)
2. **NEXT**: Implement `synthetic_identity` fraud type
3. **NEXT**: Implement `bnpl_abuse` fraud type
4. **NEXT**: Build attack profile configuration
5. **NEXT**: Enhance feedback loop with failure analyzer
6. **NEXT**: Replace Tier 2 with Autoencoder
7. **NEXT**: Create solution document (.docx)
8. **LAST**: Web prototype + cleanup

---

*Status: READY FOR EXECUTION - Starting Phase 1*




