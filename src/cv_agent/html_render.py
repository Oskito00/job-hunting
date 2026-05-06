from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
import re
from typing import Any

from cv_agent.render_limits import RenderLimits, validate_render_limits


HTML_FILENAME = "cv.html"
RENDER_REPORT_FILENAME = "render-report.md"
FLOW_PAGE_MODE = "flow"
ONE_PAGE_MODE = "one_page"
DEFAULT_NAME = "Candidate"
KNOWN_TEMPLATE_PLACEHOLDERS = {
    "title",
    "name",
    "contact",
    "education",
    "skills",
    "profile",
    "work_experience",
    "projects",
    "additional_experience",
    "page_class",
}
REQUIRED_TEMPLATE_PLACEHOLDERS = {"name", "contact", "profile", "work_experience", "projects", "skills", "education"}
PRINT_NORMALIZATION_MARKER = "cv-agent-print-normalization"


@dataclass(frozen=True)
class RenderOptions:
    page_mode: str = FLOW_PAGE_MODE
    template_path: Path | None = None


def render_cv_html_file(cv_content: dict[str, Any], output_dir: Path, limits: RenderLimits | None = None, options: RenderOptions | None = None) -> Path:
    active_options = options or RenderOptions()
    output_dir.mkdir(parents=True, exist_ok=True)
    errors = render_validation_errors(cv_content, active_options, limits)
    write_render_report(output_dir, errors, active_options)
    html_path = output_dir / HTML_FILENAME
    html_path.write_text(render_cv_html(cv_content, active_options), encoding="utf-8")
    return html_path


def render_validation_errors(cv_content: dict[str, Any], options: RenderOptions, limits: RenderLimits | None = None) -> list[str]:
    errors: list[str] = []
    if options.page_mode == ONE_PAGE_MODE:
        errors.extend(validate_render_limits(cv_content, limits))
    if options.template_path:
        errors.extend(validate_template_html(options.template_path.read_text(encoding="utf-8")))
    return errors


def write_render_report(output_dir: Path, errors: list[str], options: RenderOptions | None = None) -> None:
    report = build_render_report(errors, options or RenderOptions())
    (output_dir / RENDER_REPORT_FILENAME).write_text(report, encoding="utf-8")


def build_render_report(errors: list[str], options: RenderOptions | None = None) -> str:
    active_options = options or RenderOptions()
    if not errors:
        return f"# Render Report\n\nPage mode: {active_options.page_mode}\n\nNo render issues found.\n"
    lines = ["# Render Report", "", f"Page mode: {active_options.page_mode}", "", "The HTML was rendered, but validation found issues.", ""]
    lines.extend(f"- {error}" for error in errors)
    return "\n".join(lines) + "\n"


def render_cv_html(content: dict[str, Any], options: RenderOptions | None = None) -> str:
    active_options = options or RenderOptions()
    template_html = load_template_html(active_options.template_path)
    return render_template_cv_html(template_html, content, active_options)


def load_template_html(template_path: Path | None) -> str:
    if template_path and template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return default_template_html()


def default_template_html() -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{{{title}}}}</title>
  <style>{stylesheet()}</style>
</head>
<body>
  <main class="page {{{{page_class}}}}">
    <header class="top">
      <h1>{{{{name}}}}</h1>
    </header>
    <section class="layout">
      <aside class="sidebar">
        {{{{contact}}}}
        {{{{education}}}}
        {{{{skills}}}}
      </aside>
      <section class="main">
        {{{{profile}}}}
        {{{{work_experience}}}}
        {{{{projects}}}}
        {{{{additional_experience}}}}
      </section>
    </section>
  </main>
</body>
</html>
"""


def render_template_cv_html(template_html: str, content: dict[str, Any], options: RenderOptions) -> str:
    replacements = build_template_replacements(content, options, custom_template=options.template_path is not None)
    html = template_html
    for name, value in replacements.items():
        html = replace_placeholder(html, name, value)
    return apply_print_normalization(html)


def apply_print_normalization(html: str) -> str:
    if PRINT_NORMALIZATION_MARKER in html:
        return html
    style = f"<style id=\"{PRINT_NORMALIZATION_MARKER}\">{print_normalization_stylesheet()}</style>"
    if "</head>" in html:
        return html.replace("</head>", f"{style}\n</head>", 1)
    return style + html


def print_normalization_stylesheet() -> str:
    return """
