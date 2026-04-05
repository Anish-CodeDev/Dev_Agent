---
name: skill-generator
description: >
  Generates a well-structured SKILL.md file for a given topic so that an LLM agent
  can learn and execute tasks it wouldn't natively know how to do. Use this skill
  whenever a user provides a topic and wants a skill file generated, says things like
  "generate a skill for X", "create a skill that does Y", "make a SKILL.md for Z",
  or provides a prompt template asking to produce skill documentation. Strongly prefer
  this skill for software/code tasks (libraries, APIs, SDKs) and workflow/process tasks
  (CI/CD, deployment, automation pipelines). Always include test cases in the output.
  The generated skill is intended for use in a custom LLM agent, not necessarily Claude.ai.
---

# Skill Generator

Generates a complete, agent-ready `SKILL.md` file from a topic description. The output
teaches an LLM agent exactly how to perform a task — with enough structure, examples,
and test cases that the agent can execute it reliably without further instruction.

---

## When You're Invoked

The user has provided a topic (free-form text, a prompt template, or a description).
Your job is to produce a `SKILL.md` that fully captures how to accomplish that topic.

---

## Step 1 — Clarify Intent (if needed)

Before writing, check whether you have enough information. If any of these are unclear, ask:

- **What does success look like?** (a file, an API response, a deployed service, a report?)
- **What inputs does the agent receive?** (a file path, a URL, user text, env vars?)
- **Are there tools or libraries the agent must use?** (specific SDKs, CLIs, APIs?)
- **What environment does the agent run in?** (Python, Node, bash, Docker, etc.?)
- **Are there common failure modes to guard against?**

If the topic is clear enough (e.g. "use the Stripe API to create a charge"), skip this
and proceed directly.

---

## Step 2 — Research the Topic

For software/API topics: reason about the library's interface, common patterns, auth
requirements, error handling, and gotchas. If you have web search, look up the official
docs for the specific version/API surface mentioned.

For workflow/process topics: identify the sequence of steps, tools involved at each
stage, required config, and how success/failure is signalled.

---

## Step 3 — Write the SKILL.md

Use the template below. Fill every section — do not leave placeholders. Write in the
**imperative voice** ("Install the dependency", "Call the endpoint", "Check the exit code").

Explain *why* things matter, not just *what* to do. This helps the agent handle variants
and edge cases it hasn't seen before.

### SKILL.md Template

```markdown
---
name: <kebab-case-name>
description: >
  <One concise paragraph. State: what the skill does, when to trigger it (specific
  user phrases and contexts), what inputs it expects, and what it produces.
  Be slightly "pushy" — list concrete trigger phrases so the agent doesn't undertrigger.>
compatibility:
  runtime: <e.g. Python 3.10+, Node 18+, bash>
  dependencies: <list key packages/tools, or "none">
  env_vars: <list required env vars, or "none">
---

# <Skill Title>

<1–2 sentence summary of what this skill accomplishes and why it exists.>

---

## Prerequisites

<List everything that must be true before the agent starts: installed packages,
credentials, access permissions, env vars set. Be specific — include install commands
where relevant.>

```bash
# Example setup
pip install stripe   # or npm install, brew install, etc.
```

---

## Core Concepts

<Briefly explain the mental model the agent needs. For an API skill: auth flow,
key resources, rate limits. For a workflow skill: the stages and how they connect.
2–4 short paragraphs or a bulleted list. Skip this section only if the topic is trivial.>

---

## Step-by-Step Instructions

<Number each step. For each step:>
1. **What to do** — imperative, specific.
2. **Why it matters** — one sentence if non-obvious.
3. **Example** — a minimal code snippet or command where helpful.

<Keep steps atomic. If a step has more than ~5 lines of code, move the code to a
`## Full Example` section and reference it here.>

---

## Full Example

<A complete, runnable example from inputs to output. Include all imports, config,
error handling. Annotate non-obvious lines with inline comments.>

```<language>
# Full working example
```

---

## Error Handling & Edge Cases

<List the most common failure modes and what to do about each. Format as a table
or bullet list with "Symptom → Cause → Fix".>

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `AuthenticationError` | API key missing or wrong | Check `ENV_VAR_NAME` is set and valid |
| Timeout on step N | ... | ... |

---

## Output Format

<Describe exactly what the agent should produce when done: file path, JSON shape,
printed output, side effect (e.g. "a new GitHub PR is open"). If the output format
is flexible, describe the recommended default.>

---

## Test Cases

<Always include 3 test cases. Each has: a realistic user prompt, the expected
agent behaviour, and pass/fail criteria.>

### Test Case 1 — Happy Path
**Prompt:** `<realistic user request>`
**Expected behaviour:** <what the agent does step by step>
**Pass criteria:** <what to check to confirm it worked>

### Test Case 2 — Edge Case
**Prompt:** `<a realistic but trickier variant>`
**Expected behaviour:** <...>
**Pass criteria:** <...>

### Test Case 3 — Error Recovery
**Prompt:** `<a prompt that triggers a recoverable error>`
**Expected behaviour:** <agent detects the error, reports it clearly, suggests fix>
**Pass criteria:** <error is surfaced, not silently swallowed>
```

---

## Step 4 — Review Your Output

Before finalising, check:

- [ ] Every section of the template is filled (no `<placeholder>` text remains)
- [ ] The `description` frontmatter includes specific trigger phrases
- [ ] Prerequisites list exact install commands and env var names
- [ ] The full example actually runs (mentally trace through it)
- [ ] All 3 test cases are distinct and cover happy path, edge case, error recovery
- [ ] Instructions are in imperative voice throughout
- [ ] No section exceeds ~40 lines — split into subsections if needed

---

## Step 5 — Deliver

Output the complete `SKILL.md` content inside a fenced code block so the user
can copy it directly. After the block, briefly state:

1. What the skill covers
2. The 3 test case prompts (one-liners) so the user can quickly verify them

---

## Examples of Good vs. Bad Skill Descriptions

**Bad** (too vague, won't trigger reliably):
> "Helps with API calls."

**Good** (specific, lists trigger phrases):
> "Calls the Stripe API to create charges, refunds, and retrieve customer records.
> Use when the user says 'charge a customer', 'process a payment', 'issue a refund',
> or asks about Stripe billing. Expects a Stripe secret key in `STRIPE_SECRET_KEY`."

---

## Notes on Scope

- **Software/code skills**: Always include auth setup, a minimal working code example,
  and the exact import statements. Don't assume the agent knows the library's idioms.
- **Workflow/process skills**: Always include a diagram or numbered pipeline if there
  are more than 3 sequential stages. Call out where human approval or external triggers
  are needed.
- Keep the SKILL.md under 500 lines. If the topic is large (e.g. "deploy to AWS ECS
  with autoscaling and logging"), split into a main SKILL.md that orchestrates, plus
  `references/` files for each sub-topic.
