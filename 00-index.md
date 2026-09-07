# agentskills.io Documentation Bundle — Index

Complete verbatim extraction of the agentskills.io documentation domain.
Source of scope: https://agentskills.io/llms.txt (cross-checked against /sitemap.xml and a full internal-link crawl; all three agree on the same 9 pages).

| # | Page title | Source URL | Local file |
| --- | --- | --- | --- |
| 1 | Agent Skills Overview | https://agentskills.io/home | `home.md` |
| 2 | Specification | https://agentskills.io/specification | `specification.md` |
| 3 | Client Showcase | https://agentskills.io/clients | `clients.md` |
| 4 | Quickstart | https://agentskills.io/skill-creation/quickstart | `skill-creation-quickstart.md` |
| 5 | Best practices for skill creators | https://agentskills.io/skill-creation/best-practices | `skill-creation-best-practices.md` |
| 6 | Optimizing skill descriptions | https://agentskills.io/skill-creation/optimizing-descriptions | `skill-creation-optimizing-descriptions.md` |
| 7 | Evaluating skill output quality | https://agentskills.io/skill-creation/evaluating-skills | `skill-creation-evaluating-skills.md` |
| 8 | Using scripts in skills | https://agentskills.io/skill-creation/using-scripts | `skill-creation-using-scripts.md` |
| 9 | How to add skills support to your agent | https://agentskills.io/client-implementation/adding-skills-support | `client-implementation-adding-skills-support.md` |

Total: 9 documentation pages + this index.

## Notes

- Each file begins with `# Source: <original URL>`, followed by the page's verbatim content exactly as served by the site's canonical markdown endpoint (the `.md` URL listed in the site's own llms.txt).
- Only one piece of non-content boilerplate was removed: the site-wide 3-line 'Documentation Index → llms.txt' callout that the server prepends to every page. No substantive content was altered.
- The `home` and `clients` pages render their client-logo grids in randomized order on every HTML page load (the site's own `LogoCarousel`/`ClientShowcase` components shuffle entries client-side). The canonical markdown endpoints are deterministic and were used as the authoritative source; both pages list the same 46 client integrations.

## Appendix: llms.txt (as served at https://agentskills.io/llms.txt)

```
# Agent Skills

## Docs

- [Agent Skills Overview](https://agentskills.io/home.md): A standardized way to give AI agents new capabilities and expertise.
- [Specification](https://agentskills.io/specification.md): The complete format specification for Agent Skills.
- [Client Showcase](https://agentskills.io/clients.md): Agent products that support the Agent Skills format.
- [Quickstart](https://agentskills.io/skill-creation/quickstart.md): Create your first Agent Skill and see it work in VS Code.
- [Best practices for skill creators](https://agentskills.io/skill-creation/best-practices.md): How to write skills that are well-scoped and calibrated to the task.
- [Optimizing skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions.md): How to improve your skill's description so it triggers reliably on relevant prompts.
- [Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills.md): How to test whether your skill produces good outputs using eval-driven iteration.
- [Using scripts in skills](https://agentskills.io/skill-creation/using-scripts.md): How to run commands and bundle executable scripts in your skills.
- [How to add skills support to your agent](https://agentskills.io/client-implementation/adding-skills-support.md): A guide for adding Agent Skills support to an AI agent or development tool.
```
