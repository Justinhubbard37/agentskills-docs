# Agent Instructions

## Purpose

This repository is a read-only, repository-shaped mirror of the official [AgentSkills.io](https://agentskills.io) documentation. It exists so AI collaborators can directly apply the same Agent Skills standards and guidance published for human developers when helping the Director create, evaluate, optimize, or integrate Agent Skills.

The mirrored documentation is reference material, not a development surface for the Agent Skills standard.

## Read-only boundary

Files listed as documentation entries in `sources.json` are preserved source material. Do not rewrite, reorganize, summarize in place, "improve," or otherwise modify them during normal collaboration.

A mirrored documentation file may change only when a difference is verified against the official published AgentSkills.io documentation. Upstream changes are handled through the review-gated synchronization workflow; do not manually patch the mirror as a substitute for that process.

## Authority

For Agent Skills format requirements, `specification.md` is the normative local authority. If another mirrored document conflicts with it on a format requirement, follow `specification.md` and surface the discrepancy.

Other mirrored documents provide explanatory guidance, examples, implementation guidance, evaluation guidance, or ecosystem information. They do not create additional format requirements.

`README.md`, `00-index.md`, `sources.json`, this file, and repository automation are navigation, provenance, and maintenance surfaces; they are not part of the Agent Skills specification.

If a verified current official AgentSkills.io publication differs from this snapshot, the official published documentation controls current standards. Report the difference and use the review-gated synchronization path rather than editing the mirror casually.

## Task routing

Use progressive disclosure. Start with the minimum documents needed for the task.

- **Understand Agent Skills:** `home.md`; add `specification.md` when requirements matter.
- **Create a skill:** `specification.md` + `skill-creation-quickstart.md`; add best practices as needed.
- **Apply skill-creation best practices:** `skill-creation-best-practices.md` + relevant requirements from `specification.md`.
- **Optimize a skill description:** `skill-creation-optimizing-descriptions.md` + `specification.md`.
- **Evaluate a skill:** `skill-creation-evaluating-skills.md` + `specification.md`; add best practices when useful.
- **Use scripts in a skill:** `skill-creation-using-scripts.md` + `specification.md`.
- **Implement Agent Skills support in a client:** `client-implementation-adding-skills-support.md` + `specification.md`.
- **Check supported clients:** `clients.md`. If current support status matters and network access is available, verify against the current official publication because ecosystem listings can change.

Do not load the entire corpus by default. `00-index.md` is the human-readable document map; `sources.json` is the machine-readable source/provenance manifest.

## Snapshot and provenance

`sources.json` records the snapshot source, capture date, canonical published URLs, normalization rules, and hashes of the local normalized files. Each mirrored document also begins with a local `# Source:` header identifying its published page.

The local mirror intentionally removes the non-substantive Mintlify AI-navigation banner that points to `llms.txt`; repository navigation is provided by `AGENTS.md`, `00-index.md`, and `sources.json` instead.

## Preserved presentation material

Canonical Markdown may contain Mintlify, React, JSX, or other presentation-oriented source material. Preserve it as part of the published source capture, but do not treat presentation machinery as defining Agent Skills requirements unless `specification.md` independently establishes the requirement.