@media print {
  .section,
  .experience-section,
  .work-section,
  .work-list {
    break-inside: auto !important;
    page-break-inside: auto !important;
  }

  .experience-section,
  .work-section {
    break-before: auto !important;
    page-break-before: auto !important;
  }

  .experience-section .entry,
  .work-section .entry,
  .work-list .entry {
    break-inside: auto !important;
    page-break-inside: auto !important;
  }

  .section-title,
  h2,
  h3 {
    break-after: avoid !important;
    page-break-after: avoid !important;
  }
}
"""


def build_template_replacements(content: dict[str, Any], options: RenderOptions, custom_template: bool = False) -> dict[str, str]:
    name = candidate_name(content)
    if custom_template:
        contact = render_contact_body(content.get("contact"))
        education = render_education_body(content.get("education"))
        skills = render_skills_body(content.get("skills"))
        profile = render_profile_body(content.get("profile"))
        work_experience = render_work_body(content.get("work_experience"))
        projects = render_projects_body(content.get("projects"))
        additional_experience = render_additional_body(content.get("additional_experience"))
    else:
        contact = render_contact(content.get("contact"))
        education = render_education(content.get("education"))
        skills = render_skills(content.get("skills"))
        profile = render_profile(content.get("profile"))
        work_experience = render_work_experience(content.get("work_experience"))
        projects = render_projects(content.get("projects"))
        additional_experience = render_additional_experience(content.get("additional_experience"))
    return {
        "title": f"{name} CV",
        "name": escape(name),
        "contact": contact,
        "education": education,
        "skills": skills,
        "profile": profile,
        "work_experience": work_experience,
        "projects": projects,
        "additional_experience": additional_experience,
        "page_class": escape(page_mode_classes(options.page_mode)),
    }


def page_mode_classes(page_mode: str) -> str:
    if page_mode == ONE_PAGE_MODE:
        return "one_page one-page"
    return page_mode.replace("_", "-")


def candidate_name(content: dict[str, Any]) -> str:
    contact = dict_value(content.get("contact"))
    name = str(contact.get("name", "")).strip()
    return name or DEFAULT_NAME


def replace_placeholder(html: str, name: str, value: str) -> str:
    return re.sub(r"{{\s*" + re.escape(name) + r"\s*}}", value, html)


def validate_template_html(template_html: str) -> list[str]:
    placeholders = set(find_template_placeholders(template_html))
    errors: list[str] = []
    missing = sorted(REQUIRED_TEMPLATE_PLACEHOLDERS - placeholders)
    if missing:
        errors.append("template is missing placeholders: " + ", ".join(f"{{{{{name}}}}}" for name in missing))
    unknown = sorted(placeholders - KNOWN_TEMPLATE_PLACEHOLDERS)
    if unknown:
        errors.append("template contains unknown placeholders: " + ", ".join(f"{{{{{name}}}}}" for name in unknown))
    return errors


def find_template_placeholders(template_html: str) -> list[str]:
    return [match.strip() for match in re.findall(r"{{\s*([a-zA-Z0-9_]+)\s*}}", template_html)]


def find_unresolved_template_tokens(html: str) -> list[str]:
    return re.findall(r"{{\s*[a-zA-Z0-9_]+\s*}}", html)


def render_contact(contact: object) -> str:
    return render_sidebar_section("Contact", render_contact_body(contact))


def render_contact_body(contact: object) -> str:
    data = dict_value(contact)
    rows = [
        contact_link("email", "Email", data.get("email", ""), f"mailto:{data.get('email', '')}"),
        contact_link("phone", "Phone", data.get("phone", ""), f"tel:{data.get('phone', '')}"),
        contact_link("linkedin", "LinkedIn", "LinkedIn", data.get("linkedin", "")),
        contact_link("website", "Website", "Website", data.get("website", "")),
        contact_link("github", "GitHub", "GitHub", data.get("github", "")),
        contact_text("location", "Location", data.get("location", "")),
    ]
    return "".join(row for row in rows if row)


def contact_link(kind: str, label: str, text: object, href: object) -> str:
    href_text = str(href).strip()
    display_text = str(text).strip()
    if not href_text or not display_text:
        return ""
    return f"""<a class="contact-row" data-kind="{escape(kind)}" href="{escape(href_text)}" aria-label="{escape(label)}">
  <span class="contact-icon">{contact_icon(kind)}</span>
  <span class="contact-text">{escape(display_text)}</span>
