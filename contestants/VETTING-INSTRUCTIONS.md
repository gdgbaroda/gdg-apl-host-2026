# Vetting Instructions (per agent)

You're scoring APL hackathon submissions for the "Build with AI · Agentic Premier League" event.

## Your inputs
- `/Users/knightkill/Code/gdg-apl/contestants/batch-N.json` — 10 records, your assigned batch.
- `/Users/knightkill/Code/gdg-apl/contestants/<slug>/` — the cloned repo for each record where `_clone_status == "ok"`. If status is `bad-url` / `fail`, there is **no repo** — score based on the form fields only and note the missing code as a major penalty.

## Each record contains
- `Full name`, `Project title`, `One-line pitch`, `What does it do?`, `How is it agentic / how did you use AI?`, `Stack & tools`, `Anything else judges should know?`
- `Source code URL`, `Live demo/ video URL`
- `Which challenge?` — `Gamified Habit Builder` or `Data & Insights`
- `_slug`, `_clone_status`

## Score on five criteria (1-10 each; equal weight)

1. **Agentic / AI usage**
   Theme weight. Did they actually use AI (LLM API, agents, RAG, etc.)? Check:
   - Form's "How is it agentic" answer
   - Repo code for `anthropic`, `openai`, `gemini`, `langchain`, `genai`, `crewai`, vector DB libs, `.env` keys for AI providers
   - Code that calls AI APIs (not just imports)
   1 = no AI at all; 5 = single LLM call; 8 = AI is meaningfully integrated; 10 = genuinely agentic multi-step flow.

2. **Live demo / runnability**
   - Try to GET the Live demo URL if present (curl). 2xx = pass.
   - If no demo URL but repo has clear run instructions in README and a deployable structure, give partial credit (4-6).
   - If demo URL 404s / times out, score 1-2.
   - If demo URL is a video (YouTube/Loom), give 4-5 (we can't really verify but they tried).

3. **Code quality + completeness**
   - Project structure (folder organization, file count, line count)
   - README presence/quality
   - Dependencies declared (package.json, requirements.txt, etc.)
   - Whether it looks like a real attempt vs. a 30-min hack
   - If `_clone_status != "ok"`, this is automatically 1-2 (no code to review).

4. **Challenge fit**
   - Does the project actually solve the stated challenge?
   - Gamified Habit Builder: should have habits, streaks, rewards, progress tracking.
   - Data & Insights: should turn match/player/sport data into intuitive insights.
   - 10 = perfect fit, fully addresses the brief; 5 = partial; 1 = unrelated.

5. **Originality**
   - Is the approach novel, or just a generic CRUD/dashboard?
   - Bonus for unusual stacks, creative UX, unexpected angles.
   - 10 = standout idea; 5 = competent but generic; 1 = template-clone.

## Output

Write your scores to `/Users/knightkill/Code/gdg-apl/contestants/scores-batch-N.json` (replace N with your batch number). Format:

```json
[
  {
    "slug": "...",
    "name": "...",
    "title": "...",
    "challenge": "Gamified Habit Builder",
    "scores": {
      "agentic": 7,
      "demo": 5,
      "quality": 8,
      "fit": 9,
      "originality": 6
    },
    "total": 35,
    "reason": "One paragraph: what stood out, what's weak, why these scores. ~80-150 words. Mention specific evidence (file names, code snippets, API keys spotted, demo URL response).",
    "demo_check": "2xx" | "404" | "timeout" | "no-url" | "video",
    "ai_evidence": "anthropic SDK in requirements.txt, Gemini API call in main.py:42" | "no AI code found" | "form-only"
  },
  ...
]
```

## How to work efficiently

- Use `ls`, `head`, `find`, `grep -r` aggressively to scan repos quickly. Don't read every file.
- For AI usage: `grep -rE "anthropic|openai|gemini|genai|langchain|crewai|huggingface|llama|claude" <slug>/ --include='*.py' --include='*.js' --include='*.ts' --include='*.json' --include='*.md' -l` is your friend.
- For demo URL: `curl -s -o /dev/null -w "%{http_code}" --max-time 10 <url>` — quick HEAD-ish check.
- Total time budget: ~3-5 minutes per record. 10 records ≈ 30-45 min per agent in parallel.

When done, send a one-line summary to team-lead via SendMessage with format:
"batch-N done: <count> scored, avg total = X, top = <slug>, bottom = <slug>"
