from typing import List, Optional, Literal, Union
from pydantic import BaseModel, Field


class TLocation(BaseModel):
    address: Optional[str] = None
    postalCode: Optional[str] = None
    city: Optional[str] = None
    countryCode: Optional[str] = None
    region: Optional[str] = None


class TProfile(BaseModel):
    network: Optional[str] = None
    username: Optional[str] = None
    url: Optional[str] = None


class TBasicsFields(BaseModel):
    name: Optional[str] = None
    label: Optional[str] = None
    image: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    url: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[TLocation] = None
    profiles: List[TProfile] = Field(default_factory=list)


class TBasics(BaseModel):
    type: Literal["basics"]
    fields: TBasicsFields


class TWorkItemFields(BaseModel):
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


class TWorkItem(BaseModel):
    type: Literal["work_item"]
    fields: TWorkItemFields


class TWorkSection(BaseModel):
    type: Literal["work"]
    label: Optional[str] = None
    children: List[TWorkItem] = Field(default_factory=list)


class TEducationItemFields(BaseModel):
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


class TEducationItem(BaseModel):
    type: Literal["education_item"]
    fields: TEducationItemFields


class TEducationSection(BaseModel):
    type: Literal["education"]
    label: Optional[str] = None
    children: List[TEducationItem] = Field(default_factory=list)


class TProjectItemFields(BaseModel):
    name: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    role: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)


class TProjectItem(BaseModel):
    type: Literal["project_item"]
    fields: TProjectItemFields


class TProjectSection(BaseModel):
    type: Literal["projects"]
    label: Optional[str] = None
    children: List[TProjectItem] = Field(default_factory=list)


class TCustomItemFields(BaseModel):
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


class TCustomItem(BaseModel):
    type: Literal["custom_item"]
    fields: TCustomItemFields


class TCustomSectionFields(BaseModel):
    sectionTitle: Optional[str] = None
    sectionType: Optional[str] = None
    summary: Optional[str] = None


class TCustomSection(BaseModel):
    type: Literal["custom"]
    label: Optional[str] = None
    fields: TCustomSectionFields
    children: List[TCustomItem] = Field(default_factory=list)


TSection = Union[
    TWorkSection,
    TEducationSection,
    TProjectSection,
    TCustomSection,
]


class TMeta(BaseModel):
    sourceFileName: Optional[str] = None
    sourceFormat: Optional[str] = None
    parsedAt: Optional[str] = None
    parserVersion: Optional[str] = None
    rawText: Optional[str] = None


class TResume(BaseModel):
    basics: TBasics
    sections: List[TSection] = Field(default_factory=list)
    meta: TMeta


class StructuredLLMTransport(BaseModel):
    message: str
    parsed_resume: Optional[TResume] = None