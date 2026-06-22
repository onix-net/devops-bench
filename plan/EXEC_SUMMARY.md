The fix is a single deletion of the preamble paragraph. This is a straightforward, well-specified edit, so I'll output the corrected markdown directly.

# devops-bench: A Neutral Industry Standard for Measuring AI Agents on Real DevOps Work

**One sentence:** devops-bench measures how well AI agents handle the operational work of running modern cloud systems, on real infrastructure, scored on whether they actually fixed the problem.

## The opportunity

DevOps is one of the largest and most important domains in SDLC relying on humans. As AI agents move into this space, the natural claim is that theirs is the best. There are many ways to judge an agent, but today, there is no neutral, repeatable industry standard for DevOps- which is different than other spaces like SWE-bench.
Whoever establishes that standard shapes how the entire market evaluates agents, and Google is positioned to set it.

## What it is

devops-bench puts agents into the operational scenarios they actually encounter day to day, on real infrastructure, and then checks the outcome. The agent acts, and we verify whether the system was truly fixed, not whether the agent described a plausible fix. Two properties make the results trustworthy and comparable: scenarios are built in predictable, repeatable ways, and performance is scored in predictable, repeatable ways. The same performance earns the same score every time.

## Why it is credible and hard to game

Results are graded on real outcomes (did the system actually get fixed), not on another model's opinion. The benchmark is also resistant to gaming and contamination by design:

- Scenarios vary on every run, so memorized answers do not transfer.
- The same symptom can have a different underlying cause each time, so a canned playbook fails.
- The agent never sees the answer key.

A high score therefore reflects real capability, not memorization.

## The plan

Wave 1 delivers roughly 115 real-world scenarios in 6 to 8 weeks, going deep on Google Cloud and Kubernetes first, with AWS and Azure to follow on the same foundation. A small, AI-fluent team (one lead plus two engineers) steers an AI "factory" that mass-produces and automatically quality-checks the scenarios. People set the direction and the quality bar; the AI does the volume.

## What the investment buys

- A defensible, neutral industry standard Google can anchor to.
- Very cheap to scale: each new scenario is mostly an AI run plus a quick human check, not weeks of engineering.
- Fair, broad coverage that makes Google Cloud and Kubernetes strengths obvious without looking biased.

## Where we are and what is next

We are starting from a small existing benchmark on a deliberately constrained, low-risk path. The near-term work is focused: extend the scoring the benchmark already has so results are graded on real outcomes; build the scenario factory, including the same-symptom-different-cause variation and an automatic validation step that proves every generated scenario is solvable and not trivially passable; and stand up continuous testing that runs reference agents against the benchmark to keep producing signal. Full execution detail lives in PROJECT_AND_STAFFING_PLAN.md.
