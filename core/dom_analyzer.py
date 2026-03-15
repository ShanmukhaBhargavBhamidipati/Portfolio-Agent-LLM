import re
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from core.inspiration import (
    ImageSummary,
    InspirationSummary,
    InteractionEvidence,
    SectionSummary,
)

SECTION_KEYWORDS = [
    "hero", "home", "about", "experience", "projects", "skills",
    "certifications", "education", "contact", "footer", "services",
    "portfolio", "testimonials", "blog", "resume", "work", "career"
]


def clean_text(text: Optional[str]) -> str:
    if not text:
        return ""
    return " ".join(text.split()).strip()


def short_text(text: Optional[str], limit: int = 220) -> str:
    text = clean_text(text)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def fetch_html(url: str, timeout: int = 20) -> Tuple[str, str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; PortfolioInspirationBot/2.0)"
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text, str(resp.url)


def detect_title(soup: BeautifulSoup) -> Optional[str]:
    return soup.title.get_text(strip=True) if soup.title else None


def detect_meta_description(soup: BeautifulSoup) -> Optional[str]:
    tag = soup.find("meta", attrs={"name": "description"})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return None


def classify_section_from_tokens(tag: str, identifier: str, heading_texts: List[str], text_sample: str) -> str:
    blob = " ".join([tag, identifier, " ".join(heading_texts), text_sample]).lower()
    for keyword in SECTION_KEYWORDS:
        if keyword in blob:
            return keyword
    if tag == "footer":
        return "footer"
    if tag == "header":
        return "hero"
    if "form" in blob:
        return "contact"
    return "generic-section"


def infer_role_for_image(img: Dict[str, Any], section_kind: str) -> str:
    alt = (img.get("alt") or "").lower()
    src = (img.get("src") or "").lower()

    if any(x in alt for x in ["profile", "portrait", "headshot", "avatar"]):
        return "Likely a profile or portrait image."
    if any(x in alt for x in ["certificate", "badge", "certification"]):
        return "Likely a certification or badge image."
    if any(x in alt for x in ["project", "dashboard", "preview", "screenshot"]):
        return "Likely a project preview image."
    if "logo" in alt or "logo" in src:
        return "Likely a brand or logo image."
    if section_kind in ["hero", "home"]:
        return "Likely a prominent top-of-page visual."
    if section_kind in ["projects", "portfolio"]:
        return "Likely used to visually support a project entry."
    return "Likely a supporting visual element."


