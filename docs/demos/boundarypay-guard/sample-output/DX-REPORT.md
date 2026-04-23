# BoundaryPay Guard DX Report

## Current Run

This generated report was created in `fixture` mode. In fixture mode, the demo uses a
deterministic Jupiter price snapshot so reviewers can run it without an API key or
wallet. Before final Superteam/Jupiter submission, rerun with `--mode live` after the
Jupiter Developer Platform account and API key are ready.

## Jupiter Developer Platform Notes

- The Jupiter Developer Platform is a strong fit for agents because the docs present
  REST APIs, clean JSON responses, and AI-specific surfaces such as llms.txt, skills,
  MCP, and CLI tooling.
- For an agentic payment safety demo, the most useful review surfaces are the Price,
  Tokens, and Swap API families plus the AI tooling docs.
- The most important DX artifact for this submission is a reproducible trace showing
  what the agent proposed and why the guard allowed or blocked it.

## What Needs Live Follow-Up

- Time from API-key creation to first successful request.
- Whether the Price/Swap docs make route and amount binding easy to preserve.
- Whether error responses are structured enough for an agent to recover safely.
- Whether API logs expose enough metadata to audit agent-triggered requests.
