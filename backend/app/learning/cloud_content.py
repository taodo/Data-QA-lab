"""Eight bilingual lessons; cloud providers are taught with labelled local evidence."""
import re
from backend.app.learning import cloud

GRAINS = {
    "cloud_context": "one row per session; fixed UTC as_of and visible batch",
    "cloud_runs": "one row per run_id; provider execution evidence",
    "cloud_activities": "one row per run_id/activity_id; dependency belongs to the same run",
    "cloud_source": "one row per event_id; several versions may share order_id",
    "cloud_bronze": "one latest visible row per order_id; defects may violate uniqueness",
    "cloud_silver": "one latest visible row per order_id; defects may violate uniqueness",
    "cloud_target": "one latest visible row per order_id; defects may violate uniqueness",
    "cloud_schema": "one reported field per dataset/column_name",
    "cloud_expected_schema": "one independent contract per dataset/column_name",
    "cloud_manifest": "one row per file_key; duplicates remain observable",
    "cloud_expected_partitions": "one independently required UTC partition",
    "cloud_references": "one observed dataset_id/reference_id",
    "cloud_required_references": "one independently required reference and inclusive SLA",
    "cloud_steps": "one row per step_no; greatest step_no is current execution/checkpoint",
    "cloud_imports": "one immutable import_id; raw file, SHA-256 and run IDs retained",
}
SCHEMA = {table: {"grain": GRAINS[table], "columns": dict(field.strip().split(" ", 1)
          for field in re.split(r",(?![^()]*\))", definition))} for table, definition in cloud.DEFINITIONS.items()}