def rendered_page_snapshot(url: str) -> Dict[str, Any]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 2200})
        page.goto(url, wait_until="networkidle", timeout=30000)

        data = page.evaluate(
            """
            () => {
              function pickSections() {
                const els = Array.from(document.querySelectorAll('header, nav, main, section, footer, aside'));
                if (els.length) return els;
                return Array.from(document.body.children);
              }

              function visible(el) {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return style.display !== 'none' &&
                       style.visibility !== 'hidden' &&
                       rect.width > 0 &&
                       rect.height > 0;
              }

              function toObj(rect) {
                return {
                  x: rect.x, y: rect.y, width: rect.width, height: rect.height,
                  top: rect.top, left: rect.left, right: rect.right, bottom: rect.bottom
                };
              }

              function summarizeSection(el, index) {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                const headings = Array.from(el.querySelectorAll('h1,h2,h3')).slice(0, 4)
                  .map(h => h.textContent.trim()).filter(Boolean);

                const paras = Array.from(el.querySelectorAll('p')).slice(0, 3)
                  .map(p => p.textContent.trim()).filter(Boolean);

                const images = Array.from(el.querySelectorAll('img')).slice(0, 8).map(img => {
                  const r = img.getBoundingClientRect();
                  const s = window.getComputedStyle(img);
                  return {
                    src: img.getAttribute('src'),
                    alt: img.getAttribute('alt'),
                    bbox: toObj(r),
                    objectFit: s.objectFit,
                    width: r.width,
                    height: r.height
                  };
                });

                const links = el.querySelectorAll('a').length;
                const buttons = el.querySelectorAll('button').length;
                const forms = el.querySelectorAll('form').length;
                const articles = el.querySelectorAll('article').length;
                const cards = el.querySelectorAll('[class*="card" i]').length;

                return {
                  index,
                  tag: el.tagName.toLowerCase(),
                  id: el.id || '',
                  className: el.className || '',
                  ariaLabel: el.getAttribute('aria-label') || '',
                  textSample: (paras.join(' | ') || el.textContent || '').trim().slice(0, 500),
                  headings,
                  bbox: toObj(rect),
                  computed: {
                    display: style.display,
                    position: style.position,
                    flexDirection: style.flexDirection,
                    justifyContent: style.justifyContent,
                    alignItems: style.alignItems,
                    gridTemplateColumns: style.gridTemplateColumns,
                    gridTemplateRows: style.gridTemplateRows,
                    gap: style.gap,
                    margin: style.margin,
                    padding: style.padding,
                    backgroundColor: style.backgroundColor,
                    color: style.color,
                    border: style.border,
                    borderRadius: style.borderRadius,
                    boxShadow: style.boxShadow,
                    fontSize: style.fontSize,
                    fontWeight: style.fontWeight,
                    maxWidth: style.maxWidth,
                    textAlign: style.textAlign,
                    opacity: style.opacity
                  },
                  counts: {
                    links,
                    buttons,
                    forms,
                    articles,
                    cards,
                    images: images.length
                  },
                  images
                };
              }

              const sections = pickSections().filter(visible).map(summarizeSection);

              const scripts = Array.from(document.scripts).map((s, i) => ({
                index: i,
                src: s.src || null,
                text: s.textContent ? s.textContent.slice(0, 50000) : ''
              }));

              const pageInfo = {
                bodyClass: document.body.className || '',
                title: document.title || '',
                viewport: {
                  width: window.innerWidth,
                  height: window.innerHeight
                },
                allImages: Array.from(document.querySelectorAll('img')).map(img => {
                  const r = img.getBoundingClientRect();
                  return {
                    src: img.getAttribute('src'),
                    alt: img.getAttribute('alt'),
                    bbox: toObj(r)
                  };
                })
              };

              return { sections, scripts, pageInfo };
            }
            """
        )

        browser.close()
        return data


def describe_layout(computed: Dict[str, Any], bbox: Dict[str, Any]) -> List[str]:
    facts = []
    display = computed.get("display", "")
    grid_cols = computed.get("gridTemplateColumns", "")
    flex_dir = computed.get("flexDirection", "")
    gap = computed.get("gap", "")
    padding = computed.get("padding", "")
    max_width = computed.get("maxWidth", "")
    text_align = computed.get("textAlign", "")

    if display == "grid":
        facts.append(f"The section uses CSS grid with columns defined as: {grid_cols}.")
    elif display == "flex":
        facts.append(f"The section uses flex layout with direction {flex_dir} and alignment {computed.get('justifyContent')} / {computed.get('alignItems')}.")
    else:
        facts.append(f"The section uses {display} layout.")

    if gap and gap != "normal":
        facts.append(f"Spacing between child elements uses a gap of {gap}.")
    if padding and padding != "0px":
        facts.append(f"Internal spacing is provided by padding {padding}.")
    if max_width and max_width not in ("none", "0px"):
        facts.append(f"The section content appears constrained by max-width {max_width}.")
    if text_align and text_align != "start":
        facts.append(f"Text alignment is {text_align}.")
    if bbox.get("width") and bbox.get("height"):
        facts.append(f"Rendered size is approximately {round(bbox['width'])}×{round(bbox['height'])} pixels.")

    return facts


def describe_style(computed: Dict[str, Any]) -> List[str]:
    facts = []
    bg = computed.get("backgroundColor", "")
    color = computed.get("color", "")
    radius = computed.get("borderRadius", "")
    shadow = computed.get("boxShadow", "")
    border = computed.get("border", "")
    font_size = computed.get("fontSize", "")
    font_weight = computed.get("fontWeight", "")
    opacity = computed.get("opacity", "")

    if bg and bg != "rgba(0, 0, 0, 0)":
        facts.append(f"The section has a visible background color of {bg}.")
    else:
        facts.append("The section background appears transparent or inherited.")

    if color:
        facts.append(f"Primary text color computes to {color}.")
    if radius and radius != "0px":
        facts.append(f"Corners are rounded with border-radius {radius}.")
    if shadow and shadow != "none":
        facts.append(f"A visible shadow is applied: {shadow}.")
    if border and border != "0px none rgb(0, 0, 0)":
        facts.append(f"The section uses a border style of {border}.")
    if font_size:
        facts.append(f"Base computed font size is {font_size}.")
    if font_weight:
        facts.append(f"Base computed font weight is {font_weight}.")
    if opacity and opacity != "1":
        facts.append(f"The section is rendered with opacity {opacity}.")

    return facts


