# ML Models & Techniques Playbook
### Mastercard GenAI Payment Fraud Hackathon — Identify / Generate / Defend

This is a complete map of every technique relevant to your project, explained properly (real terminology, defined the first time it appears), and sequenced by what to build **first** given: a 5-person team, ~10 days, and an intro-ML skill level (Andrew Ng's course + Andrej Karpathy's neural network series).

**How to read this**: Tier 1 is your minimum viable, fully-achievable submission. Tier 2 strengthens it if Tier 1 finishes early. Tier 3 is genuine stretch/novelty — attempt only if ahead of schedule, and frame it as "we prototyped this" rather than a core deliverable.

---

## 0. Lock these down before writing any model code (Day 1, no ML yet)

- **Fix your transaction/event schema.** Decide every field your synthetic data will have — amount, timestamp, merchant category, device ID, IP/geo, account age, etc. — before you generate a single row. Changing the schema later means redoing both your generator and your detector.
- **Pick your 10–15 core features up front** (see Feature Engineering below) so your generator and detector are built against the same fields from day one.
- **Generate behavioral sequences, not single labeled rows.** A fraud "case" should be a short sequence of events — e.g., two normal transactions → device change → burst of six transactions in three minutes → new geography — rather than one row tagged `fraud=1`. This is more realistic, closer to how real fraud unfolds, and lets your detector learn *drift over time*, not just a static threshold on one row.

---

## Foundations — matter more than which model you pick

### Feature engineering
Raw columns (amount, timestamp, merchant) rarely carry enough signal on their own. Most of the real "signal" in fraud detection comes from **engineered features**:
- **Velocity features**: number of transactions by this card/account in the last 1 min / 1 hr / 24 hr
- **Aggregation features**: this transaction's amount vs. this specific user's 30-day average (is it unusual *for them*, not just in general)
- **Time-since-last-transaction**: fraud often arrives in rapid bursts
- **Geo-velocity ("impossible travel")**: distance between two consecutive transaction locations divided by the time between them — a transaction in New York 10 minutes after one in Tokyo is physically impossible and a very strong signal

A simple model with good engineered features usually beats a complex model fed only raw columns.

### Train/test splitting — get this wrong and your results are meaningless
Fraud data is **temporal** — it has a time order, and fraud patterns evolve. Randomly shuffling rows into train/test sets lets information from the future leak into training, inflating your metrics in a way that won't hold up on new data. Use a **temporal split**: train on earlier transactions, test on later ones. This mimics real deployment, where you're always predicting on data you haven't seen yet.

**Dataset-specific caution**: if you use PaySim, its balance fields (`oldbalanceOrg`, `newbalanceOrig`, etc.) can leak the fraud label almost perfectly if used naively — a well-documented quirk of that dataset. If your model suddenly looks 99%+ accurate, treat that as a sign of leakage, not a sign your model is great — check whether you're accidentally handing it the answer.

### Evaluation metrics — not accuracy
- **Precision**: of everything flagged as fraud, what fraction actually was (controls false positives)
- **Recall**: of everything that was actually fraud, what fraction you caught (controls false negatives)
- **F1**: harmonic mean of precision and recall, one balanced number
- **PR-AUC (Precision-Recall Area Under Curve)**: the area under the precision-recall curve as you vary your decision threshold. **Prefer this over ROC-AUC.** ROC-AUC factors in the true-negative rate, and when 99%+ of transactions are legitimate, true negatives are so easy to rack up that ROC-AUC looks artificially high even for a mediocre model. PR-AUC only reflects performance on the rare positive (fraud) class — what you actually care about.
- **Cost-sensitive framing**: state plainly that a false positive (blocking a real customer) and a false negative (missing real fraud) cost different amounts in the real world. Reporting "at this threshold we catch X% of fraud while wrongly blocking Y% of legitimate transactions" shows judges you understand the actual tradeoff banks face — more convincing than a single F1 number.

---

## TIER 1 — Build first (your minimum viable submission)

### 1. Gradient-boosted decision trees — XGBoost or LightGBM
**What it is**: An **ensemble** method. Instead of one model, you build many small decision trees in sequence, where each new tree is trained specifically to correct the errors ("residuals") of the trees before it — this sequential error-correction is what "boosting" means (as opposed to "bagging," like Random Forest, where trees are built independently and their votes averaged).

