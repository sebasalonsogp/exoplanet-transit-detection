# Exoplanet Transit Lab task list

This checklist mirrors the approved implementation order in `tasks/plan.md`. A task is complete
only when its acceptance criteria and verification steps in the plan have passed.

## Phase 0: Source hygiene and evidence

- [x] Task 1: Sanitize the archived notebook.
- [x] Task 2: Establish the verified demo data package.

### Checkpoint A: Clean and trustworthy source

- [x] Notebook hygiene test passes.
- [x] Data provenance and reference values have been reviewed.
- [x] No runtime network request or local machine path is required.
- [x] Human review before Phase 1.

## Phase 1: First end-to-end analytical slice

- [ ] Task 3: Implement the data contract and loader.
- [ ] Task 4: Reproduce the BLS result.
- [ ] Task 5: Render the core recruiter-facing story.

### Checkpoint B: Analytical proof

- [ ] Full test, lint, and type-check suite passes.
- [ ] A fresh clone can reproduce the BLS result from bundled data.
- [ ] A visitor can understand the target, candidate period, and folded transit in two minutes.
- [ ] Human review before method comparisons.

## Phase 2: Preparation and method-comparison story

- [ ] Task 6: Add signal-preparation views.
- [ ] Task 7: Package the notebook's Fourier and SVD results.
- [ ] Task 8: Build the method comparison view.

### Checkpoint C: Notebook analysis successfully repackaged

- [ ] Prepare and Compare use the same versioned dataset.
- [ ] Fourier/SVD additions reuse prior work and introduce no unsupported claims.
- [ ] Full quality suite passes and interaction remains responsive.
- [ ] Human review before final interaction and interpretation work.

## Phase 3: Interaction and interpretation

- [ ] Task 9: Add bounded candidate exploration and caching.
- [ ] Task 10: Add the evidence and limitations panel.

### Checkpoint D: Portfolio MVP

- [ ] Observe → Prepare → Compare → Search → Fold → Interpret works end to end.
- [ ] Default state is complete and interaction deepens the story.
- [ ] No external service, upload, database, or authentication is required.
- [ ] Human approval that the MVP content and behavior are complete.

## Phase 4: Portfolio polish and launch readiness

- [ ] Task 11: Apply responsive visual and accessibility polish.
- [ ] Task 12: Write the portfolio documentation.
- [ ] Task 13: Add a minimal continuous-integration gate.
- [ ] Task 14: Deploy and perform the public-readiness audit.

### Checkpoint E: Ready to share

- [ ] Hosted app and repository tell the same concise project story.
- [ ] CI is green and the release audit has no unresolved findings.
- [ ] User explicitly approves any repository visibility change.
- [ ] Project is ready to link from GitHub, a résumé, and applications.

## Deferred unless the plan changes

- [ ] Multi-target browsing or live catalog search.
- [ ] User-uploaded light curves.
- [ ] Machine-learning classification or new research.
- [ ] Authentication, persistence, or a standalone API.
- [ ] 3D scenes or custom decorative components.
