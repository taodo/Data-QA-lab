"""Public curriculum taxonomy; availability reflects implemented executable labs."""
from backend.app.learning.lessons import CATALOG, lesson

# Subject, course and chapter are distinct. Only SQL is executable in Task 9.
SUBJECTS = (
    ("sql", "SQL", "SQL", "Query evidence, reconcile records and prove data quality.", "Truy vấn bằng chứng, đối soát bản ghi và chứng minh chất lượng dữ liệu.", "core"),
    ("etl", "ETL / ELT Testing", "Kiểm thử ETL / ELT", "Validate ingestion, transformations and incremental pipelines.", "Kiểm tra ingestion, biến đổi dữ liệu và pipeline incremental.", "core"),
    ("api", "API & Data Contracts", "API & Data Contract", "Check response contracts and data consistency across services.", "Kiểm tra hợp đồng response và tính nhất quán dữ liệu giữa các dịch vụ.", "core"),
    ("fabric", "Microsoft Fabric", "Microsoft Fabric", "Investigate integrated analytics pipelines and lakehouse quality.", "Điều tra pipeline analytics tích hợp và chất lượng lakehouse.", "azure"),
    ("adf", "Azure Data Factory", "Azure Data Factory", "Validate orchestration, dependencies and data movement.", "Kiểm tra orchestration, dependency và luồng di chuyển dữ liệu.", "azure"),
    ("onelake", "OneLake", "OneLake", "Explore lake data layout, shortcuts and consistency.", "Khám phá bố cục dữ liệu lake, shortcut và tính nhất quán.", "azure"),
    ("azure", "Azure Data Platform", "Azure Data Platform", "Build shared Azure data-platform testing fundamentals.", "Xây dựng nền tảng kiểm thử hệ sinh thái dữ liệu Azure.", "azure"),
    ("databricks", "Databricks", "Databricks", "Test lakehouse transformations and versioned data.", "Kiểm thử biến đổi lakehouse và dữ liệu có phiên bản.", "lakehouse"),
    ("synapse", "Azure Synapse", "Azure Synapse", "Validate warehouse and analytics data pipelines.", "Kiểm tra pipeline dữ liệu warehouse và analytics.", "azure"),
)
COURSE_IDS = {row[0]: ("sql-data-qa" if row[0] == "sql" else row[0]+"-testing") for row in SUBJECTS}
CHAPTERS = (
    ("FOUNDATION", "SQL foundations & investigation", "SQL nền tảng & điều tra dữ liệu"),
    ("SQL_ADVANCED", "Advanced SQL & data grain", "SQL nâng cao & grain dữ liệu"),
    ("INCREMENTAL", "Incremental loads & replay", "Load incremental & replay"),
    ("FRESHNESS", "Freshness & service levels", "Độ mới dữ liệu & SLA"),
    ("SCD", "Customer versions & history", "Phiên bản & lịch sử customer"),
)


def subjects(language="VIE"):
    return [{"id": row[0], "title": row[1 if language == "ENG" else 2],
             "summary": row[3 if language == "ENG" else 4], "family": row[5],
             "course_id": COURSE_IDS[row[0]], "available": row[0] == "sql"}
            for row in SUBJECTS]


def courses(language="VIE"):
    result = []
    for subject in subjects(language):
        available = subject["available"]
        title = ("SQL for Data QA" if language == "ENG" else "SQL cho QA Data") if available else subject["title"]
        result.append({"id": subject["course_id"], "subject_id": subject["id"],
                       "title": title, "summary": subject["summary"], "available": available,
                       "level": "foundation-to-advanced" if available else "planned",
                       "lesson_count": len(CATALOG) if available else 0,
                       "minutes": sum(item["minutes"] for item in CATALOG.values()) if available else 0,
                       "objectives": (["Write SQL checks using observable evidence.", "Detect defects with clean and faulty fixtures.", "Validate replay, freshness and dimension history."] if language == "ENG" else ["Viết kiểm tra SQL dựa trên bằng chứng.", "Phát hiện lỗi bằng dữ liệu sạch và dữ liệu có lỗi.", "Kiểm tra replay, freshness và lịch sử dimension."]) if available else [subject["summary"]],
                       "prerequisites": (["Basic database concepts; guided SQL practice is included.", "Docker Desktop running for local practical labs."] if language == "ENG" else ["Biết khái niệm database cơ bản; có hướng dẫn thực hành SQL.", "Docker Desktop đang chạy để thực hành local."]) if available else []})
    return result


def course(course_id, language="VIE"):
    item = next((item for item in courses(language) if item["id"] == course_id), None)
    if item is None:
        return None
    item["chapters"] = []
    if item["available"]:
        for track, eng, vie in CHAPTERS:
            labs = [lesson(key, language) for key in sorted(CATALOG, key=lambda k: CATALOG[k]["order"]) if CATALOG[key].get("track","FOUNDATION") == track]
            item["chapters"].append({"id": track, "title": eng if language == "ENG" else vie,
                                     "minutes": sum(lab["minutes"] for lab in labs), "lessons": labs})
    return item
