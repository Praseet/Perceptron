# Graph Report - fraud_model  (2026-08-24)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 44 nodes · 73 edges · 10 communities (8 shown, 2 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `37fc8072`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7

## God Nodes (most connected - your core abstractions)
1. `call_structured()` - 8 edges
2. `new_tx_id()` - 7 edges
3. `new_case_id()` - 6 edges
4. `generate_benign_case_batch()` - 6 edges
5. `generate_llm_case_batch()` - 6 edges
6. `_sleep_for_retry()` - 5 edges
7. `inject_bustout()` - 5 edges
8. `materialize_llm_transaction()` - 4 edges
9. `_structured_anthropic()` - 3 edges
10. `_structured_gemini()` - 3 edges

## Surprising Connections (you probably didn't know these)
- `materialize_llm_transaction()` --calls--> `new_tx_id()`  [INFERRED]
  src/generator/llm_generator.py → src/generator/rule_generator.py

## Import Cycles
- None detected.

## Communities (10 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.54
Nodes (7): call_structured(), Returns a parsed dict, or None if every attempt failed (caller supplies the…, _sleep_for_retry(), _structured_anthropic(), _structured_gemini(), _structured_local(), _structured_openai()

### Community 1 - "Community 1"
Cohesion: 0.36
Nodes (8): materialize_llm_transaction(), Turns extracted conversation parameters into an actual transaction row -- same…, inject_account_takeover(), inject_auth_bypass(), inject_card_testing(), inject_impersonation_case(), new_case_id(), new_tx_id()

### Community 2 - "Community 2"
Cohesion: 0.43
Nodes (4): datetime, get_bustout_device(), inject_bustout(), sample_event_timestamp()

### Community 3 - "Community 3"
Cohesion: 0.40
Nodes (5): _fallback_benign_case(), generate_benign_case(), generate_benign_case_batch(), Batched version of generate_benign_case: one call for the whole batch. Writes…, Unchanged single-case entry point, kept for compatibility.

### Community 4 - "Community 4"
Cohesion: 0.40
Nodes (5): _fallback_case(), generate_llm_case(), generate_llm_case_batch(), Generates len(pretext_case_pairs) cases in a single API call instead of one…, Unchanged single-case entry point, kept for compatibility. Prefer…

### Community 5 - "Community 5"
Cohesion: 0.83
Nodes (3): add_features(), haversine_km(), rolling_sum_trailing()

## Knowledge Gaps
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `generate_benign_case_batch()` connect `Community 3` to `Community 0`, `Community 2`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `generate_llm_case_batch()` connect `Community 4` to `Community 0`, `Community 2`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `call_structured()` connect `Community 0` to `Community 3`, `Community 4`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._