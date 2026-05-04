from __future__ import annotations

import os
from pathlib import Path

from cv_agent.config import load_static_profile_config
from cv_agent.schemas import CVContent, content_to_dict, validate_cv_content
from cv_agent.tools import ToolRuntime, build_tools


DEFAULT_MODEL = "gpt-5.5"


class CVAgentError(RuntimeError):
    pass


def run_cv_agent(job_text: str, company: str, role: str, bank_dir: Path, model: str | None = None) -> dict[str, object]:
    agent = build_cv_agent(bank_dir=bank_dir, model=model)
    prompt = build_agent_prompt(job_text=job_text, company=company, role=role)
    result = run_agent_sync(agent, prompt)
    content = content_to_dict(result.final_output)
    errors = validate_cv_content(content)
    if errors:
        raise CVAgentError("Generated CV content failed validation: " + "; ".join(errors))
    return content


def build_cv_agent(bank_dir: Path, model: str | None = None):
    from agents import Agent

    runtime = ToolRuntime(
        bank_dir=bank_dir,
        static_config=load_static_profile_config(bank_dir),
    )
    return Agent(
        name="CV Content Agent",
        instructions=agent_instructions(),
        model=model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        tools=build_tools(runtime),
        output_type=CVContent,
    )


def run_agent_sync(agent, prompt: str):
    from agents import Runner

    return Runner.run_sync(agent, prompt, max_turns=20)


def build_agent_prompt(job_text: str, company: str, role: str) -> str:
    return f"""Create tailored CV content JSON for this application.

Company: {company}
Role: {role}

Job description:
{job_text}
"""


def agent_instructions() -> str:
    return """You create tailored CV content from job descriptions.

Use the available tools to search and read the local experience bank before writing.
Use read_static_profile_config for confirmed contact and education details.

Output only structured CV content matching the declared output type.

Rules:
- Every profile sentence, work bullet, project bullet, and additional-experience bullet must include evidence paths from the experience bank.
- Use evidence paths exactly as returned by the tools, for example "projects/cv-database-and-ranking-system.md".
- Do not invent metrics, employers, titles, dates, education, client names, technologies, or outcomes.
- Render Logan Sinclair dates as "June 2025 - Present"; do not include the exact start day.
- Treat needs_clarification in source files as caution flags; do not present those details as confirmed.
- Prefer relevance to the job description over completeness.
- Maximise truthful relevance to the job description for both human reviewers and ATS/AI screening.
- Profile should be 2 sentences maximum and usually 220-280 characters.
- Profile sentence 1 should lead with role positioning and product/use-case outcome, not a long list of tools.
- Profile sentence 2 may include the strongest 3-5 directly relevant tools plus ownership across requirements, demos, rollout feedback, or iteration.
- Avoid vague profile phrases like "customer-facing requirements"; use concrete phrases such as requirements gathering, demos, rollout feedback, or product iteration.
- Prioritise must-have requirements over nice-to-haves.
- Where experience genuinely matches the job description, mirror the employer's terminology naturally.
- Include exact-match technologies, skills, and domain terms from the job description only when supported by evidence.
- Do not keyword-stuff or repeat terms unnaturally.
- Do not mention unsupported requirements just to improve match score.
- Prefer recent, production, beta-tested, client-facing, or measurable work over weaker examples.
- Use "Logan Sinclair" work experience when relevant and preserve its confirmed title/dates.
- Include side projects only when they strengthen the match to the job.
- Output 4 projects when four relevant, distinct projects are available within the bullet limits.
- Treat InBetments and the eBay Fast Notification SaaS as eligible right-column projects when they are relevant to the job description.
- Use InBetments for sports analytics, XGBoost, prediction modelling, quantitative/analytical roles, predictive signals, large-scale historical data, API data ingestion, or model-evaluation matches.
- Use the eBay Fast Notification SaaS for SaaS, marketplace monitoring, alerting, beta testing, external users, product engineering, or ecommerce matches.
- Do not put technical side projects in additional_experience; use additional_experience only for non-technical client-facing roles if needed.
- Keep the right-hand CV column sparse enough for one page: maximum 4 work bullets, maximum 4 projects, and maximum 2 bullets per project.
- Output exactly 6 skills where possible, ordered by relevance to the job description.
- Skill categories must be one of: ai, software, product, infra, data, other.
- Skill names must be concise labels, ideally 1-3 words and no longer than 28 characters, so they fit on one line.
- Skills must be meaningful hiring signals, not generic AI-sounding labels. Avoid vague skills such as "Python APIs", "AI tools", "coding", or "software development".
- Prefer specific, credible capabilities such as LangChain, MCP, ChromaDB, Neo4j/Cypher, Docker, GitHub Actions, Nginx, Vector Search, Retrieval, Product Discovery, or Requirements Gathering when relevant and supported.
- Prefer recruiter-recognisable skill labels; use Product Discovery or User Feedback Loops instead of Requirements Gathering when that better matches the job description.
- Do not assign skill ratings; the renderer assigns ratings deterministically from skill order.
- Keep bullets short, punchy, and concrete-tech-first.
- Work bullets should usually be 100-155 characters; project bullets should usually be 90-140 characters.
- Prefer one concrete claim per bullet.
- Start bullets with strong verbs and include the most relevant technologies naturally.
- Avoid long explanatory clauses, stacked context, and "including..." lists unless essential.
- Recruiters may skim for keywords, so surface concrete tools and systems clearly: LangChain, MCP, ChromaDB, Neo4j, Cypher, Docker, GitHub Actions, Nginx, Flask, Express, XGBoost, etc. when supported and relevant.
- Keep project names short and scannable; prefer technology-specific names where helpful, such as "ChromaDB CV Ranking System".
- Include contact and education from the static profile config.
"""
