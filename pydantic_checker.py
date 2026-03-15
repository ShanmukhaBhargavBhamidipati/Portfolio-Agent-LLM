from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class Location(BaseModel):
    address: Optional[str] = None
    postalCode: Optional[str] = None
    city: Optional[str] = None
    countryCode: Optional[str] = None
    region: Optional[str] = None

class Profile(BaseModel):
    network: Optional[str] = None
    username: Optional[str] = None
    url: Optional[str] = None

class BasicsFields(BaseModel):
    name: Optional[str] = None
    label: Optional[str] = None
    image: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    url: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[Location] = None
    profiles: List[Profile] = Field(default_factory=list)

class Basics(BaseModel):
    type: str
    fields: BasicsFields
    children: List[Any] = Field(default_factory=list)
    raw: Optional[Any] = None
    other: Dict[str, Any] = Field(default_factory=dict)
    unmapped: List[Any] = Field(default_factory=list)

class WorkItemFields(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    url: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None
    employmentType: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)

class WorkItem(BaseModel):
    type: str
    fields: WorkItemFields
    children: List[Any] = Field(default_factory=list)
    raw: Optional[Any] = None
    other: Dict[str, Any] = Field(default_factory=dict)
    unmapped: List[Any] = Field(default_factory=list)

class WorkSection(BaseModel):
    type: str
    label: Optional[str] = None
    fields: Dict[str, Any] = Field(default_factory=dict)
    children: List[WorkItem] = Field(default_factory=list)
    raw: Optional[Any] = None
    other: Dict[str, Any] = Field(default_factory=dict)
    unmapped: List[Any] = Field(default_factory=list)

class EducationItemFields(BaseModel):
    institution: Optional[str] = None
    url: Optional[str] = None
    area: Optional[str] = None
    studyType: Optional[str] = None
    degree: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    score: Optional[str] = None
    grade: Optional[str] = None
    location: Optional[str] = None
    courses: List[str] = Field(default_factory=list)
    honors: List[str] = Field(default_factory=list)
    activities: List[str] = Field(default_factory=list)
    thesis: Optional[str] = None

class EducationItem(BaseModel):
    type: str
    fields: EducationItemFields
    children: List[Any] = Field(default_factory=list)
    raw: Optional[Any] = None
    other: Dict[str, Any] = Field(default_factory=dict)
    unmapped: List[Any] = Field(default_factory=list)

class EducationSection(BaseModel):
    type: str
    label: Optional[str] = None
    fields: Dict[str, Any] = Field(default_factory=dict)
    children: List[EducationItem] = Field(default_factory=list)
    raw: Optional[Any] = None
    other: Dict[str, Any] = Field(default_factory=dict)
    unmapped: List[Any] = Field(default_factory=list)

class ProjectItemFields(BaseModel):
    name: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    role: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)

class ProjectItem(BaseModel):
    type: str
    fields: ProjectItemFields
    children: List[Any] = Field(default_factory=list)
    raw: Optional[Any] = None
    other: Dict[str, Any] = Field(default_factory=dict)
    unmapped: List[Any] = Field(default_factory=list)

class ProjectSection(BaseModel):
    type: str
    label: Optional[str] = None
    fields: Dict[str, Any] = Field(default_factory=dict)
    children: List[ProjectItem] = Field(default_factory=list)
    raw: Optional[Any] = None
    other: Dict[str, Any] = Field(default_factory=dict)
    unmapped: List[Any] = Field(default_factory=list)

class CustomItemFields(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    date: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)

class CustomItem(BaseModel):
    type: str
    fields: CustomItemFields
    children: List[Any] = Field(default_factory=list)
    raw: Optional[Any] = None
    other: Dict[str, Any] = Field(default_factory=dict)
    unmapped: List[Any] = Field(default_factory=list)

class CustomSectionFields(BaseModel):
    sectionTitle: Optional[str] = None
    sectionType: Optional[str] = None
    summary: Optional[str] = None

class CustomSection(BaseModel):
    type: str
    label: Optional[str] = None
    fields: CustomSectionFields
    children: List[CustomItem] = Field(default_factory=list)
    raw: Optional[Any] = None
    other: Dict[str, Any] = Field(default_factory=dict)
    unmapped: List[Any] = Field(default_factory=list)

class Meta(BaseModel):
    sourceFileName: Optional[str] = None
    sourceFormat: Optional[str] = None
    parsedAt: Optional[str] = None
    parserVersion: Optional[str] = None
    rawText: Optional[str] = None
    other: Dict[str, Any] = Field(default_factory=dict)

Section = Union[WorkSection, EducationSection, ProjectSection, CustomSection]

class Resume(BaseModel):
    basics: Basics
    sections: List[Section] = Field(default_factory=list)
    meta: Meta

class LLMResponse(BaseModel):
    message: str
    parsed_resume: Optional[Resume] = None