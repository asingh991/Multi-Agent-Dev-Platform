# Multi-Agent Autonomous Development Platform

A CrewAI-based system where four specialised AI agents (Planner, Developer, Reviewer and Tester) work through a software request in sequence, passing their results to one another. Give it a request such as "a command-line todo list app" and it produces a plan, the code, a code review and a pytest file.

> **Credit:** The idea and base code for this project come from Nicholas Renotte's tutorial ["How to Build a Multi Agent AI System"](https://youtu.be/gUrENDkPw_k) and his repository [nicknochnack/WatsonxCrewAI](https://github.com/nicknochnack/WatsonxCrewAI), which builds a keynote-writing crew with CrewAI and IBM watsonx.ai. See [Acknowledgements](#acknowledgements) for what I changed.

## Why this project exists

One prompt that tries to plan, code, review and test at once tends to produce shallow results. Splitting the work into roles mirrors how a small engineering team operates: each agent has one job, sees only what it needs, and builds on the previous agent's output.

## How it works

```
request
   │
   ▼
[Planner]  ──►  outputs/plan.md
   │
   ▼
[Developer] ──►  outputs/solution.py
   │
   ▼
[Reviewer]  ──►  outputs/review.md
   │
   ▼
[Tester]    ──►  outputs/test_solution.py
```

1. **Planner** turns the request into a numbered implementation plan.
2. **Developer** implements the plan as a single Python file.
3. **Reviewer** reads the code and lists bugs and improvements, most severe first.
4. **Tester** writes pytest tests using both the code and the review, so tests can target the weak points the reviewer found.

Agents communicate through CrewAI task context: each task declares which earlier outputs it receives, and the crew runs them in order.

## Design decisions

- **Prompts live in `prompts.yaml`, not in code.** Every agent role, goal, backstory and every task description is defined in one YAML file. Prompts can be edited, compared and version-controlled without touching Python.
- **Model selection at startup.** The program tests each model in `GEMINI_MODELS` with a small call and uses the first one that works. This avoids failing mid-run on a model that has no free-tier quota.
- **Rate-limit awareness.** The crew paces its requests (`max_rpm`) to stay inside free-tier limits.
- **Execution tracking.** Each run writes `outputs/run_log.json` with the request, the model used, time per task, total time and token usage, so runs can be compared.
- **Secrets stay out of Git.** The API key lives in `.env`, which is in `.gitignore`.

## Tech stack

Python 3.12 · CrewAI · Google Gemini API · PyYAML · python-dotenv · pytest · Git/GitHub

## Setup

```bash
git clone https://github.com/asingh991/Multi-Agent-Dev-Platform.git
cd Multi-Agent-Dev-Platform
pip install "crewai[google-genai]" python-dotenv pyyaml
```

CrewAI requires Python 3.10 to 3.13. Create a `.env` file (never commit it):

```
GOOGLE_API_KEY=your_key_here
GEMINI_MODELS=model_id_1,model_id_2
```

## Usage

```bash
python main.py "a command-line todo list app"
```

Results are written to `outputs/`: `plan.md`, `solution.py`, `review.md`, `test_solution.py` and `run_log.json`.

## Project structure

| File | Purpose |
|---|---|
| `main.py` | Builds the agents, tasks and crew, selects a working model, runs the workflow and writes the run log |
| `prompts.yaml` | All agent and task prompts |
| `.env` | API key and model list (not committed) |

## Current limitations

- Agents run one after another, so a run takes as long as all four steps combined.
- Generated code and tests are not executed automatically, so correctness is not verified by the system.
- The model is chosen once at startup and does not switch if it hits a limit mid-run.

## Roadmap

- Run generated code and tests in an isolated Docker container with log capture
- Add a self-correction loop that feeds test failures back to the Developer agent
- Run independent steps concurrently with asynchronous orchestration
- Benchmark runs across models and prompt versions

## Acknowledgements

This project is based on the idea and starting code from [Nicholas Renotte's tutorial](https://youtu.be/gUrENDkPw_k) and his [WatsonxCrewAI repository](https://github.com/nicknochnack/WatsonxCrewAI). From that work I kept the core pattern: agents with roles and goals, tasks that pass context to one another, and a crew that runs them in sequence.

What I changed or added:

- Replaced IBM watsonx.ai with the Google Gemini API (free tier)
- Replaced the keynote researcher and writer with four software-development agents: Planner, Developer, Reviewer and Tester
- Moved all prompts into `prompts.yaml`
- Added startup model selection, request pacing and execution logging (`run_log.json`)
- Updated the code to the current CrewAI version