</a>"""


def contact_text(kind: str, label: str, text: object) -> str:
    display_text = str(text).strip()
    if not display_text:
        return ""
    return f"""<div class="contact-row" data-kind="{escape(kind)}" aria-label="{escape(label)}">
  <span class="contact-icon">{contact_icon(kind)}</span>
  <span class="contact-text">{escape(display_text)}</span>
</div>"""


def contact_icon(kind: str) -> str:
    icons = {
        "email": "✉",
        "phone": "☎",
        "linkedin": linkedin_svg(),
        "website": website_svg(),
        "github": github_svg(),
        "location": "⌂",
    }
    return icons.get(kind, "•")


def linkedin_svg() -> str:
    return """<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
  <path d="M4.98 3.5C4.98 4.88 3.86 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1s2.48 1.12 2.48 2.5zM.4 8h4.2v14H.4V8zm7.6 0h4v1.9h.1c.6-1.1 2-2.2 4.1-2.2 4.4 0 5.2 2.9 5.2 6.7V22h-4.2v-6.8c0-1.6 0-3.7-2.3-3.7s-2.6 1.8-2.6 3.6V22H8V8z"/>
</svg>"""


def github_svg() -> str:
    return """<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
  <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.1 3.3 9.4 7.9 10.9.6.1.8-.25.8-.57v-2.2c-3.2.7-3.9-1.35-3.9-1.35-.53-1.34-1.3-1.7-1.3-1.7-1.05-.72.08-.7.08-.7 1.17.08 1.78 1.2 1.78 1.2 1.04 1.78 2.73 1.27 3.4.97.1-.75.4-1.27.73-1.56-2.56-.3-5.26-1.28-5.26-5.7 0-1.26.45-2.3 1.2-3.1-.12-.3-.52-1.52.12-3.06 0 0 .98-.31 3.2 1.18.93-.26 1.93-.39 2.93-.4 1 .01 2 .14 2.93.4 2.22-1.49 3.2-1.18 3.2-1.18.64 1.54.24 2.76.12 3.06.75.8 1.2 1.84 1.2 3.1 0 4.43-2.7 5.4-5.27 5.69.42.36.78 1.06.78 2.15v3.2c0 .32.2.68.8.57 4.6-1.5 7.9-5.8 7.9-10.9C23.5 5.65 18.35.5 12 .5z"/>
</svg>"""


def website_svg() -> str:
    return """<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
  <path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm6.93 6h-3.02a15.6 15.6 0 0 0-1.35-3.18A8.04 8.04 0 0 1 18.93 8zM12 4.04c.73 1.05 1.33 2.4 1.72 3.96h-3.44C10.67 6.44 11.27 5.09 12 4.04zM4.26 14a8.2 8.2 0 0 1 0-4h3.42A17.22 17.22 0 0 0 7.56 12c0 .69.04 1.36.12 2H4.26zm.81 2h3.02c.33 1.2.78 2.28 1.35 3.18A8.04 8.04 0 0 1 5.07 16zm3.02-8H5.07a8.04 8.04 0 0 1 4.37-3.18A15.6 15.6 0 0 0 8.09 8zM12 19.96c-.73-1.05-1.33-2.4-1.72-3.96h3.44c-.39 1.56-.99 2.91-1.72 3.96zM14.15 14h-4.3a14.94 14.94 0 0 1 0-4h4.3a14.94 14.94 0 0 1 0 4zm.41 5.18c.57-.9 1.02-1.98 1.35-3.18h3.02a8.04 8.04 0 0 1-4.37 3.18zM16.32 14c.08-.64.12-1.31.12-2s-.04-1.36-.12-2h3.42a8.2 8.2 0 0 1 0 4h-3.42z"/>
