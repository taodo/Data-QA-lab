"""Public curriculum taxonomy; availability reflects implemented executable labs."""
from backend.app.learning.lessons import CATALOG, lesson, course_id as lesson_course

# Subject, course and chapter are distinct; only executable courses are available.
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
             "course_id": COURSE_IDS[row[0]], "available": row[0] in {"sql","etl","api"}}
            for row in SUBJECTS]


def courses(language="VIE"):
    result = []
    for subject in subjects(language):
        available = subject["available"]
        labs = [value for key,value in CATALOG.items() if lesson_course(key)==subject["course_id"]]
        title = ("SQL for Data QA" if language == "ENG" else "SQL cho QA Data") if subject["id"]=="sql" else subject["title"]
        result.append({"id": subject["course_id"], "subject_id": subject["id"],
                       "title": title, "summary": subject["summary"], "available": available,
                       "level": "foundation-to-advanced" if available else "planned",
                       "lesson_count": len(labs) if available else 0,
                       "minutes": sum(item["minutes"] for item in labs) if available else 0,
                       "objectives": (["Write SQL checks using observable evidence.", "Detect defects with clean and faulty fixtures.", "Validate replay, freshness and dimension history."] if language == "ENG" else ["Viết kiểm tra SQL dựa trên bằng chứng.", "Phát hiện lỗi bằng dữ liệu sạch và dữ liệu có lỗi.", "Kiểm tra replay, freshness và lịch sử dimension."]) if available else [subject["summary"]],
                       "prerequisites": (["Basic database concepts; guided SQL practice is included.", "Docker Desktop running for local practical labs."] if language == "ENG" else ["Biết khái niệm database cơ bản; có hướng dẫn thực hành SQL.", "Docker Desktop đang chạy để thực hành local."]) if available else []})
    for item in result:
        if item["id"]=="etl-testing":
            item["objectives"] = (["Validate mapping, exact transformations and rejected records.","Run real isolated batches, replay and recover a failed publication.","Design SQL checks using Source/Target and execution evidence."] if language=="ENG" else ["Kiểm tra ánh xạ, biến đổi chính xác và dòng bị reject.","Chạy batch riêng biệt, replay và khôi phục publish lỗi.","Thiết kế kiểm tra SQL dùng bằng chứng Source/Target và thực thi."])
        if item["id"]=="api-testing":
            item["objectives"] = (["Test actual HTTP responses and JSON contracts.","Prove pagination completeness and bounded retries.","Load HTTP records into PostgreSQL and verify idempotent replay."] if language=="ENG" else ["Kiểm thử response HTTP thật và hợp đồng JSON.","Chứng minh pagination đầy đủ và retry có giới hạn.","Load bản ghi HTTP vào PostgreSQL và kiểm tra replay idempotent."])
            item["prerequisites"] = (["Basic HTTP/JSON concepts; guided examples are included.","Docker Desktop running for the local HTTP playground and PostgreSQL."] if language=="ENG" else ["Khái niệm HTTP/JSON cơ bản; có ví dụ hướng dẫn.","Docker Desktop đang chạy cho HTTP playground và PostgreSQL local."])
    return result


def course(course_id, language="VIE"):
    item = next((item for item in courses(language) if item["id"] == course_id), None)
    if item is None:
        return None
    item["chapters"] = []
    if item["available"]:
        chapters=list(CHAPTERS) if course_id=="sql-data-qa" else (
            [("ETL_MAPPING","Mapping & reference data","Ánh xạ & dữ liệu tham chiếu"),("ETL_TRANSFORM","Transformation contracts","Hợp đồng biến đổi"),("ETL_REJECT","Rejects & quarantine","Dữ liệu lỗi & quarantine"),("ETL_INCREMENTAL","Batches & replay","Batch & replay"),("ETL_RECOVERY","Failure & recovery","Lỗi & khôi phục")] if course_id=="etl-testing" else
            [("API_CONTRACT","HTTP & JSON contracts","Hợp đồng HTTP & JSON"),("API_RELIABILITY","Pagination & reliability","Pagination & độ tin cậy"),("API_INGESTION","Ingestion & reconciliation","Ingestion & đối soát")])
        for track, eng, vie in chapters:
            labs = [lesson(key, language) for key in sorted(CATALOG, key=lambda k: CATALOG[k]["order"]) if lesson_course(key)==course_id and CATALOG[key].get("track","FOUNDATION") == track]
            item["chapters"].append({"id": track, "title": eng if language == "ENG" else vie,
                                     "minutes": sum(lab["minutes"] for lab in labs), "lessons": labs})
    return item
