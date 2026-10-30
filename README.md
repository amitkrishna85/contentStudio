# CreatorOS

CreatorOS is a compact content studio that turns a brief into an opinionated content plan, draft, visual, schedule, and learning loop.

## Overview

A user supplies a brief such as "a LinkedIn post about AI safety". The system uses a small set of specialized agents to:

- infer the brand voice from sample posts,
- propose angles and platform-aware copy,
- critique and revise the draft,
- generate a matching image,
- schedule the final output,
- learn from post-performance and adapt future suggestions.

## Agent flow

Strategist -> Writer -> Editor -> Visual -> Schedule -> Learn

## Setup

1. Create a Python 3.11+ virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add a valid `GEMINI_API_KEY` from Google AI Studio. The key is required for content generation; without it, the brief form explains the missing setup and does not save a fake draft. Restart the server after changing `.env`.
4. Run the app with `uvicorn creatoros.app.main:app --reload`.

## Design decisions

- All text, structured-output, and image-generation calls go through the Google Gen AI SDK and Gemini Interactions API in `creatoros/app/llm.py`.
- A successful generation produces platform-ready copy and a visual; the content review page includes a copy-to-clipboard action. Gemini API failures are shown to the user rather than disguised as successful generic drafts.
- Brand voice describes the style inferred from a brand's sample posts (tone, sentence length, vocabulary, emoji and hashtag habits, formatting quirks, phrases to avoid, and example copy). The two demo profiles are seeded from their included sample sets.
- SQLite is used for durable records and the learning loop.
- Agent decisions are kept in the database as structured events for auditing.
- A simple learning playbook is injected into new generations when enough evidence exists.

## Evaluation

The evaluation suite in `creatoros/eval` compares first-draft vs final-draft quality, validates the learning impact, and checks brand-voice separation.

## Limitations

This repo is intentionally compact and is designed as a working starter implementation. Real deployment would add stronger auth, queueing, metrics collection, and richer brand analysis.
