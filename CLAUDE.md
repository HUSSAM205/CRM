# GradTrack CRM — Agent Skills

This project has [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) installed
under `.claude/skills/` via the [`skills` CLI](https://github.com/vercel-labs/skills). Update them with:

```bash
npx skills update -y
```

## Core principle: auto-invoke skills

When a task matches an installed skill's description, use that skill proactively — don't wait to be
asked by name. Prefer the installed skill over ad-hoc equivalent work. Currently installed:

| Skill | Use when |
| --- | --- |
| `web-design-guidelines` | Reviewing UI code, accessibility, or design compliance |
| `writing-guidelines` | Reviewing docs/prose, tone, or style |
| `deploy-to-vercel` | Deploying this app or creating a preview deployment |
| `vercel-cli-with-tokens` | Vercel CLI work using token-based (non-interactive) auth |
| `vercel-optimize` | Investigating Vercel cost/performance on a deployed instance of this app |
| `vercel-composition-patterns` | Designing/refactoring React component APIs (not yet used in this repo — plain Express/vanilla JS today) |
| `vercel-react-best-practices` | React/Next.js performance work (not yet applicable — this repo has no React yet) |
| `vercel-react-native-skills` | React Native/Expo work (not applicable to this repo) |
| `vercel-react-view-transitions` | React View Transition animations (not applicable to this repo) |

Auto-invocation is a selection convenience only — it does **not** change confirmation requirements for
risky actions (deletions, pushes, deployments, spending, credentials, etc.). Those still require the
same explicit user confirmation as any other action.

## Shortcut commands

Each installed skill also has a matching `/` command in `.claude/commands/` (e.g. `/review-ui`,
`/deploy`) for explicitly invoking it with arguments. See that directory for the full list.
