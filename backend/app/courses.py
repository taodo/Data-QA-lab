"""Public curriculum taxonomy; availability reflects implemented executable labs."""
from backend.app.learning.lessons import CATALOG, lesson, course_id as lesson_course
from backend.app.course_introductions import introduction

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
             "course_id": COURSE_IDS[row[0]], "available": any(lesson_course(k)==COURSE_IDS[row[0]] for k in CATALOG)}
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
        if item["subject_id"] in {"fabric","adf","onelake","databricks","synapse","azure"}:
            item["objectives"] = (["Trace run/activity evidence and reconcile actual snapshots.","Prove schema, replay, partitions and freshness with independent contracts.","Distinguish SIMULATED/IMPORTED evidence from live cloud verification."] if language=="ENG" else
                                  ["Truy vết run/activity và đối soát snapshot thực tế.","Chứng minh schema, replay, partition và freshness theo hợp đồng độc lập.","Phân biệt evidence SIMULATED/IMPORTED với kiểm chứng cloud thật."])
            item["prerequisites"] = (["SQL, ETL and API course fundamentals.","Local Docker PostgreSQL; no cloud account required."] if language=="ENG" else ["Kiến thức khóa SQL, ETL và API.","Docker PostgreSQL local; không cần tài khoản cloud."])
        if item["id"]=="etl-testing":
            item["objectives"] = (["Validate mapping, exact transformations and rejected records.","Run real isolated batches, replay and recover a failed publication.","Design SQL checks using Source/Target and execution evidence."] if language=="ENG" else ["Kiểm tra ánh xạ, biến đổi chính xác và dòng bị reject.","Chạy batch riêng biệt, replay và khôi phục publish lỗi.","Thiết kế kiểm tra SQL dùng bằng chứng Source/Target và thực thi."])
        if item["id"]=="api-testing":
            item["objectives"] = (["Test actual HTTP responses and JSON contracts.","Prove pagination completeness and bounded retries.","Load HTTP records into PostgreSQL and verify idempotent replay."] if language=="ENG" else ["Kiểm thử response HTTP thật và hợp đồng JSON.","Chứng minh pagination đầy đủ và retry có giới hạn.","Load bản ghi HTTP vào PostgreSQL và kiểm tra replay idempotent."])
            item["prerequisites"] = (["Basic HTTP/JSON concepts; guided examples are included.","Docker Desktop running for the local HTTP playground and PostgreSQL."] if language=="ENG" else ["Khái niệm HTTP/JSON cơ bản; có ví dụ hướng dẫn.","Docker Desktop đang chạy cho HTTP playground và PostgreSQL local."])
    outcomes={
        'databricks':(['Account for accepted, rejected and quarantined records.','Reconcile before/after versions, replay and deletion.'],['Đối soát dòng accepted, rejected và quarantined.','So version before/after, replay và xóa ngoài ý muốn.']),
        'synapse':(['Prove staging-to-fact keys and dimension mappings.','Validate reporting grain and independent totals; detect JOIN fanout.'],['Chứng minh key staging-to-fact và mapping dimension.','Kiểm tra grain báo cáo và tổng độc lập; phát hiện JOIN fanout.']),
        'azure':(['Reconcile required file paths, routes and completeness.','Investigate access errors and incomplete observations separately from data quality.'],['Đối soát path, route và độ đầy đủ file bắt buộc.','Điều tra lỗi truy cập và observation chưa đủ riêng với chất lượng dữ liệu.'])}
    for item in result:
        if item['subject_id'] in outcomes:
            item['objectives']=outcomes[item['subject_id']][0 if language=='ENG' else 1]
    return result


def course(course_id, language="VIE"):
    item = next((item for item in courses(language) if item["id"] == course_id), None)
    if item is None:
        return None
    subject_title = next(s["title"] for s in subjects(language) if s["id"] == item["subject_id"])
    item["introduction"] = introduction(course_id, subject_title, language)
    item["chapters"] = []
    if item["available"]:
        chapters=list(CHAPTERS) if course_id=="sql-data-qa" else (
            [("ETL_MAPPING","Mapping & reference data","Ánh xạ & dữ liệu tham chiếu"),("ETL_TRANSFORM","Transformation contracts","Hợp đồng biến đổi"),("ETL_REJECT","Rejects & quarantine","Dữ liệu lỗi & quarantine"),("ETL_INCREMENTAL","Batches & replay","Batch & replay"),("ETL_RECOVERY","Failure & recovery","Lỗi & khôi phục")] if course_id=="etl-testing" else
            [("API_CONTRACT","HTTP & JSON contracts","Hợp đồng HTTP & JSON"),("API_RELIABILITY","Pagination & reliability","Pagination & độ tin cậy"),("API_INGESTION","Ingestion & reconciliation","Ingestion & đối soát")])
        cloud_chapters={"fabric-testing":[("FABRIC_EVIDENCE","Runs, contracts & layers","Run, hợp đồng & layer")],
                        "adf-testing":[("ADF_EVIDENCE","Copy, replay & recovery","Copy, replay & khôi phục")],
                        "onelake-testing":[("ONELAKE_EVIDENCE","Partitions & reference freshness","Partition & freshness reference")]}
        cloud_chapters.update({
            'databricks-testing':[('DATABRICKS_FOUNDATIONS','Classification & version contracts','Contract classification & version')],
            'synapse-testing':[('SYNAPSE_FOUNDATIONS','Fact publication & reporting grain','Publication fact & grain báo cáo')],
            'azure-testing':[('AZURE_FOUNDATIONS','Lake manifests & access evidence','Manifest lake & evidence truy cập')]})
        chapters=cloud_chapters.get(course_id,chapters)
        for track, eng, vie in chapters:
            labs = [lesson(key, language) for key in sorted(CATALOG, key=lambda k: CATALOG[k]["order"]) if lesson_course(key)==course_id and CATALOG[key].get("track","FOUNDATION") == track]
            item["chapters"].append({"id": track, "title": eng if language == "ENG" else vie,
                                     "minutes": sum(lab["minutes"] for lab in labs), "lessons": labs})
    return item
