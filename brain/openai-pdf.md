# A Practical Guide to Building Agents

*Adapted from the OpenAI PDF – Markdown version* citeturn8file0

---

## Table of Contents
1. [Introduction](#introduction)
2. [What Is an Agent?](#what-is-an-agent)
3. [When Should You Build an Agent?](#when-should-you-build-an-agent)
4. [Agent Design Foundations](#agent-design-foundations)
   - [Selecting Your Models](#selecting-your-models)
   - [Defining Tools](#defining-tools)
   - [Configuring Instructions](#configuring-instructions)
5. [Orchestration Patterns](#orchestration-patterns)
   - [Single‑Agent Systems](#single-agent-systems)
   - [Multi‑Agent Systems](#multi-agent-systems)
     - [Manager Pattern](#manager-pattern)
     - [Decentralised Pattern](#decentralised-pattern)
6. [Guardrails](#guardrails)
   - [Types of Guardrails](#types-of-guardrails)
   - [Building Guardrails](#building-guardrails)
7. [Conclusion](#conclusion)
8. [More Resources](#more-resources)

---

## Introduction
Large language models (LLMs) can now tackle **complex, multi‑step tasks**. That progress unlocked a new category of systems called **agents**—LLM‑powered workflows that act on a user’s behalf. This guide distils OpenAI’s customer experience into practical advice for teams building their **first agents**. citeturn8file0

---

## What Is an Agent?
*Agents are systems that independently accomplish tasks on your behalf.* Their key traits:

1. **LLM‑controlled workflow execution** – The model decides when the job is done and can self‑correct or bail out.  
2. **Tool use** – Agents call external functions/APIs within strict guardrails. citeturn8file0

Applications that merely add an LLM to a deterministic flow (single‑turn chatbots, classifiers) **are not agents**.

---

## When Should You Build an Agent?
Prioritise workflows that resisted traditional automation because they involve:

| Friction Point | Example |
| -------------- | ------- |
| **Complex decision‑making** | Refund approval in customer service |
| **Rules that are costly to maintain** | Vendor security reviews |
| **Heavy unstructured data** | Insurance‑claim processing |

If deterministic code can solve the task, use it. Otherwise an agent may shine. citeturn8file0

---

## Agent Design Foundations
An agent has three core parts:

| Component | Purpose |
|-----------|---------|
| **Model** | LLM that reasons & decides |
| **Tools** | External functions/APIs the model can call |
| **Instructions** | System prompt & guardrails that shape behaviour |

```python
weather_agent = Agent(
    name="Weather agent",
    instructions="You are a helpful agent who…",
    tools=[get_weather]
)
``` citeturn8file0

### Selecting Your Models
1. Prototype with the most capable model to set a baseline.  
2. Swap in cheaper/faster models **only where accuracy stays acceptable**.  
3. Use evals to measure impact. citeturn8file0

### Defining Tools
Tools extend capability. Three broad types:

- **Data** – fetch context (DB query, web‑search).
- **Action** – mutate state (send email, refund order).
- **Orchestration** – an *agent* wrapped as a tool for another agent.

Tools should have standardised JSON schemas and clear docs. citeturn8file0

### Configuring Instructions
Good instructions:
- Re‑use existing SOPs & policies.  
- Break dense tasks into numbered steps.  
- Map each step to a specific tool/action.  
- Describe edge cases explicitly. citeturn8file0

Example template snippet:
```jinja
You are a call‑centre agent. User: {{user_first_name}} (member {{user_tenure}})…
```

---

## Orchestration Patterns
### Single‑Agent Systems
Start simple: one agent, multiple tools, run in a loop until:
1. It calls a designated *final‑output* tool, or  
2. Returns a direct answer, or  
3. Hits max‑turns / error.

Prompt templates + variables keep complexity manageable. citeturn8file0

### Multi‑Agent Systems
Split only when a single agent struggles.

#### Manager Pattern
A **central manager agent** calls specialised agents as *tools*, synthesising results.

#### Decentralised Pattern
Agents are peers; they hand off control to each other via *handoff functions* that transfer context.

Code examples for both appear on pages 19–23. citeturn8file0

---

## Guardrails
Layered defences to mitigate data privacy, safety and reputational risks.

### Types of Guardrails
- **Relevance classifier** – flag off‑topic asks.  
- **Safety / jailbreak classifier** – detect prompt injections.  
- **PII filter & OpenAI Moderation API**.  
- **Tool‑risk ratings** – pause or require human approval for high‑risk calls.  
- **Rules‑based** – regex, input length caps.  
- **Output validation** – brand‑voice compliance. citeturn8file0

### Building Guardrails
1. Start with privacy & content‑safety.  
2. Add new layers as you find failures.  
3. Balance security vs. UX; inject human‑in‑loop for high‑risk or repeated failures.

---

## Conclusion
Agents let software **reason through ambiguity, call tools, and finish complex workflows** autonomously. Start with one well‑guarded agent, iterate with real users, and scale up only when necessary. citeturn8file0

---

## More Resources
- OpenAI Developer Docs  
- OpenAI API Platform  
- ChatGPT Enterprise  
- OpenAI safety guidelines  citeturn8file0

