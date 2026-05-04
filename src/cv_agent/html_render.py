from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

from cv_agent.render_limits import RenderLimits, validate_render_limits


HTML_FILENAME = "cv.html"
RENDER_REPORT_FILENAME = "render-report.md"
NAME = "Oscar Alberigo"
FOUR_STAR_NOTE = "4-star skills indicate active development focus."
CLIENT_FACING_EXPERIENCE = [
    {
        "role": "Beach Resort Manager",
        "place": "Macan Beach, Andora, Italy",
        "dates": "May 2024 - October 2024",
    },
    {
        "role": "Tennis Coach",
        "place": "CEM Tenis L'Hospitalet, Barcelona, Spain",
        "dates": "November 2023 - May 2024",
    },
    {
        "role": "Camp Counsellor / Tennis Coach",
        "place": "Camp Lokanda, Glen Spey, NY, USA",
        "dates": "Summer 2022",
    },
]


def render_cv_html_file(cv_content: dict[str, Any], output_dir: Path, limits: RenderLimits | None = None) -> Path:
    errors = validate_render_limits(cv_content, limits)
    write_render_report(output_dir, errors)
    html_path = output_dir / HTML_FILENAME
    html_path.write_text(render_cv_html(cv_content), encoding="utf-8")
    return html_path


def write_render_report(output_dir: Path, errors: list[str]) -> None:
    report = build_render_report(errors)
    (output_dir / RENDER_REPORT_FILENAME).write_text(report, encoding="utf-8")


def build_render_report(errors: list[str]) -> str:
    if not errors:
        return "# Render Report\n\nNo render limit issues found.\n"
    lines = ["# Render Report", "", "The HTML was rendered, but the CV content exceeds the configured one-page limits.", ""]
    lines.extend(f"- {error}" for error in errors)
    return "\n".join(lines) + "\n"


def render_cv_html(content: dict[str, Any]) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(NAME)} CV</title>
  <style>{stylesheet()}</style>
</head>
<body>
  <main class="page">
    <header class="top">
      <h1>{escape(NAME)}</h1>
    </header>
    <section class="layout">
      <aside class="sidebar">
        {render_contact(content.get("contact"))}
        {render_education(content.get("education"))}
        {render_skills(content.get("skills"))}
        {render_client_facing()}
      </aside>
      <section class="main">
        {render_profile(content.get("profile"))}
        {render_work_experience(content.get("work_experience"))}
        {render_projects(content.get("projects"))}
      </section>
    </section>
  </main>
</body>
</html>
"""


def render_contact(contact: object) -> str:
    data = dict_value(contact)
    rows = [
        contact_link("email", "Email", data.get("email", ""), f"mailto:{data.get('email', '')}"),
        contact_link("phone", "Phone", data.get("phone", ""), f"tel:{data.get('phone', '')}"),
        contact_link("linkedin", "LinkedIn", "LinkedIn", data.get("linkedin", "")),
        contact_link("website", "Website", "Website", data.get("website", "")),
        contact_link("github", "GitHub", "GitHub", data.get("github", "")),
    ]
    return render_sidebar_section("Contact", "".join(row for row in rows if row))


def contact_link(kind: str, label: str, text: object, href: object) -> str:
    href_text = str(href).strip()
    display_text = str(text).strip()
    if not href_text or not display_text:
        return ""
    return f"""<a class="contact-row" data-kind="{escape(kind)}" href="{escape(href_text)}" aria-label="{escape(label)}">
  <span class="contact-icon">{contact_icon(kind)}</span>
  <span class="contact-text">{escape(display_text)}</span>
</a>"""


def contact_icon(kind: str) -> str:
    icons = {
        "email": "✉",
        "phone": "☎",
        "linkedin": linkedin_svg(),
        "website": website_svg(),
        "github": github_svg(),
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
    entries = list_value(education)
    body = "".join(render_education_entry(entry) for entry in entries)
    return render_sidebar_section("Education", body)


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
    rows = "".join(render_skill(skill, index) for index, skill in enumerate(list_value(skills)[:6]))
    note = f'<p class="skill-note">{escape(FOUR_STAR_NOTE)}</p>' if rows else ""
    return render_sidebar_section("Skills", rows + note)


def render_skill(skill: object, index: int) -> str:
    data = normalise_skill(skill)
    rating = deterministic_skill_rating(index)
    category = escape(data.get("category", "other"))
    return f"""<div class="skill" data-category="{category}">
  <span>{escape(data.get("name", ""))}</span>
  <span class="stars">{render_stars(rating)}</span>
</div>"""


def normalise_skill(skill: object) -> dict[str, str]:
    if isinstance(skill, str):
        return {"name": skill, "category": "other"}
    data = dict_value(skill)
    return {"name": str(data.get("name", "")), "category": str(data.get("category", "other"))}


def deterministic_skill_rating(index: int) -> int:
    return 5 if index < 4 else 4


def render_stars(rating: int) -> str:
    full = "★" * rating
    empty = "☆" * (5 - rating)
    return escape(full + empty)


def render_client_facing() -> str:
    body = "".join(render_client_facing_item(item) for item in CLIENT_FACING_EXPERIENCE)
    return render_sidebar_section("Client-Facing Experience", body)


def render_client_facing_item(item: object) -> str:
    data = dict_value(item)
    role = str(data.get("role", ""))
    place = str(data.get("place", ""))
    dates = str(data.get("dates", ""))
    return f"""<div class="client-item">
  <p class="item-title">{escape(role)}</p>
  <p>{escape(place)}</p>
  <p>{escape(dates)}</p>
</div>"""


def render_profile(profile: object) -> str:
    data = dict_value(profile)
    content = data.get("content", "")
    return render_main_section("Profile", f'<p class="profile-text">{escape(str(content))}</p>')


def render_work_experience(items: object) -> str:
    body = "".join(render_work_item(item) for item in list_value(items))
    return render_main_section("Work Experience", body)


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
    body = "".join(render_project(project) for project in list_value(projects)[:4])
    return render_main_section("Projects", body)


def render_project(project: object) -> str:
    data = dict_value(project)
    name = escape(str(data.get("name", "")))
    bullets = render_bullets(data.get("bullets"), limit=2)
    return f'<article class="entry"><h3>{name}</h3>{bullets}</article>'


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
  height: 297mm;
  overflow: hidden;
  margin: 0 auto;
  background: #fff;
  padding: 16mm 15mm 12mm;
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
  display: grid;
  grid-template-columns: minmax(0, 1fr) 26mm;
  align-items: baseline;
  gap: 2mm;
  margin-bottom: 1.2mm;
}
.skill span:first-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.stars {
  color: #ffd970;
  font-size: 12.5pt;
  letter-spacing: 0.02em;
  line-height: 1;
}
.skill[data-category="ai"] .stars {
  color: #8fa7ff;
}
.skill-note {
  margin-top: 2mm;
  font-size: 8.6pt;
  font-style: italic;
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
    height: 297mm;
    background: #fff;
    overflow: hidden;
  }
  .page {
    margin: 0;
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
