# Changelog

## Gate 14.6 - Vietnamese documentation and docs audit

- Added Vietnamese documentation pages for README, quickstart, security/privacy, roadmap, and operation rules.
- Added documentation quality audit to guard against mojibake, placeholders, raw key examples, and missing Vietnamese docs links.

## Gate 14.5 - Mojibake cleanup

- Rewrote public documentation in clean UTF-8.
- Added repository text encoding audit script.
- Cleaned provider registry notes that contained broken characters.

## Gate 14 - Health scoreboard, aliases, and privacy design

- Added safe health scoreboard and JSON cache support for live smoke.
- Added last-known-good model lookup and model ranking from health metadata.
- Added provider/model alias parser for `provider:model` references.
- Added AIOS privacy policy adapter design without AIOS_habbit integration.

## Gate 13 - AI gateway research

- Compared LiteLLM, Portkey Gateway, OpenRouter, Vercel AI SDK/Gateway, and health-routing patterns.
- Selected small features worth copying conceptually without large dependencies.

## Gate 12 - Additional Gemini models

- Enabled `gemini-flash-lite-latest`, `gemini-3.1-flash-lite-preview`, and `gemma-4-31b-it` after live PASS.

## Gate 11 - Gemini discovery

- Added opt-in Gemini model discovery.
- Kept discovered models separate from enabled runtime models.

## Gate 10 - Additional Gemini candidates

- Tested extra Gemini candidates.
- Added only candidates that live PASS.

## Gate 9 - Gemini model catalog

- Added and verified a broader Gemini model catalog.
- Kept unit tests network-free.

## Gate 8 - Gemini support

- Added Gemini through the OpenAI-compatible endpoint.
- Added safe live smoke support for Gemini.

## Gate 7 - Live strategy and Groq debugging

- Improved live provider order and `live_free_first` behavior.
- Investigated Groq failures safely without leaking keys.

## Gate 6 - v0.1.0 internal release

- Verified live provider calls with real keys outside the repository.
- Prepared internal release state and tag.

## Gate 5 - Optional network transport

- Added optional real HTTP transport and live smoke script.
- Kept default tests offline.

## Gate 4 - Registry and environment config

- Added provider registry and environment-based router creation.

## Gate 3 - OpenAI-compatible provider

- Added mock-first OpenAI-compatible adapter.

## Gate 2 - Core router intelligence

- Added router policy, provider health, and fallback behavior.

## Gate 0 - Foundation

- Created project foundation, packaging metadata, tests, and initial documentation.
