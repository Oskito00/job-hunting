from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvidenceText(StrictModel):
    text: str = ""
    evidence: list[str] = Field(default_factory=list)


class ProfileSection(StrictModel):
    content: str
    evidence: list[str] = Field(default_factory=list)


class WorkExperienceSection(StrictModel):
    company: str
    title: str
    dates: str
    bullets: list[EvidenceText] = Field(default_factory=list)


class ProjectSection(StrictModel):
    name: str
    bullets: list[EvidenceText] = Field(default_factory=list)


class SkillSection(StrictModel):
    name: str = ""
    category: str = "other"


class EducationEntry(StrictModel):
    institution: str = ""
    degree: str = ""
    classification: str = ""
    dates: str = ""


class ContactSection(StrictModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    website: str = ""
    github: str = ""
    location: str = ""


class CVContent(StrictModel):
    page_mode: str = "multi_page"
    profile: ProfileSection
    work_experience: list[WorkExperienceSection] = Field(default_factory=list)
    projects: list[ProjectSection] = Field(default_factory=list)
    skills: list[SkillSection] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    contact: ContactSection = Field(default_factory=ContactSection)
    additional_experience: list[EvidenceText] = Field(default_factory=list)


def content_to_dict(content: CVContent | dict[str, Any]) -> dict[str, Any]:
    if isinstance(content, dict):
        return content
    if isinstance(content, BaseModel):
        return content.model_dump()
    raise TypeError(f"Unsupported CV content type: {type(content).__name__}")


def validate_cv_content(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_profile(data.get("profile")))
    errors.extend(validate_evidenced_items(data.get("additional_experience", []), "additional_experience"))
    errors.extend(validate_work_experience(data.get("work_experience", [])))
    errors.extend(validate_projects(data.get("projects", [])))
    errors.extend(validate_skills(data.get("skills", [])))
    return errors


def validate_profile(profile: object) -> list[str]:
    if not isinstance(profile, dict):
        return ["profile must be an object"]
    if profile.get("content") and not profile.get("evidence"):
        return ["profile.content requires evidence"]
    return []


def validate_work_experience(items: object) -> list[str]:
    if not isinstance(items, list):
        return ["work_experience must be a list"]
    errors: list[str] = []
    for index, item in enumerate(items):
        errors.extend(validate_evidenced_items(item.get("bullets", []) if isinstance(item, dict) else [], f"work_experience[{index}].bullets"))
    return errors


def validate_projects(items: object) -> list[str]:
    if not isinstance(items, list):
        return ["projects must be a list"]
    errors: list[str] = []
    for index, item in enumerate(items):
        errors.extend(validate_evidenced_items(item.get("bullets", []) if isinstance(item, dict) else [], f"projects[{index}].bullets"))
    return errors


def validate_skills(items: object) -> list[str]:
    if not isinstance(items, list):
        return ["skills must be a list"]
    if len(items) > 6:
        return ["skills must contain at most 6 items"]
    return []


def validate_evidenced_items(items: object, label: str) -> list[str]:
    if not isinstance(items, list):
        return [f"{label} must be a list"]
    errors: list[str] = []
    for index, item in enumerate(items):
        if isinstance(item, dict) and item.get("text") and not item.get("evidence"):
            errors.append(f"{label}[{index}] requires evidence")
    return errors
