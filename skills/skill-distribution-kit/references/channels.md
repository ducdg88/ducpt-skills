# Skill distribution channels

Checked September 2026. Registries change often; verify each link before submitting.

## Tier 1. Registries and install surfaces (people already intend to install)

| Channel | How to get listed | Notes |
|---|---|---|
| skills.sh (the `skills` npm CLI) | Public GitHub repo with `skills/<name>/SKILL.md`; users run `npx skills add owner/repo`. Installs are tracked on the leaderboard. | Largest install volume. Test the command yourself first. |
| ClawHub (clawhub.ai) | Sign in with GitHub and publish from the site, or use the CLI described at docs.openclaw.ai. Users install with `openclaw skills install @owner/skill`. Listings show downloads and a security audit. | The real site is clawhub.ai. `claw-hub.net` is a lookalike, do not use it. |
| Claude Code plugin marketplace (your own) | Add `.claude-plugin/marketplace.json`; users run `/plugin marketplace add owner/repo`. | Works on day one, no approval. |
| claude-plugins-community | Submit through the community plugin directory form or PR, following its template. | Higher trust, slower. |
| Gemini CLI extensions, awesome-copilot | Follow each repo's contribution guide. | Same skill, new audience. |

## Tier 2. Index and discovery

| Channel | Action |
|---|---|
| GitHub topics | Up to 20 topics: agent-skills, claude-skills, claude-code, claude-code-plugin, skills, ai-agents, plus niche words. |
| Awesome lists | Open a PR on lists such as awesome-claude-skills and awesome-claude-code. One line, follow their format, one PR per list. |
| Your website | One page per skill with install command, what it does, example output, and JSON-LD. Submit the sitemap in Google Search Console. |
| llms.txt | Cheap to add. It is not a strong ranking lever on its own. |

## Tier 3. Communities (bring a demo, not a collection)

r/ClaudeCode, r/ClaudeAI, r/cursor, dev.to (#claudecode), Hacker News "Show HN" only with a surprising working demo, Viblo.asia for Vietnamese developers, Facebook groups about Claude and AI agents, Discord servers of each tool. Answer real questions and link the skill only where it solves that question.

## Tier 4. Media

Your own X or Facebook thread with the origin story and real numbers first, then pitch small YouTube channels and newsletters that cover agent tooling.

## Measurement

- Tag links: `?utm_source=<channel>&utm_medium=<post|pr|listing>`.
- Save GitHub traffic daily (it expires after 14 days).
- Watch referrers for chatgpt.com and perplexity.ai: that is AI assistants recommending you.
