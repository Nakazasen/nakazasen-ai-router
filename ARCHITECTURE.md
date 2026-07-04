# Architecture

Nakazasen AI Router is a library-first Python router for selecting AI providers and models safely.

## Core

The core package exposes request/result types and a router that tries provider candidates in policy order.
The router is designed to be mock-first: unit tests do not call the internet.

## Provider registry

`registry.py` defines provider profiles such as Gemini, OpenRouter, Groq, DeepSeek, NVIDIA NIM, ChatAnyWhere, Mistral, and local OpenAI-compatible servers.
Each profile stores safe metadata: provider id, base URL, API key environment variable, default models, and notes.

## OpenAI-compatible adapter

`providers/openai_compatible.py` adapts OpenAI-style chat completions endpoints.
Network access is dependency-injected through an HTTP client so tests can use mocks.

## Optional transport

Real HTTP transport is optional and only used when callers enable network access.
The default test path does not require provider keys.

## Discovery

`discovery.py` supports opt-in provider model discovery, currently focused on Gemini.
Discovery lists provider models but does not automatically enable them in the runtime catalog.

## Health scoreboard

`scoreboard.py` stores safe provider/model health metadata:

- success count
- failure count
- failure streak
- last status
- last error type
- latency
- timestamps
- cooldown time

It must not store prompts, API keys, Authorization headers, raw responses, or evidence.

## Alias registry

`aliases.py` parses `provider:model` references and resolves friendly aliases such as `gemini:fast`, `gemini:lite`, and `gemini:gemma`.

## Privacy boundary

AIOS_habbit integration is not implemented yet.
The design is that AIOS assigns privacy labels and sanitizes prompts before calling the router.
The router will enforce metadata-based policy and must fail closed for unknown or confidential content.

## No network by default

Network calls require explicit opt-in through live scripts or router creation options.
Unit tests stay offline.
