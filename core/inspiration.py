from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SectionSummary(BaseModel):
    index: int
    tag: str
    identifier: str
    inferred_kind: str

    heading_texts: List[str] = Field(default_factory=list)
    text_sample: Optional[str] = None

    bbox: Dict[str, float] = Field(default_factory=dict)
    layout_facts: List[str] = Field(default_factory=list)
    style_facts: List[str] = Field(default_factory=list)
    image_facts: List[str] = Field(default_factory=list)
    component_facts: List[str] = Field(default_factory=list)
    interaction_facts: List[str] = Field(default_factory=list)

    narrative: str = ""


class InteractionEvidence(BaseModel):
    behavior: str
    confidence: str
    evidence: List[str] = Field(default_factory=list)


class ImageSummary(BaseModel):
    src: Optional[str] = None
    alt: Optional[str] = None
    section_index: Optional[int] = None
    section_kind: Optional[str] = None
    bbox: Dict[str, float] = Field(default_factory=dict)
    inferred_role: Optional[str] = None


class InspirationSummary(BaseModel):
    url: str
    final_url: str
    title: Optional[str] = None
    meta_description: Optional[str] = None

    page_overview: List[str] = Field(default_factory=list)
    global_style_facts: List[str] = Field(default_factory=list)
    interaction_evidence: List[InteractionEvidence] = Field(default_factory=list)

    section_order: List[str] = Field(default_factory=list)
    sections: List[SectionSummary] = Field(default_factory=list)
    images: List[ImageSummary] = Field(default_factory=list)

    overall_impression: List[str] = Field(default_factory=list)
    long_visual_summary: str = ""

    def to_prompt_block(self) -> str:
        lines: List[str] = []

        lines.append(f"Source URL: {self.url}")
        if self.final_url and self.final_url != self.url:
            lines.append(f"Resolved URL: {self.final_url}")
        if self.title:
            lines.append(f"Title: {self.title}")
        if self.meta_description:
            lines.append(f"Meta Description: {self.meta_description}")

        if self.page_overview:
            lines.append("\nPage Overview:")
            for item in self.page_overview:
                lines.append(f"- {item}")

        if self.global_style_facts:
            lines.append("\nGlobal Styling Facts:")
            for item in self.global_style_facts:
                lines.append(f"- {item}")

        if self.interaction_evidence:
            lines.append("\nInteraction Evidence:")
            for item in self.interaction_evidence:
                evidence = "; ".join(item.evidence) if item.evidence else "No evidence recorded"
                lines.append(f"- {item.behavior} ({item.confidence} confidence): {evidence}")

        if self.section_order:
            lines.append("\nSection Order:")
            lines.append("- " + " -> ".join(self.section_order))

        if self.sections:
            lines.append("\nSection-by-Section Notes:")
            for sec in self.sections:
                lines.append(
                    f"- Section {sec.index} [{sec.inferred_kind}] "
                    f"{sec.narrative or sec.text_sample or 'No narrative available.'}"
                )

        if self.images:
            lines.append("\nImages:")
            for img in self.images[:10]:
                alt = img.alt or "No alt text"
                role = img.inferred_role or "Supporting visual"
                lines.append(
                    f"- Section {img.section_index} [{img.section_kind}]: {role}. Alt/context: {alt}"
                )

        if self.overall_impression:
            lines.append("\nOverall Impression:")
            for item in self.overall_impression:
                lines.append(f"- {item}")

        if self.long_visual_summary:
            lines.append("\nDetailed Visual Summary:")
            lines.append(self.long_visual_summary)

        return "\n".join(lines)