def describe_components(counts: Dict[str, Any]) -> List[str]:
    facts = []
    if counts.get("links"):
        facts.append(f"The section contains {counts['links']} link element(s).")
    if counts.get("buttons"):
        facts.append(f"The section contains {counts['buttons']} button element(s).")
    if counts.get("forms"):
        facts.append(f"The section contains {counts['forms']} form element(s).")
    if counts.get("articles"):
        facts.append(f"The section contains {counts['articles']} article-like content block(s).")
    if counts.get("cards"):
        facts.append(f"The section contains {counts['cards']} element(s) whose classes suggest card-style grouping.")
    return facts


def describe_images(section_images: List[Dict[str, Any]], section_kind: str) -> List[str]:
    facts = []
    if not section_images:
        facts.append("No standard image elements were detected in this section.")
        return facts

    facts.append(f"The section contains {len(section_images)} image element(s).")
    for img in section_images[:4]:
        role = infer_role_for_image(img, section_kind)
        alt = clean_text(img.get("alt") or "No alt text")
        bbox = img.get("bbox", {})
        facts.append(
            f"{role} Alt/context: {alt}. "
            f"Rendered image size is approximately {round(bbox.get('width', 0))}×{round(bbox.get('height', 0))} pixels."
        )
    return facts


def detect_interactions_from_scripts(scripts: List[Dict[str, Any]], soup: BeautifulSoup) -> List[InteractionEvidence]:
    joined = "\n".join((s.get("text") or "") for s in scripts)

    evidence: List[InteractionEvidence] = []

    def add(behavior: str, confidence: str, ev: List[str]):
        evidence.append(InteractionEvidence(behavior=behavior, confidence=confidence, evidence=ev))

    if "window.print(" in joined:
        add(
            "print action",
            "high",
            ["Detected explicit call to window.print()."]
        )

    if "IntersectionObserver" in joined:
        nav_present = bool(soup.select("nav a[href^='#']"))
        ev = ["Detected use of IntersectionObserver."]
        if nav_present:
            ev.append("Page includes anchor-style navigation links.")
            add("active section highlighting or scroll-aware navigation", "high", ev)
        else:
            add("viewport-aware interaction", "medium", ev)

    if "classList.toggle('dark'" in joined or 'classList.toggle("dark"' in joined:
        add(
            "theme toggle",
            "high",
            ["Detected classList.toggle('dark')."]
        )
    elif "theme" in joined.lower() and "addEventListener" in joined:
        add(
            "theme-related interaction",
            "medium",
            ["Found theme-related code with event listeners."]
        )

    if re.search(r"addEventListener\s*\(\s*['\"]click['\"]", joined):
        add(
            "click-driven interaction",
            "high",
            ["Detected one or more click event listeners."]
        )

    if re.search(r"addEventListener\s*\(\s*['\"]submit['\"]", joined) or "onsubmit" in joined:
        add(
            "form submission handling",
            "high",
            ["Detected submit handler or onsubmit usage."]
        )

    if "localStorage" in joined:
        add(
            "persistent UI state",
            "high",
            ["Detected localStorage usage."]
        )

    if "scrollIntoView" in joined:
        add(
            "programmatic scrolling",
            "high",
            ["Detected scrollIntoView usage."]
        )

    if re.search(r"classList\.toggle\s*\(", joined) and "dark" not in joined:
        add(
            "visibility/state toggling",
            "medium",
            ["Detected generic classList.toggle() usage."]
        )

    return evidence


