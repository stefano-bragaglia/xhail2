# Changelog

## [1.0.0] — 2026-06-22

Initial release: faithful Python port of the original Java XHAIL implementation.

### Added

- Full Python port of the XHAIL abduction/induction/deduction pipeline
- `Problem`, `Grounding`, `Hypothesis`, `Answer`, `Answers` entities
- ASP-based solver integration via external Gringo/Clasp v3 binaries
- `#display`, `#example`, `#modeh`, `#modeb` directive parser
- Command-line interface (`xhail` entry point) with all original flags
- 1009-test suite at 93 % coverage
- Example problems in `examples/toys/`
