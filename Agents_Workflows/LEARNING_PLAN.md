# AI Agents & Workflows — Learning Roadmap

**Keyword to resume**: `AGENTFLOW`
When you say **AGENTFLOW** at the start of any session, your assistant will recall this plan and your last stopping point.

**Stack**: Python + Claude API (claude-sonnet-4-6)
**Pre-requisites met**: Google Cloud GenAI cert, Claude API, MCP, Prompt Engineering, Claude Code

---

## How Sessions Work
Each module contains:
- **Theory** — concepts explained clearly
- **Q&A** — questions you answer, graded on the spot
- **Coding Lab** — guided hands-on exercise
- **Checkpoint** — marks progress in PROGRESS.md

Your final grade (1–10) is calculated at the end of Phase 5 based on Q&A accuracy and code quality across all phases.

---

## Phase 1 — Conceptual Foundations
**Goal**: Clearly understand what agents and workflows are, and when to use each.

### Module 1.1 — Workflows vs Agents
- What is an AI Workflow? (deterministic, structured, predictable)
- What is an AI Agent? (autonomous, dynamic, tool-using, loop-based)
- Key differences table
- Real-world examples of each
- Decision framework: when to use a workflow vs an agent

### Module 1.2 — Core Patterns (Theory)
- Workflow patterns: Sequential Chain, Parallel Fan-out, Conditional Router, Evaluator-Optimizer
- Agent patterns: ReAct (Reason + Act), Plan-and-Execute, Reflection
- Orchestrator + Subagent pattern (combining both)

### Module 1.3 — Q&A Session #1
- 5 conceptual questions (graded)
- Short discussion on answers

**Checkpoint 1**: After Q&A #1 passes, move to Phase 2.

---

## Phase 2 — Building Your First AI Workflow
**Goal**: Build a working multi-step document analysis workflow using the Claude API.

### Module 2.1 — Anatomy of a Workflow
- Steps, state, handoffs
- Why workflows are deterministic (you control the flow, not the LLM)
- How to chain Claude API calls together
- Passing context between steps

### Module 2.2 — Coding Lab A: Document Analysis Workflow
Build a 4-step pipeline in Python:
```
Input Document
    → Step 1: Extract key facts (Claude call)
    → Step 2: Summarize in 3 bullets (Claude call)
    → Step 3: Classify topic + sentiment (Claude call)
    → Step 4: Generate 3 action items (Claude call)
    → Final structured output (JSON)
```
Files to create: `workflow/document_pipeline.py`

### Module 2.3 — Q&A Session #2
- 5 questions on workflow design and the code you just wrote
- Code review discussion

**Checkpoint 2**: After Lab A and Q&A #2, move to Phase 3.

---

## Phase 3 — Building Your First AI Agent
**Goal**: Build a working tool-using agent with an autonomous loop using the Claude API.

### Module 3.1 — Anatomy of an Agent
- The agent loop: Observe → Think → Act → Observe (repeat)
- Tools / Function calling — how Claude decides when to use them
- Memory: in-context (conversation history) vs external
- Stopping conditions: when does the agent decide it's done?

### Module 3.2 — The ReAct Pattern
- Reason: Claude thinks about what to do next
- Act: Claude calls a tool
- Observe: Tool result is fed back into context
- Repeat until goal is achieved

### Module 3.3 — Coding Lab B: Research Agent
Build a research agent in Python with 4 tools:
```python
tools = [
    web_search(query)      # simulated — returns fake results
    calculator(expression) # evaluates math
    save_note(text)        # writes to a local notes file
    read_notes()           # reads saved notes
]
```
Agent task: *"Research the top 3 benefits of solar energy, calculate average cost savings of 20%, and save a summary note."*

The agent should run autonomously through multiple tool calls until it completes the task.

Files to create: `agent/research_agent.py`, `agent/tools.py`

### Module 3.4 — Q&A Session #3
- 5 questions on agent design, tool use, and your code
- Discussion on agent failure modes and guardrails

**Checkpoint 3**: After Lab B and Q&A #3, move to Phase 4.

---

## Phase 4 — Putting It Together
**Goal**: Combine an agent and a workflow. Understand when hybrid architectures make sense.

### Module 4.1 — Hybrid Architectures
- Agent as orchestrator, workflows as sub-tasks
- When to hardcode steps (workflow) vs let the model decide (agent)
- Cost, latency, and reliability trade-offs

### Module 4.2 — Memory Patterns
- Short-term: conversation history (in-context)
- Long-term: file/database-backed memory
- Semantic memory: vector search (overview only)

### Module 4.3 — Coding Lab C: Agent-Orchestrated Workflow
Extend your research agent so that after it finishes research, it automatically triggers your document analysis workflow on the notes it saved.

```
Research Agent runs →
    → saves notes →
        → Document Workflow runs on notes →
            → produces final structured report
```

Files to modify: `agent/research_agent.py`, `workflow/document_pipeline.py`
New file: `main.py` (orchestrates both)

### Module 4.4 — Q&A Session #4
- 5 questions on hybrid design and trade-offs

**Checkpoint 4**: After Lab C and Q&A #4, move to Phase 5.

---

## Phase 5 — Final Assessment
**Goal**: Demonstrate mastery through a final challenge and graded review.

### Module 5.1 — Final Coding Challenge
Build a small end-to-end system from a prompt (given fresh in the session, no hints).

### Module 5.2 — Final Q&A
- 10 mixed questions across all phases

### Module 5.3 — Grading Rubric (1–10)

| Category                        | Max Points |
|---------------------------------|-----------|
| Q&A Sessions #1–4 accuracy      | 3.0       |
| Coding Lab A (Workflow)         | 1.5       |
| Coding Lab B (Agent)            | 1.5       |
| Coding Lab C (Hybrid)           | 1.5       |
| Final Q&A                       | 1.5       |
| Final Coding Challenge          | 1.0       |
| **Total**                       | **10.0**  |

---

## Quick Reference: Key Concepts

| Concept          | Workflow                          | Agent                              |
|------------------|-----------------------------------|------------------------------------|
| Control flow     | Developer-defined                 | LLM-driven                         |
| Predictability   | High                              | Lower (more autonomous)            |
| Best for         | Repeatable, structured tasks      | Open-ended, dynamic tasks          |
| Loop             | Fixed number of steps             | Loops until goal met               |
| Tools            | Optional                          | Core to how agents act             |
| Example          | ETL pipeline, report generation   | Research assistant, coding agent   |

---

## Environment Setup (do once before Phase 2)
```bash
# From project root
uv add anthropic python-dotenv
```
Create `.env`:
```
ANTHROPIC_API_KEY=your_key_here
```
