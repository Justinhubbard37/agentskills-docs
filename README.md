# Agent Skills Documentation Mirror (`agentskills-docs`)

An offline-ready, deterministic, and verbatim knowledge base mirror of the official [Agent Skills](https://agentskills.io) documentation suite.

Designed for dual-audience utility:
1. **AI Agent Ingestion & RAG:** High-integrity, deterministic markdown with zero paraphrasing, clear document boundaries, and structured metadata for agent connectivity and retrieval pipelines.
2. **Human Director Orchestration:** Clean, scanable architecture enabling technical directors to navigate, review, and orchestrate agent capabilities without code-reading friction.

This is a **read-only AgentSkills.io documentation mirror for human-AI collaboration**. Mirrored source documents remain unchanged unless the official published AgentSkills.io documentation changes. AI collaborators should read [`AGENTS.md`](./AGENTS.md) for navigation, authority, progressive-disclosure, and usage rules.

---

## Provenance & Verification

| Parameter | Value |
| :--- | :--- |
| **Source Domain** | [agentskills.io](https://agentskills.io) |
| **Upstream Repository** | [agentskills/agentskills](https://github.com/agentskills/agentskills) |
| **Upstream License** | Apache License 2.0 |
| **Retrieval Date** | September 6, 2026 |
| **Scope Audit** | 9 canonical documentation pages (100% concordance across `llms.txt`, `/sitemap.xml`, and internal crawler) |
| **Extraction Integrity** | Verbatim extraction from canonical `.md` endpoints. Zero summarization or synthetic rewrites. |

---

## Documentation Catalog

| Document | Title | Scope & Description | Source URL |
| :--- | :--- | :--- | :--- |
| [`00-index.md`](./00-index.md) | **Documentation Index** | Master index table, extraction methodology notes, and raw upstream `llms.txt`. | [llms.txt](https://agentskills.io/llms.txt) |
| [`home.md`](./home.md) | **Agent Skills Overview** | Overview of Agent Skills framework, architecture, ecosystem, and integration principles. | [/home](https://agentskills.io/home) |
| [`specification.md`](./specification.md) | **Specification** | Complete formal specification: directory structure, `SKILL.md` frontmatter, schema validation, and naming constraints. | [/specification](https://agentskills.io/specification) |
| [`clients.md`](./clients.md) | **Client Showcase** | Comprehensive registry of all 46 tools, IDEs, and agent frameworks supporting Agent Skills. | [/clients](https://agentskills.io/clients) |
| [`skill-creation-quickstart.md`](./skill-creation-quickstart.md) | **Quickstart** | Hands-on guide to creating a first skill, configuring directories, and executing within VS Code. | [/skill-creation/quickstart](https://agentskills.io/skill-creation/quickstart) |
| [`skill-creation-best-practices.md`](./skill-creation-best-practices.md) | **Best Practices** | Guidelines for scope calibration, progressive disclosure, context budgeting, and tool orchestration. | [/skill-creation/best-practices](https://agentskills.io/skill-creation/best-practices) |
| [`skill-creation-optimizing-descriptions.md`](./skill-creation-optimizing-descriptions.md) | **Optimizing Descriptions** | Trigger tuning, negative constraints, synthetic evaluation queries, and prompt calibration. | [/skill-creation/optimizing-descriptions](https://agentskills.io/skill-creation/optimizing-descriptions) |
| [`skill-creation-evaluating-skills.md`](./skill-creation-evaluating-skills.md) | **Evaluating Skills** | Eval-driven development lifecycle, test case generation, execution scoring, and quality gates. | [/skill-creation/evaluating-skills](https://agentskills.io/skill-creation/evaluating-skills) |
| [`skill-creation-using-scripts.md`](./skill-creation-using-scripts.md) | **Using Scripts in Skills** | Bundling executable scripts, subprocess isolation, runtime environments, and deterministic outputs. | [/skill-creation/using-scripts](https://agentskills.io/skill-creation/using-scripts) |
| [`client-implementation-adding-skills-support.md`](./client-implementation-adding-skills-support.md) | **Adding Skills Support** | Architecture guide for agent developers implementing skill discovery, parsing, and execution runtimes. | [/client-implementation/adding-skills-support](https://agentskills.io/client-implementation/adding-skills-support) |

---

## Agent & RAG Ingestion Guide

### Document Structure Conventions
* **Source Provenance Header:** Every document begins with `# Source: <canonical-url>` on line 1, followed immediately by the verbatim `# <Page Title>` on line 3.
* **Deterministic Content:** All tables, code fences, shell scripts, and parameter lists are preserved in exact upstream form.
* **Non-Content Removal Disclosure:** The only text omitted from source files is the transient 3-line Mintlify index banner (`> ## Documentation Index...`). No substantive text, parameter definitions, or code examples were modified.
* **Client Ordering:** Canonical `.md` endpoints were utilized to eliminate non-deterministic client-side JavaScript shuffling present on browser rendering of the `home` and `clients` pages.

### Programmatic Manifest (`sources.json`)
For automated RAG pipelines, pipeline indexing, and cache invalidation, refer to [`sources.json`](./sources.json), which provides:
* Document titles and canonical source URLs
* Character counts, byte sizes, and line counts
* Local SHA-256 checksums for each normalized mirror file

---

## License & Attribution

This documentation mirror is derived from the official [Agent Skills](https://agentskills.io) specification provided by the Agent Skills community.
The source materials are licensed under the **Apache License 2.0**. See the [`LICENSE`](./LICENSE) file for complete license terms.
