from __future__ import annotations

from collections.abc import Sequence
import json
import os
from pathlib import Path
from typing import Any

from cv_agent.config import load_static_profile_config
from cv_agent.schemas import CVContent, content_to_dict, validate_cv_content
from cv_agent.tools import ToolRuntime, build_tools


DEFAULT_MODEL = "gpt-5.5"


class CVAgentError(RuntimeError):
    pass


def run_cv_agent(job_text: str, company: str, role: str, bank_dir: Path, model: str | None = None, page_mode: str | None = None) -> dict[str, object]:
    agent = build_cv_agent(bank_dir=bank_dir, model=model)
    prompt = build_agent_prompt(job_text=job_text, company=company, role=role, page_mode=page_mode)
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


def run_agent_sync(agent, prompt: str | Sequence[dict[str, Any]]):
    from agents import Runner

    return Runner.run_sync(agent, prompt, max_turns=20)


def revise_cv_content_for_fit(
    cv_content: dict[str, object],
    render_errors: list[str],
    job_text: str,
    company: str,
    role: str,
    bank_dir: Path,
    model: str | None = None,
) -> dict[str, object]:
    agent = build_cv_agent(bank_dir=bank_dir, model=model)
    prompt = build_revision_prompt(cv_content=cv_content, render_errors=render_errors, job_text=job_text, company=company, role=role)
    result = run_agent_sync(agent, prompt)
    content = content_to_dict(result.final_output)
    errors = validate_cv_content(content)
    if errors:
        raise CVAgentError("Revised CV content failed validation: " + "; ".join(errors))
    return content


def build_agent_prompt(job_text: str, company: str, role: str, page_mode: str | None = None) -> str:
    page_guidance = page_mode or "agent_decides_preserve_all_roles"
    return f"""Create tailored CV content JSON for this application.

Company: {company}
Role: {role}
Page mode: {page_guidance}

Job description:
{job_text}
"""


def build_revision_prompt(cv_content: dict[str, object], render_errors: list[str], job_text: str, company: str, role: str) -> str:
    return f"""Revise this tailored CV content so it fits the requested one-page render limits.

Company: {company}
Role: {role}

Render errors:
{chr(10).join(f"- {error}" for error in render_errors)}

Revision policy:
- Keep all work roles if at all possible.
- Shorten bullets, reduce projects, and tighten profile/skills before dropping a work role.
- If a role must be omitted to satisfy one-page rendering, omit only the least relevant/oldest role and preserve evidence coverage for the roles kept.

Current CV content JSON:
{json.dumps(cv_content, indent=2, ensure_ascii=False)}

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
- Use evidence paths exactly as returned by the tools, for example "projects/payment-platform.md".
- Do not invent metrics, employers, titles, dates, education, client names, technologies, or outcomes.
- Treat needs_review or needs_clarification in source files as caution flags; do not present those details as confirmed.
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
- Include side projects only when they strengthen the match to the job.
- Decide whether work, projects, skills, or additional_experience best express the candidate's fit for this role.
- Set page_mode to "one_page" when a concise one-page CV is best, or "multi_page" when the role benefits from more detail. Obey an explicit Page mode if provided.
- Include all work roles by default, using the order implied by the source CV or reverse chronology. Tailor the number and wording of bullets inside each role rather than omitting roles.
- If Page mode is agent_decides_preserve_all_roles, preserve all work roles and choose multi_page unless all roles naturally fit on one page without cramped wording.
- If Page mode is one_page, keep all work roles but compress them: use fewer bullets for weakly relevant roles, maximum 4 bullets per role, maximum 4 projects, and maximum 2 bullets per project.
- Drop a work role only if explicit one-page rendering cannot fit after compression. If you drop a role, mention that omission in additional_experience with evidence.
- If Page mode is multi_page or agent_decides, include more relevant detail where it improves the application, but avoid padding.
- Output exactly 6 skills where possible, ordered by relevance to the job description.
- Skill categories must be one of: ai, software, product, infra, data, other.
- Skill names must be concise labels, ideally 1-3 words and no longer than 28 characters, so they fit on one line.
- Skills must be meaningful hiring signals, not generic AI-sounding labels. Avoid vague skills such as "Python APIs", "AI tools", "coding", or "software development".
- Prefer specific, credible capabilities from the evidence bank when relevant and supported.
- Prefer recruiter-recognisable skill labels; use Product Discovery or User Feedback Loops instead of Requirements Gathering when that better matches the job description.
- Do not assign skill ratings or imply proficiency stars.
- Keep bullets short, punchy, and concrete-tech-first.
- Work bullets should usually be 100-155 characters; project bullets should usually be 90-140 characters.
- Prefer one concrete claim per bullet.
- Start bullets with strong verbs and include the most relevant technologies naturally.
- Avoid long explanatory clauses, stacked context, and "including..." lists unless essential.
- Recruiters may skim for keywords, so surface concrete tools and systems clearly: LangChain, MCP, ChromaDB, Neo4j, Cypher, Docker, GitHub Actions, Nginx, Flask, Express, XGBoost, etc. when supported and relevant.
- Keep project names short and scannable; prefer technology-specific names where helpful, such as "ChromaDB CV Ranking System".
- Include contact and education from the static profile config.
"""
