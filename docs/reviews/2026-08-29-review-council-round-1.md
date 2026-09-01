# Independent review council — round 1

Branch reviewed: `feat/wordassistant-v2-universal-core`  
Decision: **CHANGES REQUIRED / NO-GO**

Four read-only reviewers independently inspected the stable 192-test diff.
CRG was unavailable, so they used full workspace inventory, `git diff`, `rg`,
direct source inspection, focused tests, and (for one reviewer) OCR Delegation.
No reviewer edited, committed, pushed, or ran Antigravity.

Review roles:

- Wegener — architecture, control-plane, selectors, capability and blast radius.
- Hilbert — Word/OOXML fidelity, fields, numbering, tables, notes, pagination.
- Locke — test, security, packaging, release and CI adversarial review.
- Planck — adversarial integrator; challenged, deduplicated and classified all findings.

Consensus release blockers:

1. Native dry-run/output handling could mutate the input.
2. CLI/facade bypassed the advertised router and transaction coordinator.
3. Capability evidence was inferred from backend names; fidelity was not enforced.
4. Verification could report PASS with stale fields or unreviewed requested render.
5. Agent workflows were syntactically valid but not executable end to end.
6. Table autofit, field removal, bookmark references, render inventory, timeout
   cleanup, structured errors, package discovery, and release checks had concrete defects.
7. Several advanced features were tags or dormant code rather than proven Word
   semantics and needed explicit `UNSUPPORTED` gating.

The accepted remediation contract is intentionally narrow: connect one safe
execution service, prove operations with explicit test sources, repair the
reproducible fidelity defects, and hide unsupported variants instead of
claiming near-complete Word fidelity.

Round 2 is permitted only after focused RED/GREEN evidence is stable.
