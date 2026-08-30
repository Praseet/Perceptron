# H.63 Source-to-decision map for future agents

| Question | First source to inspect | Secondary |
|---|---|---|
| Which page owns this? | Phase 0.2 + page phase | `docs/FRONTEND_VISION.md` |
| What visual token? | Appendix D | This Appendix H.2 |
| What API shape? | Appendix C/E | This Appendix H.2/H.29 |
| What model field? | Appendix B | `src/config.py` |
| How is prediction actually implemented? | `src/fraud_model/inference.py` | API adapter |
| How is generation actually implemented? | `src/generator/llm_generator.py` / `rule_generator.py` | Phase 7 |
| How does the loop actually work? | `src/models/feedback_loop.py` | Phase 9 |
| Which numbers are trusted? | Appendix F / `CHANGELOG.md` | current API response |
| Which old UI can be copied? | **None** | legacy frontend is historical only |
| How do I verify? | phase acceptance criteria | Phase 10 |
| What if two docs disagree? | authority order in H.1 | `PROGRESS.md` |

---

