---
version: 1.0.0
last_updated: 2026-09-14
---

# Project Glossary

## Task
A unit of work that can be claimed by an AI agent. Contains:
- id (UUID)
- title (string)
- description (string)
- status (enum: backlog, claimed, in_progress, review, done)
- owner (agent ID or null)

## Agent
An AI worker that can claim and complete tasks.

## Claim
The act of an agent taking ownership of a task. Only one agent can claim a task at a time.

## Review
A quality check performed by a reviewer agent before a task moves to "done".