TEXT = [
    (
        "Trace Fabric runs and dataset lineage", "Truy vết run Fabric và lineage dữ liệu",
        "A run ID connects execution evidence to published data. Activity dependency IDs must resolve inside the same run. A successful activity with an orphaned Target run ID is not traceable. This lesson scores activities without a known run/state/source/target, unresolved or unsuccessful dependencies, and Target rows whose run ID is absent. Each activity or Target row counts once in each applicable rule; UNKNOWN is an evidence gap, not a fabricated success.",
        "Run ID nối bằng chứng thực thi với dữ liệu đã publish. Dependency ID của activity phải thuộc cùng run. Activity thành công nhưng Target mang run ID không tồn tại thì không truy vết được. Bài này cộng activity thiếu run/state/source/target đã biết, dependency thiếu hoặc chưa thành công, và dòng Target có run ID không tồn tại. Mỗi activity/dòng Target tính một lần trong từng quy tắc phù hợp; UNKNOWN là thiếu bằng chứng, không phải thành công giả định.",
        "SELECT a.activity_id,a.run_id,a.dependency_id,a.execution_status,r.execution_status AS run_state FROM cloud_activities a LEFT JOIN cloud_runs r USING(run_id);",
        ["Join activities to runs by run_id.", "Join dependencies by both activity_id and run_id.", "Add unlinked Target rows; compare unknown states explicitly."],
        ["JOIN activity với run theo run_id.", "JOIN dependency theo cả activity_id và run_id.", "Cộng dòng Target mất liên kết; kiểm tra state UNKNOWN rõ ràng."],
    ),
    (
        "Detect schema drift before publication", "Phát hiện schema drift trước publication",
        "The reported provider schema is evidence, separate from the local typed snapshot. cloud_expected_schema is the independently defined contract. FULL JOIN on dataset and column_name catches missing and unexpected fields; compare data_type exactly. Add the number of duplicate dataset/column groups. A float declaration for exact money violates the contract even if the current local NUMERIC rows look correct. Reported types are data; the importer never executes DDL from them.",
        "Schema do provider báo là bằng chứng riêng với snapshot local đã có kiểu. cloud_expected_schema là hợp đồng định nghĩa độc lập. FULL JOIN theo dataset và column_name bắt trường thiếu/thừa; so data_type chính xác. Cộng số nhóm dataset/column bị trùng. Khai báo float cho tiền vi phạm hợp đồng dù dòng NUMERIC local hiện đúng. Type được báo là dữ liệu; importer không chạy DDL từ type đó.",
        "SELECT e.dataset,e.column_name,e.data_type AS expected_type,a.data_type AS actual_type FROM cloud_expected_schema e FULL JOIN cloud_schema a USING(dataset,column_name);",
        ["Compare field identity in both directions.", "Use IS DISTINCT FROM on type strings.", "Add duplicate field groups; do not infer provider schema from local storage."],
        ["So tên field theo hai chiều.", "Dùng IS DISTINCT FROM với chuỗi type.", "Cộng nhóm field trùng; không suy schema provider từ storage local."],
    ),
    (
        "Reconcile Bronze, Silver and Gold snapshots", "Đối soát snapshot Bronze, Silver và Gold",
        "cloud_target represents the published Gold order snapshot, at order_id grain. Source has event grain: choose the greatest event_id for each order among arrived batches and updated_at <= as_of. Compare Source→Bronze, Bronze→Silver and Silver→Target by key, customer, exact amount, timestamp and event ID. Sum each edge's differing FULL JOIN rows plus duplicated order-key groups in the three outputs. An equal-count key swap remains a defect; the score counts rule violations, not unique bad orders.",
        "cloud_target là snapshot order Gold đã publish, grain order_id. Source có grain event: chọn event_id lớn nhất mỗi order trong batch đã tới và updated_at <= as_of. So Source→Bronze, Bronze→Silver, Silver→Target theo key, customer, amount chính xác, timestamp và event ID. Cộng dòng FULL JOIN sai ở từng cạnh và nhóm order key trùng trong ba output. Thay key giữ nguyên count vẫn là lỗi; điểm đếm vi phạm quy tắc, không phải order lỗi duy nhất.",
        "SELECT 'Bronze' AS layer,COUNT(*) AS rows,SUM(amount) AS exact_total FROM cloud_bronze UNION ALL SELECT 'Silver',COUNT(*),SUM(amount) FROM cloud_silver UNION ALL SELECT 'Gold',COUNT(*),SUM(amount) FROM cloud_target;",
        ["Reduce Source event grain to latest visible order grain first.", "Reconcile all three edges using FULL JOIN and IS DISTINCT FROM.", "Count duplicated output key groups separately; never compare row positions."],
        ["Thu Source event grain về order mới nhất đang thấy.", "Đối soát cả ba cạnh bằng FULL JOIN và IS DISTINCT FROM.", "Đếm nhóm key output trùng riêng; không ghép theo vị trí dòng."],
    ),
    (
        "Test ADF copy metrics against actual keys", "Kiểm tra copy metrics ADF với key thực tế",
        "rowsRead and rowsWritten describe an activity, not correctness. Compare latest visible Source with actual Target keys, customer, exact amount, event and timestamp; add duplicated Target key groups. Add one for each target activity whose state is not SUCCESS or whose metrics are NULL/differ from actual counts. If no target activity exists add one evidence gap. Equal-count swaps pass copy counts but fail keyed reconciliation. Missing metrics stay NULL rather than zero.",
        "rowsRead và rowsWritten mô tả activity, chưa chứng minh đúng dữ liệu. So Source mới nhất đang thấy với key, customer, amount chính xác, event, timestamp của Target; cộng nhóm key Target trùng. Cộng một cho mỗi activity đích có state khác SUCCESS hoặc metrics NULL/khác count thực tế. Nếu không có activity đích, cộng một thiếu bằng chứng. Thay key giữ count vượt qua copy counts nhưng thất bại đối soát theo key. Metrics thiếu giữ NULL, không đổi thành 0.",
        "SELECT activity_id,execution_status,rows_read,rows_written,(SELECT COUNT(*) FROM cloud_target) AS actual_target_rows FROM cloud_activities WHERE target_dataset='target';",
        ["Treat metrics and actual data as independent evidence.", "A target activity with any metric/state error counts once.", "Combine keyed differences, duplicated key groups and activity gaps."],
        ["Xem metrics và dữ liệu thực là bằng chứng độc lập.", "Activity đích sai metrics/state chỉ tính một lần.", "Cộng sai khác theo key, nhóm key trùng và activity thiếu bằng chứng."],
    ),
    (
        "Watermarks, late arrivals and idempotent replay", "Watermark, late arrival và replay idempotent",
        "Source events arrive in persisted batches. A late update has an older updated_at but greater event_id; a timestamp-only watermark loses it. Visibility uses batch_no <= context.batch_no and updated_at <= fixed UTC as_of, including the exact boundary and excluding a future event. Select the greatest visible event_id per order. Return differing Source/Target FULL JOIN rows plus duplicated Target key groups. RESET starts batch 0; NEXT exposes batches; REPLAY repeats publication without duplicates under the clean policy.",
        "Event Source tới trong batch đã lưu. Update tới muộn có updated_at cũ nhưng event_id lớn hơn; chỉ dùng timestamp watermark sẽ bỏ mất. Visibility dùng batch_no <= context.batch_no và updated_at <= as_of UTC cố định, nhận đúng biên và loại event tương lai. Chọn event_id lớn nhất đang thấy mỗi order. Trả tổng dòng FULL JOIN Source/Target sai và nhóm key Target trùng. RESET về batch 0; NEXT mở batch; REPLAY lặp publication không trùng với policy sạch.",
        "SELECT order_id,event_id,batch_no,updated_at,amount FROM cloud_source ORDER BY batch_no,event_id;",
        ["Apply arrival and as-of bounds before ranking versions.", "Late event order 1 and exact-boundary order 2 are both eligible in batch 2.", "Use greatest event_id and compare fields with IS DISTINCT FROM; add duplicate groups."],
        ["Áp dụng biên arrival/as-of trước khi xếp version.", "Event muộn order 1 và event đúng biên order 2 đều hợp lệ ở batch 2.", "Chọn event_id lớn nhất, so bằng IS DISTINCT FROM và cộng nhóm trùng."],
    ),
    (
        "Verify dependency recovery and publication", "Kiểm chứng recovery dependency và publication",
        "Recovery requires both correct data and current execution/checkpoint evidence. Return latest visible Source/Target differing FULL JOIN rows, duplicated Target key groups, one per non-SUCCESS activity, and one if the latest step is absent/non-SUCCESS or its batch checkpoint differs from context. An older failed run remains evidence after RECOVER; inspect the latest step, not any historical failure. A partial publication can report SUCCESS and still miss a key. Repeat recovery must retain one row per order.",
        "Recovery cần dữ liệu đúng lẫn bằng chứng execution/checkpoint hiện tại. Trả tổng dòng FULL JOIN Source/Target mới nhất sai, nhóm key Target trùng, một cho mỗi activity khác SUCCESS và một nếu step cuối thiếu/khác SUCCESS hoặc checkpoint batch khác context. Run lỗi cũ vẫn là bằng chứng sau RECOVER; xem step cuối, không dùng bất kỳ lỗi lịch sử nào. Publication một phần có thể SUCCESS nhưng thiếu key. Recovery lặp phải giữ một dòng mỗi order.",
        "SELECT * FROM cloud_steps ORDER BY step_no;",
        ["Inspect failed dependencies separately from Target data.", "Read the greatest step_no and compare its batch_no to context.", "Add keyed differences, duplicate groups, non-success activities and the latest checkpoint rule."],
        ["Xem dependency lỗi riêng với dữ liệu Target.", "Đọc step_no lớn nhất và so batch_no với context.", "Cộng sai khác theo key, nhóm trùng, activity chưa thành công và quy tắc checkpoint cuối."],
    ),
    (
        "Prove partition and file completeness", "Chứng minh partition và file đầy đủ",
        "A file manifest is observable evidence, not a listing fetched from real OneLake. cloud_expected_partitions defines two independently required UTC partitions and row counts. Group manifest rows by partition, SUM(row_count), then FULL JOIN expected partitions; count missing/unexpected/mismatched partition groups once. Add duplicated file_key groups. A repeated file may violate both the aggregate and duplicate rule. NULL row counts mean incomplete evidence. Imported file keys are labels; paths and links are never resolved.",
        "File manifest là bằng chứng quan sát được, không phải listing lấy từ OneLake thật. cloud_expected_partitions định nghĩa độc lập hai partition UTC và row counts cần có. Nhóm manifest theo partition, SUM(row_count), FULL JOIN với expected; đếm nhóm partition thiếu/thừa/sai một lần. Cộng nhóm file_key trùng. File lặp có thể vi phạm cả tổng lẫn quy tắc trùng. Row count NULL là thiếu bằng chứng. File key import chỉ là nhãn; không resolve path/link.",
        "SELECT partition_key,COUNT(*) AS files,SUM(row_count) AS represented_rows FROM cloud_manifest GROUP BY partition_key ORDER BY partition_key;",
        ["Do not confuse file count and represented row count.", "FULL JOIN partition aggregates to the independent expected table.", "Add duplicate file_key groups; count each partition mismatch once."],
        ["Không nhầm số file với số dòng được đại diện.", "FULL JOIN tổng theo partition với bảng expected độc lập.", "Cộng nhóm file_key trùng; mỗi partition sai tính một lần."],
    ),
    (
        "Check shortcut reference freshness at a fixed clock", "Kiểm tra freshness reference shortcut với đồng hồ cố định",
        "This lesson models referenced-dataset evidence, not real shortcut resolution. FULL JOIN required and observed references by dataset_id/reference_id. Count missing/unexpected references, NULL observed_at, future timestamps or age strictly greater than SLA minutes; one joined row counts once. Exactly 60 minutes is fresh for a 60-minute SLA; one microsecond older is stale. Use context.as_of, never NOW(). A completed run can reference stale data, and missing capture time cannot establish freshness.",
        "Bài này mô hình hóa bằng chứng dataset được tham chiếu, không resolve shortcut thật. FULL JOIN reference bắt buộc và đã quan sát theo dataset_id/reference_id. Đếm reference thiếu/thừa, observed_at NULL, timestamp tương lai hoặc tuổi lớn hơn SLA minutes; mỗi dòng ghép tính một lần. Đúng 60 phút còn mới với SLA 60 phút; cũ hơn một microsecond là stale. Dùng context.as_of, không dùng NOW(). Run hoàn thành vẫn có thể tham chiếu dữ liệu cũ; thiếu capture time không chứng minh freshness.",
        "SELECT r.*,c.as_of,c.as_of-r.observed_at AS age FROM cloud_references r CROSS JOIN cloud_context c;",
        ["Join required references so absent observations remain visible.", "Check NULL and future time explicitly before SLA comparison.", "Use age > SLA, not >=; keep the fixed UTC as_of clock."],
        ["JOIN reference bắt buộc để thấy observation bị thiếu.", "Kiểm tra NULL và thời điểm tương lai trước khi so SLA.", "Dùng age > SLA, không dùng >=; giữ đồng hồ as_of UTC cố định."],
    ),
]

