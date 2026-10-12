"""Source-controlled tutorial contracts, separate from executable lab sessions."""
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

COURSE_ID = "ai-test-automation"
SUBJECT_ID = "ai-test-automation"


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    @field_validator("*")
    @classmethod
    def nonblank(cls, value):
        if isinstance(value, str) and not value.strip():
            raise ValueError("Text cannot be blank")
        if isinstance(value, tuple) and any(isinstance(item, str) and not item.strip() for item in value):
            raise ValueError("Text items cannot be blank")
        return value


class Section(Contract):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]+$")
    type: Literal["concept", "steps", "code_sample", "prompt_template", "verification", "challenge_preview"]
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    items: tuple[str, ...] = ()
    code: str | None = None
    language: Literal["python", "powershell", "text"] | None = None

    @model_validator(mode="after")
    def payload(self):
        if any(not item.strip() for item in self.items) or not self.title.strip() or not self.body.strip():
            raise ValueError("Tutorial text cannot be blank")
        if self.type in {"code_sample", "prompt_template"}:
            if not self.code or not self.code.strip() or not self.language:
                raise ValueError("Copyable blocks require code and language")
        elif self.code is not None or self.language is not None:
            raise ValueError("Only code/prompt sections may contain code")
        return self


class LessonText(Contract):
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    sections: tuple[Section, ...] = ()


class LessonLocales(Contract):
    ENG: LessonText
    VIE: LessonText


class TutorialLesson(Contract):
    id: str = Field(pattern=r"^m[0-9]{2}-l[0-9]{2}$")
    order: int = Field(ge=1)
    status: Literal["available", "planned"]
    minutes: int = Field(gt=0)
    content: LessonLocales

    @model_validator(mode="after")
    def content_rules(self):
        eng, vie = self.content.ENG, self.content.VIE
        if any(not t.title.strip() or not t.summary.strip() for t in (eng, vie)):
            raise ValueError("Both languages require text")
        if self.status == "planned" and (eng.sections or vie.sections):
            raise ValueError("Planned lessons must not publish tutorial content")
        if self.status == "available":
            required = {"concept", "steps", "code_sample", "prompt_template", "verification", "challenge_preview"}
            for text in (eng, vie):
                if not required.issubset({s.type for s in text.sections}):
                    raise ValueError("Available lessons require complete tutorial sections")
                if len({s.id for s in text.sections}) != len(text.sections):
                    raise ValueError("Section IDs must be unique")
            if [(s.id, s.type) for s in eng.sections] != [(s.id, s.type) for s in vie.sections]:
                raise ValueError("Translated sections must match IDs, types and order")
            if [(s.code, s.language) for s in eng.sections if s.type == "code_sample"] != [(s.code, s.language) for s in vie.sections if s.type == "code_sample"]:
                raise ValueError("Copyable examples must match across languages")
        return self


class Titles(Contract):
    ENG: str = Field(min_length=1)
    VIE: str = Field(min_length=1)


class TutorialModule(Contract):
    id: str = Field(pattern=r"^m[0-9]{2}$")
    order: int = Field(ge=1)
    title: Titles
    lessons: tuple[TutorialLesson, ...]


class CourseText(Contract):
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    hybrid_explanation: str = Field(min_length=1)
    objectives: tuple[str, ...] = Field(min_length=1)
    prerequisites: tuple[str, ...] = Field(min_length=1)


class CourseLocales(Contract):
    ENG: CourseText
    VIE: CourseText


class TutorialManifest(Contract):
    id: Literal["ai-test-automation"]
    level: Literal["beginner"]
    content: CourseLocales
    modules: tuple[TutorialModule, ...]

    @model_validator(mode="after")
    def structure(self):
        if len(self.modules) != 10:
            raise ValueError("Foundation curriculum requires 10 modules")
        available = []
        for index, module in enumerate(self.modules, 1):
            if module.order != index or module.id != f"m{index:02}":
                raise ValueError("Modules require stable contiguous IDs/order")
            if len(module.lessons) != 3:
                raise ValueError("Each module requires 3 lessons")
            for order, lesson in enumerate(module.lessons, 1):
                if lesson.order != order or lesson.id != f"{module.id}-l{order:02}":
                    raise ValueError("Lessons require stable unique IDs/order")
                if lesson.status == "available":
                    available.append(lesson.id)
        if available != ["m01-l01"]:
            raise ValueError("Only m01-l01 is available in Task 21.1")
        return self


MANIFEST = TutorialManifest.model_validate(json.loads(Path(__file__).with_name("automation_curriculum.json").read_text(encoding="utf-8")))


def course(language="VIE", detail=False):
    text = getattr(MANIFEST.content, language).model_dump(mode="json")
    lessons = [lesson for module in MANIFEST.modules for lesson in module.lessons]
    result = {"id": COURSE_ID, "subject_id": SUBJECT_ID, "learning_kind": "tutorial",
              "available": True, "level": MANIFEST.level, "lesson_count": len(lessons),
              "available_lesson_count": 1, "minutes": sum(l.minutes for l in lessons), **text}
    if detail:
        result["modules"] = [{"id": module.id, "order": module.order, "title": getattr(module.title, language),
                              "lessons": [{"id": l.id, "order": l.order, "status": l.status, "minutes": l.minutes,
                                           "title": getattr(l.content, language).title, "summary": getattr(l.content, language).summary}
                                          for l in module.lessons]} for module in MANIFEST.modules]
    return result


def lesson(lesson_id, language="VIE"):
    value = next((l for m in MANIFEST.modules for l in m.lessons if l.id == lesson_id), None)
    if value is None:
        return None
    return {"course_id": COURSE_ID, "learning_kind": "tutorial", "id": value.id,
            "order": value.order, "status": value.status, "minutes": value.minutes,
            **getattr(value.content, language).model_dump(mode="json")}