def map_interactions_to_section(section: Dict[str, Any], interactions: List[InteractionEvidence]) -> List[str]:
    section_blob = " ".join(
        [
            section.get("tag", ""),
            section.get("id", ""),
            section.get("className", ""),
            section.get("ariaLabel", ""),
            " ".join(section.get("headings", [])),
        ]
    ).lower()

    facts = []

    for item in interactions:
        behavior = item.behavior
        if behavior == "theme toggle" and "theme" in section_blob:
            facts.append("This section includes high-confidence evidence of a theme toggle control.")
        elif behavior == "print action" and ("print" in section_blob or "button" in section_blob):
            facts.append("This section likely contains or relates to a print action.")
        elif behavior == "active section highlighting or scroll-aware navigation" and ("nav" in section_blob or "navigation" in section_blob):
            facts.append("This section is likely involved in scroll-aware navigation highlighting.")
        elif behavior == "form submission handling" and ("contact" in section_blob or "form" in section_blob):
            facts.append("This section likely includes interactive form handling.")

    return facts


def build_section_narrative(section: SectionSummary) -> str:
    lines = [
        f"Section {section.index}: {section.inferred_kind.replace('-', ' ').title()}."
    ]

    if section.heading_texts:
        lines.append(f"Visible headings include: {', '.join(section.heading_texts[:3])}.")
    if section.text_sample:
        lines.append(f"Text sample: {section.text_sample}.")

    lines.extend(section.layout_facts[:3])
    lines.extend(section.style_facts[:4])
    lines.extend(section.component_facts[:4])
    lines.extend(section.image_facts[:4])
    lines.extend(section.interaction_facts[:3])

    return " ".join(lines)


def build_page_overview(sections: List[SectionSummary]) -> List[str]:
    if not sections:
        return ["The page structure could not be resolved into visible sections."]

    overview = ["The page appears to be organized as a vertically structured web page composed of visible top-to-bottom sections."]

    first_kind = sections[0].inferred_kind
    if first_kind in ("hero", "home"):
        overview.append("The opening section behaves like a hero/header area, setting the first visual impression.")
    if any(s.inferred_kind == "about" for s in sections):
        overview.append("An about-oriented section explains the person, brand, or purpose of the site.")
    if any(s.inferred_kind in ("projects", "portfolio") for s in sections):
        overview.append("A project-focused section showcases work using repeated content blocks.")
    if any(s.inferred_kind == "skills" for s in sections):
        overview.append("A skills-oriented section groups capabilities or technologies.")
    if any(s.inferred_kind == "contact" for s in sections):
        overview.append("A contact-oriented section likely appears toward the end of the page.")
    if any(s.inferred_kind == "footer" for s in sections):
        overview.append("The page closes with a footer-like ending section.")

    return overview


def build_overall_impression(summary: InspirationSummary) -> List[str]:
    notes = []

    if any("shadow" in x.lower() for x in summary.global_style_facts):
        notes.append("The design uses depth cues such as shadows, which makes surfaces feel more card-like or layered.")
    if any("rounded" in x.lower() for x in summary.global_style_facts):
        notes.append("Rounded corners contribute to a softer, modern UI style.")
    if any(i.behavior == "theme toggle" and i.confidence == "high" for i in summary.interaction_evidence):
        notes.append("The page includes a confirmed theme-toggle interaction, suggesting an interactive rather than purely static experience.")
    if any(s.images for s in summary.sections if hasattr(s, "images")):
        notes.append("The page includes meaningful imagery rather than being purely text-driven.")
    if not notes:
        notes.append("The page appears professionally structured with clearly separated content sections.")

    return notes


def build_long_visual_summary(summary: InspirationSummary) -> str:
    parts = []

    if summary.title:
        parts.append(f"Page title: {summary.title}.")
    if summary.meta_description:
        parts.append(f"Meta description: {summary.meta_description}")

    parts.extend(summary.page_overview)

    if summary.global_style_facts:
        parts.append("Global styling observations: " + " ".join(summary.global_style_facts))

    if summary.interaction_evidence:
        interaction_lines = []
        for item in summary.interaction_evidence:
            interaction_lines.append(
                f"{item.behavior} ({item.confidence} confidence): {' '.join(item.evidence)}"
            )
        parts.append("Interaction evidence: " + " ".join(interaction_lines))

    if summary.sections:
        parts.append("Section-by-section walkthrough:")
        parts.extend(s.narrative for s in summary.sections)

    if summary.images:
        image_lines = []
        for img in summary.images[:10]:
            image_lines.append(
                f"Section {img.section_index} ({img.section_kind}): {img.inferred_role} "
                f"Alt/context: {img.alt or 'No alt text'}."
            )
        parts.append("Image placement summary: " + " ".join(image_lines))

    if summary.overall_impression:
        parts.append("Overall impression: " + " ".join(summary.overall_impression))

    return "\n\n".join(parts)


