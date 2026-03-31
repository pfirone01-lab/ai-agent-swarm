# AI Agent Swarm

A 4-agent AI pipeline that generates, evaluates, selects and formats
optimised sales emails automatically. Built with Gemini API and 
automated via GitHub Actions. Model-agnostic and portable to Claude API.

## Agents
- **Generator** — creates 3 versions of the email
- **Evaluator** — scores each version on clarity, CTA and tone
- **Selector** — picks the highest performing version
- **Formatter** — polishes and delivers the final output

## How to Run
Add your Gemini API key as a GitHub Secret named GEMINI_API_KEY
then trigger the workflow manually from the Actions tab.