CATALOG = {}
for index, (key, text) in enumerate(zip(cloud.IDS, TEXT, strict=True), 23):
    title, vtitle, theory, vtheory, practice, hints, vhints = text
    course = "fabric-testing" if index <= 25 else "adf-testing" if index <= 28 else "onelake-testing"
    track = "FABRIC_EVIDENCE" if index <= 25 else "ADF_EVIDENCE" if index <= 28 else "ONELAKE_EVIDENCE"
    CATALOG[key] = {"order": index, "course_id": course, "level": "INTERMEDIATE", "track": track,
                    "minutes": 35, "scenarios": ["clean", *cloud.SCENARIOS[key]]}
    for lang, heading, body, clues in (("ENG", title, theory, hints), ("VIE", vtitle, vtheory, vhints)):
        eng = lang == "ENG"
        scope = ("All evidence is SIMULATED or IMPORTED locally. This is not a Microsoft service emulator. SQL remains read-only. " if eng else
                 "Mọi bằng chứng là SIMULATED hoặc IMPORTED local. Đây không phải emulator dịch vụ Microsoft. SQL chỉ đọc. ")
        CATALOG[key][lang] = {
            "title": heading, "summary": heading,
            "objectives": [heading, "Separate execution, quality and incomplete evidence." if eng else "Phân biệt thực thi, chất lượng và bằng chứng chưa đủ."],
            "theory": scope + body,
            "steps": (["Start a SANDBOX with clean data or a named fault.", "Inspect provenance, run/activity links and Source/Target snapshots.",
                       "Run the SQL example; design the defined violation_count check.", "Try an evidence file import or the session simulator, then rerun your check.",
                       "Start a CHALLENGE and submit your check with an evidence-based explanation."] if eng else
                      ["Bắt đầu SANDBOX với dữ liệu sạch hoặc lỗi cụ thể.", "Xem provenance, liên kết run/activity và snapshot Source/Target.",
                       "Chạy SQL ví dụ; viết kiểm tra violation_count theo định nghĩa.", "Thử import file evidence hoặc simulator của session rồi chạy lại kiểm tra.",
                       "Bắt đầu CHALLENGE và nộp kiểm tra cùng giải thích dựa trên bằng chứng."]),
            "practice_sql": practice,
            "practice_expected": "Inspect evidence first; this exploration query does not validate the complete contract." if eng else "Quan sát bằng chứng trước; SQL khám phá này chưa kiểm tra toàn bộ hợp đồng.",
            "requirement": ("Return one non-negative integer column named violation_count. " if eng else "Trả một cột số nguyên không âm tên violation_count. ") + body,
            "hints": clues, "explanation": scope + body,
        }
