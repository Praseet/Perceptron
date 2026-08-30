# GenAI-Powered Payment Fraud Attack Taxonomy
## Adversarial Fraud Lab - Attack Classification Framework

**Version**: 1.0 | **Date**: August 28, 2026

---

## Category Overview

| Category | Attack Count | Avg Feasibility |
|----------|--------------|-----------------|
| **A: AI-Generated Social Engineering** | 6 | High |
| **B: Synthetic Identity & KYC Fraud** | 5 | Medium-High |
| **C: Payment Rail Exploitation** | 5 | Medium |
| **D: AI-Specific Attacks (NOVEL)** | 5 | High |
| **E: Behavioral Manipulation** | 4 | High |

---

## CATEGORY A: AI-Generated Social Engineering

### SE-001: Voice Clone Impersonation
- **Description**: Deepfake voice of family member requesting urgent payment
- **Feasibility**: ⭐⭐⭐⭐⭐ High
- **Status**: ✅ Partial (ai_impersonation)
- **Detection**: Transaction velocity + first-time recipient

### SE-002: CEO Fraud Deepfake
- **Description**: Video deepfake of executive authorizing wire transfer
- **Feasibility**: ⭐⭐⭐ Medium
- **Status**: 🔜 Conceptual

### SE-003: Romance Scam Automation
- **Description**: AI chatbot managing 100+ romantic relationships
- **Feasibility**: ⭐⭐⭐⭐⭐ High
- **Status**: ✅ Partial (ai_impersonation)

### SE-004: Customer Service Impersonation
- **Description**: AI voice bot extracting credentials
- **Feasibility**: ⭐⭐⭐⭐⭐ High
- **Status**: ✅ Partial (ai_impersonation)

### SE-005: Investment Scam Bot
- **Description**: AI personalized investment pitches
- **Feasibility**: ⭐⭐⭐⭐⭐ High
- **Status**: ✅ Partial (ai_impersonation)

### SE-006: Charity Fraud at Scale
- **Description**: AI fake charity campaigns
- **Feasibility**: ⭐⭐⭐⭐⭐ High
- **Status**: ✅ Implemented

---

## CATEGORY B: Synthetic Identity & KYC Fraud

### KYC-001: Deepfake Identity Verification
- **Description**: Real-time deepfake for video KYC
- **Feasibility**: ⭐⭐⭐ Medium
- **Status**: 🔜 Conceptual

### KYC-002: Synthetic Identity Creation ⭐ PRIORITY
- **Description**: GAN-generated face + AI-written profile
- **Feasibility**: ⭐⭐⭐⭐⭐ High
- **Status**: 🔜 **TO IMPLEMENT**

### KYC-003: Document Forgery Automation
- **Description**: AI fake IDs, passports
- **Feasibility**: ⭐⭐⭐ Medium
- **Status**: 🔜 Conceptual

### KYC-004: Account Farming Botnet ⭐ PRIORITY
- **Description**: Automated creation/aging of accounts
- **Feasibility**: ⭐⭐⭐⭐ High
- **Status**: 🔜 **TO IMPLEMENT**

### KYC-005: Biometric Spoofing
- **Description**: Fingerprint/face auth bypass
- **Feasibility**: ⭐⭐ Low
- **Status**: ⏸️ Future

---

## CATEGORY C: Payment Rail Exploitation

### PR-001: UPI Intent Hijacking
- **Description**: Malicious app intercepts UPI payment
- **Status**: 🔜 Conceptual

### PR-002: QR Code Poisoning
- **Description**: Fake QR codes redirecting payments
- **Status**: 🔜 Conceptual

### PR-003: BNPL Identity Abuse ⭐ PRIORITY
- **Description**: Synthetic identity for BNPL max-out
- **Status**: 🔜 **TO IMPLEMENT**

### PR-004: Cross-Border Arbitrage
- **Description**: FX rate exploitation
- **Status**: 🔜 Conceptual

### PR-005: Subscription Creep
- **Description**: Multiple small subscriptions
- **Status**: 🔜 **TO IMPLEMENT**

---

## CATEGORY D: AI-Specific Attacks (NOVEL)

### AI-001: Prompt Injection Fraud
- **Description**: Manipulating AI chatbot to reveal credentials
- **Status**: 🔜 **NOVEL**

### AI-002: Model Extraction Attack
- **Description**: Probing fraud API to steal model
- **Status**: 🔜 Conceptual

### AI-003: Adversarial Transaction Crafting
- **Description**: ML-evasive transaction patterns
- **Status**: 🔜 Closed-loop focus

### AI-004: LLM-Jacking ⭐ NOVEL CONTRIBUTION
- **Description**: Hijacking LLM-integrated payment flows (Siri, Alexa)
- **Status**: 🔜 **NOVEL - KEY DIFFERENTIATOR**

### AI-005: Autonomous Fraud Agent ⭐ NOVEL CONTRIBUTION
- **Description**: AI agent autonomously planning/executing fraud
- **Status**: 🔜 **NOVEL - CONCEPTUAL**

---

## CATEGORY E: Behavioral Manipulation

### BM-001: Urgency Engineering
- **Status**: ✅ Implemented

### BM-002: Trust Calibration
- **Status**: 🔜 Conceptual

### BM-003: Timing Optimization
- **Status**: 🔜 Conceptual

### BM-004: Multi-Channel Orchestration
- **Status**: 🔜 Conceptual

---

## Implementation Priority

| Priority | Attack | Impact |
|----------|--------|--------|
| **P0** | KYC-002: Synthetic Identity | High |
| **P0** | PR-003: BNPL Abuse | High |
| **P0** | AI-004: LLM-Jacking | Very High |
| **P1** | KYC-004: Account Farming | High |
| **P1** | PR-005: Subscription Creep | Medium |

---

## Novel Contributions

1. **LLM-Jacking (AI-004)**: First taxonomy for LLM-payment attacks
2. **Autonomous Fraud Agent (AI-005)**: AGI-era fraud concept
3. **Closed-Loop Adversarial Training**: Attacks from detection failures

*Total: 25 Attacks | Novel: 3*