**Why first**: this is the actual industry standard for tabular fraud detection, not a simplification for beginners — production fraud systems genuinely use this, layered with more infrastructure around it. No GPU needed, trains in seconds to minutes, handles missing values natively, no feature scaling required.

**Key setting — `scale_pos_weight`**: tells the model "the fraud class is rare, weight mistakes on it more heavily." Set it to roughly (# legitimate transactions ÷ # fraud transactions). This one setting fixes most of your class-imbalance problem before you need anything fancier.

**Library**: `xgboost` or `lightgbm` — `pip install`, scikit-learn-compatible API.

### 2. SMOTE — class imbalance handling
**What it is**: **SMOTE (Synthetic Minority Oversampling Technique)** generates new synthetic fraud examples by taking a real fraud example, finding its nearest neighbors (other fraud examples close to it in feature space), and creating new synthetic points along the line connecting them — giving your model more fraud examples without simply duplicating existing ones (which causes overfitting to those exact points).

**Use alongside `scale_pos_weight`, not instead of it** — try both, compare. Library: `imbalanced-learn` (`pip install imbalanced-learn`).

### 3. Rule-based / statistical synthetic transaction generation (your first Generate-pillar model)
**What it is**: not a trained model at all — a **statistical simulator**. Take the *distribution* of real transactions (amounts follow a certain shape, timestamps cluster at certain hours) and write code that samples from similar distributions while injecting fraud-specific patterns: rapid bursts of small amounts (card testing), incrementing amounts (BIN-attack probing), impossible-travel sequences, or the behavioral-drift sequences described in Section 0.

**Why this is legitimate, not "cheating"**: the brief scores you on **fidelity** — how realistic the output is — not on how mathematically sophisticated the generation method is. A well-tuned statistical simulator matching real distributions can outperform a poorly-trained neural generator.

### 4. LLM prompting for conversational attack generation
**What it is**: using a pretrained LLM (via API — whichever the hackathon provides credits for) through **prompting**, not training:
- **Zero-shot / few-shot prompting**: giving the model instructions (and optionally a few examples) of the behavior you want, without updating any of its internal weights — you're relying entirely on capabilities it already has
- **Role-play loop**: prompt one instance to play "scammer impersonating support," get a reply, feed that into a second prompted instance playing "victim," loop the conversation, save the transcript

**Tunable knob — temperature**: controls how random vs. deterministic word choice is. Higher = more varied, less repetitive scam transcripts.

**No training required** — pure API usage, doable regardless of ML background. Have the conversation end in a fake transaction, and feed that transaction into your Tier 1 item 3 pipeline — this links conversation and transaction data, which most teams won't bother doing.

---

## TIER 2 — Strengthen your entry (once Tier 1 works end-to-end)

### 5. Isolation Forest — unsupervised anomaly detection
**What it is**: builds many random trees, each splitting data on random features at random thresholds. Anomalous points get **isolated in fewer splits** than normal points, because they don't need many cuts to separate from the crowd — average path length to isolate a point becomes its anomaly score.

**Why add it**: needs **no fraud labels at all** — it learns what "normal" looks like and flags deviation, so it can catch attack types your generator never simulated. Directly in `scikit-learn`.

### 6. SHAP — explainability
**What it is**: **SHAP (SHapley Additive exPlanations)**, based on **Shapley values** from cooperative game theory — a way of fairly distributing "credit" among players (here, features) for a shared outcome (here, the prediction). In practice: SHAP tells you exactly how much each feature (amount, time-since-last-transaction, etc.) pushed one specific prediction toward "fraud."

**Why it matters for judging**: "real-world feasibility" is an explicit scoring criterion, and an unexplainable fraud model is not deployable in a regulated financial environment — compliance teams require this. Library: `shap`, works directly with XGBoost.

### 7. CTGAN — higher-fidelity synthetic tabular data (library call, not from-scratch)
**What it is**: **CTGAN (Conditional Tabular GAN)** is a **GAN (Generative Adversarial Network)** — two neural networks trained against each other: a **generator** creating fake rows, a **discriminator** trying to tell fake from real. They train in a loop where the generator gets better at fooling the discriminator and vice versa, until generated rows are hard to distinguish from real ones. CTGAN adapts this specifically for tabular data with mixed categorical/continuous columns.

**Practical note**: you don't implement the GAN training loop yourself. `pip install ctgan`, then `.fit(your_dataframe)` / `.sample(n)`. Treat as an upgrade to Tier 1's rule-based generator once that's already working — not a starting point.

### 8. Basic feedback loop
Take the fraud cases your Tier 1 detector *misses*, use them to inform your generator (hand-tune the rule-based simulator's parameters, or condition your LLM prompts on the missed pattern), generate more like them, retrain, and show recall improve across the cycle. This single before/after comparison is your strongest closed-loop evidence — no exotic technique required.

---

## TIER 3 — Stretch / novelty (only if ahead of schedule)

### 9. Autoencoders for anomaly detection
**What it is**: a neural network trained to compress its input into a small internal representation (the **latent space**) and reconstruct the original from it. Train only on legitimate transactions — it learns to reconstruct normal patterns well and does a poor job on fraud (which doesn't match what it learned to compress). The **reconstruction error** becomes your anomaly score.

**Connection to what you're learning**: a genuine from-scratch neural net, but a simple feedforward one — a natural next step after Karpathy's material.

### 10. Graph Neural Networks (GNNs) — GraphSAGE or GAT
**What it is**: standard ML treats each transaction as an independent row, but real fraud often involves **rings** — accounts sharing a device, IP, or beneficiary. A GNN represents data as a **graph** (nodes = accounts/cards/devices, edges = shared attributes) and learns via **message passing**: each node repeatedly aggregates information from its neighbors, so after a few rounds a node's learned representation (**embedding**) reflects its whole neighborhood's pattern, not just its own features. **GAT (Graph Attention Network)** additionally learns to weigh some neighbors more than others (an **attention mechanism** — same underlying idea as in transformers).

**Why Tier 3**: genuinely more complex to implement and explain in a demo, needs a library like PyTorch Geometric, and needs graph-structured data (shared device/IP fields) your baseline datasets may not have — you'd need to synthesize the "sharing" relationships yourself first. Sequencing tip either way: get Isolation Forest working solidly before attempting this — don't jump straight to graph modeling.

### 11. Sequence models — LSTM and Transformer/attention
**What it is**: models processing transactions **in order** to catch behavioral drift over a session or weeks.
- **LSTM (Long Short-Term Memory)**: a recurrent neural network with internal gates (input/output/forget) that decide what information to keep or discard while processing a sequence, retaining relevant signal from far earlier.
- **Transformer / attention mechanism**: instead of one step at a time like an LSTM, attention lets the model directly weigh how relevant every other position in a sequence is to the one it's currently encoding, processed in parallel. This is the exact architecture underlying every modern LLM — **directly what Karpathy's series builds toward**, so if your team finishes that material, you already have the conceptual and code foundation for this piece.

### 12. Reinforcement-learning framing for the "adaptive attacker" concept
If you want your generator to genuinely *adapt* its strategy based on what the detector catches (rather than a human manually tuning parameters, per Tier 2 item 8), the formal name for this is **reinforcement learning**: the generator is a **policy** that takes actions (attack parameter choices), receives a **reward** signal (did it evade the detector), and adjusts to maximize that reward over time. You don't need to implement full RL machinery — describing your Tier 2 feedback loop in this language for your pitch already captures the core idea, and it's the correct term if judges ask how your "adaptive attacker" actually adapts.

### 13. NLP classifiers for scam-transcript detection
Three difficulty levels, pick based on remaining time:
- **Simplest**: TF-IDF (a way of scoring how distinctive a word is to one document relative to a whole collection) + logistic regression — a few lines, no neural net
- **Middle**: fine-tune a small pretrained transformer like DistilBERT on labeled scam vs. non-scam transcripts
- **Fastest, no training**: prompt an LLM as a zero-shot judge, scoring a transcript's fraud-likelihood directly — reuses your existing API access from Tier 1 item 4

### 14. Concepts worth naming in your pitch even if not fully implemented
- **Diffusion models**: the generative technique behind most modern image generators — relevant if your Identify pillar discusses forged ID documents or deepfakes (a model trained to reverse a gradual noising process, turning random noise into a coherent image step by step). Naming this shows depth even without running one.
- **Federated learning**: multiple banks training a shared fraud model collaboratively without sending each other raw transaction data — only sharing model updates. Strong point for "real-world feasibility" specifically, since banks legally cannot pool customer data, and this is how the industry actually approaches that problem.
- **Differential privacy**: often paired with federated learning — a mathematical guarantee bounding how much any single individual's data can influence a shared model's output. One sentence naming this alongside federated learning signals real depth.

---

## A scope caution, if you're working from a plan with a full platform build

If your plan includes a dedicated backend service (e.g., FastAPI), a separate frontend (e.g., React), and a graph database (e.g., Neo4j) as distinct pieces of infrastructure: that's a legitimate production architecture, but it's a large amount of software engineering layered on top of the ML work, for a beginner-ML team with 10 days. None of the five judging criteria — diversity, fidelity, detection efficacy, novelty, feasibility — require a polished multi-service platform; they require good models and a clear demo. A single Streamlit app or well-organized notebook, reading from a local file or SQLite, tells the same attack → detection → explanation story. Spend the time you'd save on the models instead, and only build real platform infrastructure if Tier 1 and Tier 2 finish early.

---

## What NOT to attempt given 10 days
- Training an LLM or any transformer from scratch — use API access or small pretrained/fine-tunable models
- Implementing a GAN's training loop manually — use the `ctgan` library
- Full federated learning infrastructure — mention it as a design consideration, don't build it
- A full reinforcement-learning pipeline — the simplified retrain-loop (Tier 2, item 8) gets you the same narrative
- A separate backend + frontend + graph database as three distinct services — see scope caution above

---

## Quick reference

| # | Model/Technique | Pillar | Library | Needs training? |
|---|---|---|---|---|
| 1 | XGBoost / LightGBM | Defend | xgboost / lightgbm | Yes — fast, CPU, minutes |
| 2 | SMOTE | Defend (support) | imbalanced-learn | No — resampling step |
| 3 | Rule-based generator | Generate | plain Python | No |
| 4 | LLM role-play prompting | Generate | any LLM API | No |
| 5 | Isolation Forest | Defend | scikit-learn | Yes — fast, unlabeled |
| 6 | SHAP | Defend (explainability) | shap | No — explains an existing model |
| 7 | CTGAN | Generate | ctgan | Yes — moderate time |
| 9 | Autoencoder | Defend (stretch) | PyTorch/TensorFlow | Yes — GPU helps |
| 10 | GNN (GraphSAGE/GAT) | Defend (stretch) | PyTorch Geometric | Yes — GPU helps |
| 11 | LSTM/Transformer | Defend (stretch) | PyTorch | Yes — GPU helps |
| 13 | NLP classifier | Defend (scam text) | scikit-learn or transformers | Depends on approach |

---

## Where this sits versus the uploaded ChatGPT document

Worth being fair to it: it's a genuinely thorough plan, and a few things in it are worth keeping — the "generate behavioral sequences, not `fraud=true` rows" framing (folded into Section 0 above), the explicit sequencing advice ("Isolation Forest before GNN," "don't jump to Neo4j"), and the schema-first / lock-features-before-coding advice.

Confirmed genuinely absent from it (checked the full document, not just skimmed):
- **No Mastercard- or card-network-specific vocabulary** — no tokenization/MDES, 3-D Secure, EMV, or Decision Intelligence anywhere, despite this being a Mastercard-branded challenge. Naming these in your pitch signals real-world grounding specifically to these judges.
- **No deepfakes or voice cloning named anywhere**, despite being one of the most-reported GenAI-specific fraud vectors (cloned-voice CEO fraud, deepfake KYC bypass). Its "AI-Assisted Impersonation" scenario is conceptually similar to what the industry specifically calls **Authorized Push Payment (APP) fraud** — using that exact regulatory term in your pitch reads as more grounded than "impersonation."
- **No named generation techniques** — it says "generate synthetic data" throughout but never names SMOTE, CTGAN, GANs, or diffusion models specifically (all added above).
- **No SHAP by name**, despite emphasizing explainability heavily.
- **No temporal train/test split caution, no `scale_pos_weight`** — both added under Foundations above; skipping either is an easy way to end up with misleading results.
- **No federated learning or differential privacy** — both added as feasibility-narrative points.

