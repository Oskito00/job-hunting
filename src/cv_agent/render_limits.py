from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RenderLimits:
    profile_chars: int = 700
    work_bullet_chars: int = 190
    project_bullet_chars: int = 170
    additional_item_chars: int = 120
    max_work_items: int = 2
    max_work_bullets_per_item: int = 4
    max_projects: int = 4
    max_project_bullets: int = 2
    max_skills: int = 6
    max_additional_experience: int = 3


class RenderLimitError(RuntimeError):
    pass


def validate_render_limits(content: dict[str, object], limits: RenderLimits | None = None) -> list[str]:
    active_limits = limits or RenderLimits()
    errors: list[str] = []
    errors.extend(validate_profile_limit(content, active_limits))
    errors.extend(validate_work_limits(content, active_limits))
    errors.extend(validate_project_limits(content, active_limits))
    errors.extend(validate_skill_limits(content, active_limits))
    errors.extend(validate_additional_limits(content, active_limits))
    return errors


def validate_profile_limit(content: dict[str, object], limits: RenderLimits) -> list[str]:
    profile = content.get("profile")
    text = profile.get("content", "") if isinstance(profile, dict) else ""
    return validate_text_length("profile.content", str(text), limits.profile_chars)


def validate_work_limits(content: dict[str, object], limits: RenderLimits) -> list[str]:
    items = list_items(content.get("work_experience"))
    errors = validate_count("work_experience", items, limits.max_work_items)
    for index, item in enumerate(items):
        bullets = list_items(item.get("bullets") if isinstance(item, dict) else None)
        errors.extend(validate_count(f"work_experience[{index}].bullets", bullets, limits.max_work_bullets_per_item))
        errors.extend(validate_bullet_lengths(bullets, f"work_experience[{index}].bullets", limits.work_bullet_chars))
    return errors


def validate_project_limits(content: dict[str, object], limits: RenderLimits) -> list[str]:
    projects = list_items(content.get("projects"))
    errors = validate_count("projects", projects, limits.max_projects)
    for index, project in enumerate(projects):
        bullets = list_items(project.get("bullets") if isinstance(project, dict) else None)
        errors.extend(validate_count(f"projects[{index}].bullets", bullets, limits.max_project_bullets))
        errors.extend(validate_bullet_lengths(bullets, f"projects[{index}].bullets", limits.project_bullet_chars))
    return errors


def validate_skill_limits(content: dict[str, object], limits: RenderLimits) -> list[str]:
    return validate_count("skills", list_items(content.get("skills")), limits.max_skills)


def validate_additional_limits(content: dict[str, object], limits: RenderLimits) -> list[str]:
    items = list_items(content.get("additional_experience"))
    errors = validate_count("additional_experience", items, limits.max_additional_experience)
    errors.extend(validate_bullet_lengths(items, "additional_experience", limits.additional_item_chars))
    return errors


def validate_count(label: str, items: list[object], limit: int) -> list[str]:
    if len(items) <= limit:
        return []
    return [f"{label} has {len(items)} items; limit is {limit}"]


def validate_bullet_lengths(items: list[object], label: str, limit: int) -> list[str]:
    errors: list[str] = []
    for index, item in enumerate(items):
        text = item.get("text", "") if isinstance(item, dict) else ""
        errors.extend(validate_text_length(f"{label}[{index}].text", str(text), limit))
    return errors


def validate_text_length(label: str, text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return []
    return [f"{label} is {len(text)} chars; limit is {limit}"]


def list_items(value: object) -> list[object]:
    return value if isinstance(value, list) else []
