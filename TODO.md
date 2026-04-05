# Improvement Roadmap

Items to address after MVP ships. Not blockers — quality and polish work.

## Accessibility / ARIA

- [ ] Audit FileDropZone for screen reader support (drag-and-drop alternatives, file state announcements)
- [ ] Add `aria-label` to textarea (currently relies on placeholder only)
- [ ] Add error announcement via `aria-live` for inline error display (error-display step)
- [ ] Audit results page (`/contract/[uuid]`) for heading hierarchy and landmark regions
- [ ] Test full flow with VoiceOver / screen reader

## Eval Pipeline

- [ ] Re-run full contract suite on Haiku 4.5 with `max_tokens: 8192` after fence stripping
- [ ] Investigate contract_3_nonstandard and contract_4_minor_issues scoring accuracy
- [ ] Add TTFT measurement to verification script
- [ ] Build automated eval runner (run all contracts, compare against benchmarks, report diffs)

## API Hardening

- [ ] Wire `instructions` through api-route to the prompt (currently sent but ignored server-side)
- [ ] Add request size limit on `/api/evaluate`
- [ ] Add structured logging to api-route catch block
- [ ] Add health-check endpoint that validates `ANTHROPIC_API_KEY` at startup

## Frontend Polish

- [ ] Loading shimmer stagger animation (CSS animation-delay on clause cards)
- [ ] Transition between form and shimmer states (fade/slide)
- [ ] Better error UX than just resetting the form silently on failure