</svg>"""


def render_education(education: object) -> str:
    return render_sidebar_section("Education", render_education_body(education))


def render_education_body(education: object) -> str:
    entries = list_value(education)
    return "".join(render_education_entry(entry) for entry in entries)


def render_education_entry(entry: object) -> str:
    data = dict_value(entry)
    lines = [
        f'<p class="item-title">{escape(data.get("institution", ""))}</p>',
        f'<p class="item-strong">{escape(data.get("degree", ""))}</p>',
        f'<p>{escape(data.get("classification", ""))}</p>',
        f'<p>{escape(data.get("dates", ""))}</p>',
    ]
    return "".join(line for line in lines if not line.endswith("></p>"))


def render_skills(skills: object) -> str:
    return render_sidebar_section("Skills", render_skills_body(skills))


def render_skills_body(skills: object) -> str:
    return "".join(render_skill(skill) for skill in list_value(skills)[:6])


def render_skill(skill: object) -> str:
    data = normalise_skill(skill)
    category = escape(data.get("category", "other"))
    return f'<span class="skill" data-category="{category}">{escape(data.get("name", ""))}</span>'


def normalise_skill(skill: object) -> dict[str, str]:
    if isinstance(skill, str):
        return {"name": skill, "category": "other"}
    data = dict_value(skill)
    return {"name": str(data.get("name", "")), "category": str(data.get("category", "other"))}


def render_profile(profile: object) -> str:
    return render_main_section("Profile", render_profile_body(profile))


def render_profile_body(profile: object) -> str:
    data = dict_value(profile)
    content = data.get("content", "")
    return f'<p class="profile-text">{escape(str(content))}</p>' if str(content).strip() else ""


def render_work_experience(items: object) -> str:
    return render_main_section("Work Experience", render_work_body(items))


def render_work_body(items: object) -> str:
    return "".join(render_work_item(item) for item in list_value(items))


def render_work_item(item: object) -> str:
    data = dict_value(item)
    heading = render_role_heading(data)
    bullets = render_bullets(data.get("bullets"), limit=4)
    return f'<article class="entry">{heading}{bullets}</article>'


def render_role_heading(data: dict[str, Any]) -> str:
    title = escape(str(data.get("title", "")))
    company = escape(str(data.get("company", "")))
    dates = escape(display_role_dates(str(data.get("dates", ""))))
    return f'<h3>{title}</h3><p class="subhead">{company} · {dates}</p>'


def display_role_dates(dates: str) -> str:
    if dates in {"2025-06-25 to Present", "25 June 2025 to Present"}:
        return "June 2025 - Present"
    return dates


def render_projects(projects: object) -> str:
    return render_main_section("Projects", render_projects_body(projects))


def render_projects_body(projects: object) -> str:
    return "".join(render_project(project) for project in list_value(projects)[:4])


def render_project(project: object) -> str:
    data = dict_value(project)
    name = escape(str(data.get("name", "")))
    bullets = render_bullets(data.get("bullets"), limit=2)
    return f'<article class="entry"><h3>{name}</h3>{bullets}</article>'


def render_additional_experience(items: object) -> str:
    return render_main_section("Additional Experience", render_additional_body(items))


def render_additional_body(items: object) -> str:
    return render_bullets(items, limit=3)


def render_bullets(items: object, limit: int) -> str:
    bullets = [render_bullet(item) for item in list_value(items)[:limit]]
    return f'<ul>{"".join(bullets)}</ul>' if bullets else ""


def render_bullet(item: object) -> str:
    data = dict_value(item)
    return f'<li>{escape(str(data.get("text", "")))}</li>'


def render_sidebar_section(title: str, body: str) -> str:
    return f'<section class="side-section"><h2>{escape(title)}</h2>{body}</section>' if body else ""


def render_main_section(title: str, body: str) -> str:
    return f'<section class="main-section"><h2>{escape(title)}</h2>{body}</section>' if body else ""


def dict_value(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def list_value(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def stylesheet() -> str:
    return """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #f4f4f4;
  color: #595959;
  font-family: Arial, Helvetica, sans-serif;
  font-size: 10.5pt;
  line-height: 1.28;
}
.page {
  width: 210mm;
  min-height: 297mm;
  margin: 0 auto;
  background: #fff;
  padding: 16mm 15mm 12mm;
}
.page.one_page {
  height: 297mm;
  overflow: hidden;
}
.top {
  border-bottom: 1px solid #555;
  margin-bottom: 4mm;
  padding-bottom: 4mm;
  text-align: center;
}
.top h1 {
  margin: 0;
  color: #565656;
  font-size: 30pt;
  font-weight: 400;
  letter-spacing: 0.28em;
  text-transform: uppercase;
}
.layout {
  display: grid;
  grid-template-columns: 83mm 1fr;
  gap: 9mm;
}
.sidebar {
  background: linear-gradient(90deg, #f7f7f7 0 11mm, #fff 11mm 100%);
  padding: 3mm 0 0 2mm;
}
h2 {
  margin: 0 0 2.8mm;
  color: #666;
  font-size: 14pt;
  font-weight: 600;
  letter-spacing: 0.28em;
  text-transform: uppercase;
}
.side-section {
  border-bottom: 1px dashed #666;
  margin-bottom: 5mm;
  padding: 0 0 4mm 1mm;
}
.side-section:last-child { border-bottom: 0; }
.side-section p,
.main-section p {
  margin: 0 0 1.4mm;
}
.profile-text {
  font-size: 9.2pt;
  line-height: 1.15;
}
.item-title {
  font-weight: 700;
}
.item-strong {
  font-weight: 700;
}
.contact-row {
  display: grid;
  grid-template-columns: 5mm 1fr;
  gap: 2mm;
  align-items: center;
  min-height: 5mm;
  margin-bottom: 1.4mm;
  color: #595959;
  text-decoration: none;
  overflow-wrap: anywhere;
}
.contact-icon {
  display: inline-flex;
  width: 4.8mm;
  height: 4.8mm;
  align-items: center;
  justify-content: center;
  border: 1px solid #777;
  border-radius: 50%;
  color: #555;
  font-size: 7pt;
  font-weight: 700;
  line-height: 1;
}
.contact-icon svg {
  width: 3.4mm;
  height: 3.4mm;
  display: block;
  fill: currentColor;
}
.contact-row[data-kind="linkedin"] .contact-icon {
  border-color: #2475a8;
  background: #2475a8;
  color: #fff;
  font-family: Arial, Helvetica, sans-serif;
}
.contact-row[data-kind="github"] .contact-icon {
  font-size: 7pt;
}
.contact-text {
  min-width: 0;
  font-size: 8.8pt;
}
.skill {
  display: inline-block;
  margin: 0 1.5mm 1.2mm 0;
  font-size: 9pt;
}
.client-item {
  margin-bottom: 2.6mm;
}
.main-section {
  border-bottom: 1px dashed #666;
  margin-bottom: 3mm;
  padding-bottom: 2.4mm;
}
.main-section:last-child { border-bottom: 0; }
.entry {
  margin-bottom: 2.8mm;
}
.entry h3 {
  margin: 0 0 1mm;
  color: #555;
  font-size: 11pt;
  font-weight: 700;
}
.subhead {
  font-style: italic;
}
ul {
  margin: 1.4mm 0 0 4mm;
  padding-left: 3.5mm;
}
li {
  font-size: 9.4pt;
  line-height: 1.18;
  margin-bottom: 0.8mm;
}
@media print {
  html,
  body {
    width: 210mm;
    background: #fff;
  }
  .page {
    margin: 0;
  }
  .page.one_page {
    height: 297mm;
    overflow: hidden;
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .top {
    break-after: avoid;
    page-break-after: avoid;
  }
  .layout {
    break-before: avoid;
    page-break-before: avoid;
  }
}
"""
