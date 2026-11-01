import os
import sys
from pathlib import Path
from google import genai

from crewai import LLM, Agent, Crew, Process, Task
from dotenv import load_dotenv

# ---------- Config ----------
load_dotenv()
MODELS = [m.strip() for m in os.getenv("GEMINI_MODELS", "").split(",") if m.strip()]
API_KEY = os.getenv("GOOGLE_API_KEY")
if not MODELS or not API_KEY:
    sys.exit("Set GOOGLE_API_KEY and GEMINI_MODELS in .env")
Path("outputs").mkdir(exist_ok=True)

# ---------- LLM (first model that works) ----------
def pick_model(models: list[str]) -> str:
    client = genai.Client(api_key=API_KEY)
    for m in models:
        try:
            client.models.generate_content(model=m, contents="ping")
            print(f"Using model: {m}")
            return m
        except Exception as e:
            print(f"Skipping {m}: {str(e)[:90]}")
    sys.exit("No model in GEMINI_MODELS works on this key.")


llm = LLM(model=f"gemini/{pick_model(MODELS)}", api_key=API_KEY, temperature=0.2)

# ---------- Agents ----------
def make_agent(role: str, goal: str, backstory: str) -> Agent:
    return Agent(role=role, goal=goal, backstory=backstory, llm=llm,
                 allow_delegation=False, verbose=True)

planner = make_agent(
    "Software Planner",
    "Turn a software request into a clear, ordered implementation plan",
    "You are a tech lead who plans small Python projects precisely.",
)
developer = make_agent(
    "Python Developer",
    "Implement the plan as clean, working Python code",
    "You are a senior Python developer who writes simple, readable code.",
)
reviewer = make_agent(
    "Code Reviewer",
    "Find bugs, style problems and risks in the code",
    "You are a strict reviewer who lists issues from most to least severe.",
)
tester = make_agent(
    "Test Engineer",
    "Write pytest tests that verify the code",
    "You are a QA engineer who writes focused pytest tests.",
)

# ---------- Tasks ----------
plan_task = Task(
    description="Create a short implementation plan for this request: {request}",
    expected_output="A numbered plan listing the functions and their behaviour",
    agent=planner,
    output_file="outputs/plan.md",
)
dev_task = Task(
    description="Implement the plan in a single Python file. Return raw Python code only, no markdown fences.",
    expected_output="Complete Python source code",
    agent=developer,
    context=[plan_task],
    output_file="outputs/solution.py",
)
review_task = Task(
    description="Review the code. List bugs and improvements, most severe first.",
    expected_output="A prioritised review",
    agent=reviewer,
    context=[dev_task],
    output_file="outputs/review.md",
)
test_task = Task(
    description="Write pytest tests for the code (it lives in solution.py). Return raw Python code only, no markdown fences.",
    expected_output="A complete pytest file",
    agent=tester,
    context=[dev_task, review_task],
    output_file="outputs/test_solution.py",
)

# ---------- Crew ----------
crew = Crew(
    agents=[planner, developer, reviewer, tester],
    tasks=[plan_task, dev_task, review_task, test_task],
    process=Process.sequential,
    max_rpm=8,  # stay under free-tier request limits
    verbose=True,
)

# ---------- Run ----------
if __name__ == "__main__":
    request = " ".join(sys.argv[1:]) or "a command-line todo list app"
    result = crew.kickoff(inputs={"request": request})
    print("\nDone. Files saved in outputs/")