def analyze_html(url: str) -> InspirationSummary:
    html, final_url = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    rendered = rendered_page_snapshot(final_url)

    sections_raw = rendered.get("sections", [])
    scripts = rendered.get("scripts", [])

    interaction_evidence = detect_interactions_from_scripts(scripts, soup)

    section_summaries: List[SectionSummary] = []
    image_summaries: List[ImageSummary] = []

    for raw in sections_raw[:20]:
        identifier_parts = [raw.get("id", ""), raw.get("className", ""), raw.get("ariaLabel", "")]
        identifier = clean_text(" ".join(x for x in identifier_parts if x))
        heading_texts = [clean_text(x) for x in raw.get("headings", []) if clean_text(x)]
        text_sample = short_text(raw.get("textSample", ""), 220)

        inferred_kind = classify_section_from_tokens(
            raw.get("tag", ""),
            identifier,
            heading_texts,
            text_sample,
        )

        layout_facts = describe_layout(raw.get("computed", {}), raw.get("bbox", {}))
        style_facts = describe_style(raw.get("computed", {}))
        component_facts = describe_components(raw.get("counts", {}))
        image_facts = describe_images(raw.get("images", []), inferred_kind)
        interaction_facts = map_interactions_to_section(raw, interaction_evidence)

        section = SectionSummary(
            index=raw["index"],
            tag=raw.get("tag", ""),
            identifier=identifier,
            inferred_kind=inferred_kind,
            heading_texts=heading_texts,
            text_sample=text_sample,
            bbox=raw.get("bbox", {}),
            layout_facts=layout_facts,
            style_facts=style_facts,
            image_facts=image_facts,
            component_facts=component_facts,
            interaction_facts=interaction_facts,
        )
        section.narrative = build_section_narrative(section)
        section_summaries.append(section)

        for img in raw.get("images", []):
            image_summaries.append(
                ImageSummary(
                    src=img.get("src"),
                    alt=img.get("alt"),
                    section_index=raw["index"],
                    section_kind=inferred_kind,
                    bbox=img.get("bbox", {}),
                    inferred_role=infer_role_for_image(img, inferred_kind),
                )
            )

    global_style_facts: List[str] = []

    body_class = (rendered.get("pageInfo", {}) or {}).get("bodyClass", "")
    if "dark" in body_class.lower():
        global_style_facts.append("The rendered page body currently includes a dark-related class.")
    if soup.find("meta", attrs={"name": "viewport"}):
        global_style_facts.append("The page includes a viewport meta tag, indicating responsive intent.")

    all_css_text = " ".join(style.get_text(" ", strip=True) for style in soup.find_all("style"))
    css_blob = (html + " " + all_css_text).lower()

    if "box-shadow" in css_blob:
        global_style_facts.append("CSS includes shadow styling.")
    if "border-radius" in css_blob:
        global_style_facts.append("CSS includes rounded-corner styling.")
    if "grid-template-columns" in css_blob or "display:grid" in css_blob or "display: grid" in css_blob:
        global_style_facts.append("CSS includes grid-based layout rules.")
    if "display:flex" in css_blob or "display: flex" in css_blob:
        global_style_facts.append("CSS includes flex-based layout rules.")
    if "background:linear-gradient" in css_blob or "linear-gradient" in css_blob:
        global_style_facts.append("CSS includes gradient styling.")
    if "scroll-behavior:smooth" in css_blob or "scroll-behavior: smooth" in css_blob:
        global_style_facts.append("CSS includes smooth scrolling behavior.")

    summary = InspirationSummary(
        url=url,
        final_url=final_url,
        title=detect_title(soup),
        meta_description=detect_meta_description(soup),
        page_overview=build_page_overview(section_summaries),
        global_style_facts=global_style_facts,
        interaction_evidence=interaction_evidence,
        section_order=[s.inferred_kind for s in section_summaries],
        sections=section_summaries,
        images=image_summaries,
    )

    summary.overall_impression = build_overall_impression(summary)
    summary.long_visual_summary = build_long_visual_summary(summary)
    return summary