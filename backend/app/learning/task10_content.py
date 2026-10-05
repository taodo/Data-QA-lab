"""Bilingual guided ETL/API curriculum. Solutions stay in private profiles."""

import json
from backend.app.learning import etl, http_exercises as http

SCHEMA = {
    name: {
        "grain": (
            "one row per run step"
            if name.endswith("steps")
            else "one row per order/event; see lesson contract"
        ),
        "columns": dict(part.strip().split(" ", 1) for part in ddl.split(", ")),
    }
    for name, ddl in {**etl.DDL, **http.DDL}.items()
}
# Decimal DDL contains commas; use explicit columns for those tables.
for name in ("etl_target", "api_expected", "api_target"):
    SCHEMA[name]["columns"] = {
        "order_id": "bigint",
        "customer_id": "bigint",
        "net_amount": "numeric(18,2)",
        **({"event_id": "bigint"} if name == "etl_target" else {}),
    }

for name, grain in {
    "etl_context": "one row per exercise; current visible batch",
    "etl_customers": "one row per customer_code reference key",
    "etl_source": "one row per event_id; order_id may have multiple versions",
    "etl_target": "one row per order_id is required; faulty fixtures can violate this",
    "etl_rejects": "one row per rejected order_id is required",
    "etl_steps": "one row per step_no; the highest step is latest",
    "api_context": "one row per exercise",
    "api_expected": "one reference row per order_id",
    "api_target": "one row per order_id is required after replay",
}.items():
    SCHEMA[name]["grain"] = grain

DEFINITIONS = [
    (
        "lab_014_etl_mapping",
        "ETL_MAPPING",
        "Source-to-target mapping",
        "Ánh xạ Source sang Target",
        "Resolve customer codes using a reference table, then reconcile keys and customer IDs.",
        "Tra mã customer qua bảng tham chiếu, rồi đối soát key và customer ID.",
        "ETL maps source customer_code to etl_customers.customer_id. Target grain is one order_id. A successful load can map C-A to the wrong customer while preserving every count. FULL JOIN catches missing and unexpected orders; compare customer_id with IS DISTINCT FROM. Do not compare row positions.",
        "ETL ánh xạ customer_code từ Source sang customer_id trong etl_customers. Target có một dòng mỗi order_id. Load thành công vẫn có thể gán C-A cho customer sai dù count giữ nguyên. FULL JOIN bắt order thiếu/thừa; so customer_id bằng IS DISTINCT FROM. Không ghép theo vị trí dòng.",
        "Count FULL JOIN rows with missing/unexpected order_id or customer_id different from the source reference lookup. One joined row counts once.",
        "Đếm dòng FULL JOIN có order_id thiếu/thừa hoặc customer_id khác kết quả tra bảng tham chiếu từ Source. Mỗi dòng ghép tính một lần.",
        "SELECT s.order_id,s.customer_code,c.customer_id AS expected_customer,t.customer_id AS actual_customer FROM etl_source s JOIN etl_customers c USING(customer_code) LEFT JOIN etl_target t USING(order_id) ORDER BY s.order_id;",
        [
            "Resolve customer_code before comparing Target.",
            "Use FULL JOIN by order_id to include missing and unexpected keys.",
            "Count joined rows where either key is absent or customer_id IS DISTINCT FROM the lookup.",
        ],
        [
            "Tra customer_code trước khi so Target.",
            "FULL JOIN theo order_id để bắt key thiếu và thừa.",
            "Đếm dòng có key bị thiếu hoặc customer_id IS DISTINCT FROM kết quả tra.",
        ],
    ),
    (
        "lab_015_etl_transform",
        "ETL_TRANSFORM",
        "Transform strings into exact money",
        "Biến đổi chuỗi thành số tiền chính xác",
        "Test parsing, subtraction, legitimate zeros and one-cent errors.",
        "Kiểm tra parse, phép trừ, số 0 hợp lệ và sai lệch một cent.",
        "Source amounts arrive as strings with at most two fractional digits. The contract is net_amount = gross_text::numeric - discount_text::numeric. PostgreSQL NUMERIC preserves cents. A valid zero is not NULL. FULL JOIN also detects lost source orders; do not cast to float or round to whole money.",
        "Số tiền Source là chuỗi có tối đa hai chữ số thập phân. Hợp đồng là net_amount = gross_text::numeric - discount_text::numeric. NUMERIC của PostgreSQL giữ chính xác cent. Số 0 hợp lệ khác NULL. FULL JOIN còn bắt order bị mất; không đổi sang float hoặc làm tròn số nguyên.",
        "Count order-key FULL JOIN rows with missing keys or a Target amount distinct from the exact Source subtraction, including NULL Target amounts.",
        "Đếm dòng FULL JOIN theo order key có key thiếu hoặc amount Target khác phép trừ chính xác từ Source, kể cả amount Target NULL.",
        "SELECT s.order_id,s.gross_text,s.discount_text,t.net_amount FROM etl_source s LEFT JOIN etl_target t USING(order_id) ORDER BY s.order_id;",
        [
            "Cast each Source operand to numeric.",
            "Compare by key with IS DISTINCT FROM so NULL remains observable.",
            "Count missing keys and mismatched amounts once per joined row.",
        ],
        [
            "Cast từng toán hạng Source sang numeric.",
            "So theo key bằng IS DISTINCT FROM để bắt NULL.",
            "Đếm key thiếu và amount sai, mỗi dòng ghép một lần.",
        ],
    ),
    (
        "lab_016_etl_quarantine",
        "ETL_REJECT",
        "Reject invalid records without losing evidence",
        "Quarantine dòng sai và giữ bằng chứng",
        "Prove valid rows are accepted and malformed amounts are quarantined.",
        "Chứng minh dòng hợp lệ được nhận và amount lỗi được quarantine.",
        "An amount is valid only if it matches ^[0-9]+([.][0-9]{1,2})?$. Both gross and discount must be valid. Never cast malformed strings before filtering. Every valid key belongs in Target; every invalid key belongs only in etl_rejects with reason INVALID_AMOUNT. Rejected-key groups must be unique. Silent drops make counts misleading.",
        "Amount chỉ hợp lệ nếu khớp ^[0-9]+([.][0-9]{1,2})?$. Cả gross và discount phải hợp lệ. Không cast chuỗi sai trước khi lọc. Mỗi key hợp lệ phải ở Target; mỗi key không hợp lệ chỉ ở etl_rejects với reason INVALID_AMOUNT. Nhóm reject key phải duy nhất. Bỏ dòng âm thầm khiến count gây hiểu nhầm.",
        "Sum: valid-key vs Target FULL JOIN differences; invalid-key vs Reject FULL JOIN differences or wrong reason; duplicated reject-key groups. Each joined difference counts once.",
        "Cộng: khác biệt FULL JOIN key hợp lệ với Target; khác biệt FULL JOIN key lỗi với Reject hoặc reason sai; nhóm reject key trùng. Mỗi dòng ghép sai tính một lần.",
        "SELECT order_id,gross_text,discount_text FROM etl_source ORDER BY order_id; SELECT * FROM etl_rejects;",
        [
            "Separate valid and invalid keys before numeric conversion.",
            "Reconcile each set with its destination using FULL JOIN.",
            "Add accepted differences, rejected differences and duplicated reject groups.",
        ],
        [
            "Tách key hợp lệ và lỗi trước khi đổi numeric.",
            "FULL JOIN mỗi tập với đích tương ứng.",
            "Cộng khác biệt accepted, rejected và nhóm reject trùng.",
        ],
    ),
    (
        "lab_017_etl_replay",
        "ETL_INCREMENTAL",
        "Run batches and prove replay is idempotent",
        "Chạy batch và chứng minh replay idempotent",
        "Observe actual Target changes across three batches and replay.",
        "Quan sát Target thay đổi thật qua ba batch và replay.",
        "arrived_batch controls visibility; event_id controls the latest version per order. Batch 2 updates an existing order, batch 3 adds a late key. An upsert must retain the highest event_id and one row per key. Appending causes duplicates; skipping an existing key loses updates. RESET begins at batch 0. NEXT advances; REPLAY repeats the current batch. Use etl_context.batch_no when deriving expected rows.",
        "arrived_batch quyết định dữ liệu đã đến; event_id quyết định phiên bản mới nhất mỗi order. Batch 2 cập nhật order cũ, batch 3 thêm key đến muộn. Upsert phải giữ event_id lớn nhất và một dòng mỗi key. Append tạo duplicate; bỏ key cũ làm mất cập nhật. RESET về batch 0; NEXT tiến batch; REPLAY lặp batch hiện tại. Dùng etl_context.batch_no khi tính dữ liệu kỳ vọng.",
        "Sum latest-visible-version FULL JOIN differences (event_id and exact net_amount) and duplicated Target-key groups. Filter Source by current batch before ranking.",
        "Cộng khác biệt FULL JOIN phiên bản mới nhất đã đến (event_id và net_amount chính xác) với nhóm Target key trùng. Lọc Source theo batch hiện tại trước khi xếp hạng.",
        "SELECT * FROM etl_context; SELECT * FROM etl_target ORDER BY order_id,event_id;",
        [
            "Filter arrived_batch <= etl_context.batch_no.",
            "Rank each order by event_id DESC and keep rn=1.",
            "FULL JOIN expected versions to Target; add duplicated-key groups.",
        ],
        [
            "Lọc arrived_batch <= etl_context.batch_no.",
            "Xếp từng order theo event_id DESC và giữ rn=1.",
            "FULL JOIN phiên bản kỳ vọng với Target; cộng nhóm key trùng.",
        ],
    ),
    (
        "lab_018_etl_recovery",
        "ETL_RECOVERY",
        "Recover after an interrupted load",
        "Khôi phục sau load bị gián đoạn",
        "Distinguish failed execution from a successful partial publication.",
        "Phân biệt thực thi lỗi với publish thiếu nhưng báo thành công.",
        "etl_steps records execution_status and committed checkpoint. A failure before publish leaves no Target and checkpoint 0. RECOVER performs a real idempotent load and records checkpoint 1. A partial publication may report SUCCESS while omitting an order. Check both the latest execution record and keyed exact amount reconciliation; an older failure must not invalidate a later recovery.",
        "etl_steps ghi execution_status và checkpoint đã commit. Lỗi trước publish để Target rỗng và checkpoint 0. RECOVER chạy load idempotent thật và ghi checkpoint 1. Publish thiếu có thể báo SUCCESS nhưng mất order. Kiểm tra bản ghi thực thi mới nhất và đối soát amount chính xác theo key; lỗi cũ không được làm recovery mới bị fail.",
        "Add Source/Target FULL JOIN missing-key or exact-amount differences to one violation if the latest step is not SUCCESS with checkpoint 1.",
        "Cộng dòng FULL JOIN Source/Target có key thiếu hoặc amount sai với một vi phạm nếu step mới nhất không SUCCESS và checkpoint 1.",
        "SELECT * FROM etl_steps ORDER BY step_no; SELECT * FROM etl_target ORDER BY order_id;",
        [
            "Inspect only the highest step_no for execution/checkpoint.",
            "Reconcile all source keys and exact net amounts.",
            "Sum reconciliation differences and the latest-step contract violation.",
        ],
        [
            "Chỉ xét step_no cao nhất khi kiểm tra thực thi/checkpoint.",
            "Đối soát tất cả key Source và net amount chính xác.",
            "Cộng khác biệt đối soát và vi phạm hợp đồng step mới nhất.",
        ],
    ),
]
CATALOG = {}
for i, (
    key,
    track,
    title,
    vtitle,
    summary,
    vsummary,
    theory,
    vtheory,
    requirement,
    vrequirement,
    example,
    hints,
    vhints,
) in enumerate(DEFINITIONS, 14):
    CATALOG[key] = {
        "course_id": "etl-testing",
        "exercise_type": "ETL",
        "order": i,
        "level": "INTERMEDIATE",
        "track": track,
        "minutes": 30,
        "scenarios": ["clean", *etl.SPECS[key][0]],
    }
    if key == "lab_016_etl_quarantine":
        example = "SELECT order_id,gross_text,discount_text FROM etl_source ORDER BY order_id;"
    if key in ("lab_017_etl_replay", "lab_018_etl_recovery"):
        example = "SELECT * FROM etl_steps ORDER BY step_no;"
    for language, values in [
        ("ENG", (title, summary, theory, requirement, hints)),
        ("VIE", (vtitle, vsummary, vtheory, vrequirement, vhints)),
    ]:
        title, summary, theory, requirement, hints = values
        CATALOG[key][language] = {
            "title": title,
            "summary": summary,
            "theory": theory,
            "requirement": requirement,
            "objectives": (
                [
                    summary,
                    "Design a reusable check that accepts clean data and finds defects.",
                ]
                if language == "ENG"
                else [
                    summary,
                    "Thiết kế kiểm tra dùng lại được, chấp nhận dữ liệu sạch và phát hiện lỗi.",
                ]
            ),
            "steps": (
                [
                    "Inspect Source, reference tables and Target using the example.",
                    "Choose SANDBOX to explore a named defect or the clean baseline.",
                    "Run the batch controls; compare step evidence and query results.",
                    "Write one SELECT returning violation_count, then explain and submit.",
                ]
                if language == "ENG"
                else [
                    "Xem Source, bảng tham chiếu và Target bằng ví dụ.",
                    "Chọn SANDBOX để khám phá lỗi cụ thể hoặc dữ liệu sạch.",
                    "Chạy điều khiển batch; so bằng chứng step và kết quả truy vấn.",
                    "Viết một SELECT trả violation_count, giải thích rồi nộp.",
                ]
            ),
            "practice_sql": example,
            "practice_expected": (
                "Observe actual session data; this exploration query is not the complete check."
                if language == "ENG"
                else "Quan sát dữ liệu session thật; truy vấn khám phá này chưa phải kiểm tra đầy đủ."
            ),
            "hints": hints,
            "explanation": theory,
        }

API_TEXT = [
    (
        "Response contract: status, required fields and types",
        "Hợp đồng response: status, trường bắt buộc và kiểu dữ liệu",
        "HTTP 200 does not prove JSON is valid. order_id/customer_id must be integers; net_amount is a finite decimal string, including legitimate zero. Add required-field and type checks. A malformed row counts once even if several checks reject it; each final non-200 response counts once.",
        "HTTP 200 chưa chứng minh JSON hợp lệ. order_id/customer_id phải là integer; net_amount là chuỗi decimal hữu hạn, kể cả số 0 hợp lệ. Thêm kiểm tra trường bắt buộc và kiểu. Một dòng sai tính một lần dù nhiều rule bắt lỗi; mỗi response cuối khác 200 tính một lần.",
    ),
    (
        "Pagination: prove every key arrived once",
        "Pagination: chứng minh mỗi key đã đến đúng một lần",
        "A single successful page is not a complete dataset. Follow next_page to the end and compare distinct keys to api_expected; do not trust the API total alone. Count missing/unexpected keys plus duplicated response-key groups. Changing page_size must not change completeness.",
        "Một trang thành công chưa phải dataset đầy đủ. Theo next_page đến cuối rồi so key phân biệt với api_expected; không chỉ tin total từ API. Đếm key thiếu/thừa và nhóm response key trùng. Đổi page_size không được làm thay đổi completeness.",
    ),
    (
        "Bounded retries: 429, 503 and timeout",
        "Retry có giới hạn: 429, 503 và timeout",
        "The local service returns 429 then 503 before succeeding on attempt 3 for each page. Retry GET at most three times; transient attempts are evidence, not final defects. A permanent failure or timeout counts one final status violation plus missing keys. Inspect Retry-After and attempt evidence. Limits are fixed: 10 pages, 3 attempts/page, 50–300 ms/request.",
        "Dịch vụ local trả 429 rồi 503 trước khi thành công ở lần 3 mỗi trang. Retry GET tối đa ba lần; lần lỗi tạm thời là bằng chứng, chưa phải lỗi cuối. Lỗi vĩnh viễn hoặc timeout tính một vi phạm status cuối và key thiếu. Xem Retry-After và bằng chứng từng attempt. Giới hạn: 10 trang, 3 lần/trang, 50–300 ms/request.",
    ),
    (
        "API ingestion: reconcile and replay into PostgreSQL",
        "API ingestion: đối soát và replay vào PostgreSQL",
        "Enable ingest to load real HTTP records into the session PostgreSQL api_target. The same batch is applied twice. An idempotent upsert must retain one row per order_id. Compare response completeness/uniqueness plus database keys, customer_id and exact decimal net_amount against api_expected. A missing key counts in both response and Target checks.",
        "Bật ingest để load bản ghi HTTP thật vào api_target của session PostgreSQL. Cùng batch được áp dụng hai lần. Upsert idempotent phải giữ một dòng mỗi order_id. So completeness/uniqueness response và key, customer_id, net_amount decimal chính xác trong database với api_expected. Một key thiếu được tính ở cả kiểm tra response và Target.",
    ),
]
for i, (key, texts) in enumerate(zip(http.IDS, API_TEXT), 19):
    title, vtitle, theory, vtheory = texts
    CATALOG[key] = {
        "course_id": "api-testing",
        "exercise_type": "HTTP",
        "order": i,
        "level": "INTERMEDIATE",
        "track": "API_CONTRACT"
        if i == 19
        else "API_INGESTION"
        if i == 22
        else "API_RELIABILITY",
        "minutes": 30,
        "scenarios": ["clean", *http.SCENARIOS[key]],
    }
    for lang, title, theory in [("ENG", title, theory), ("VIE", vtitle, vtheory)]:
        CATALOG[key][lang] = {
            "title": title,
            "summary": title,
            "theory": theory,
            "objectives": (
                [
                    title,
                    "Use actual HTTP evidence to distinguish transport and data defects.",
                ]
                if lang == "ENG"
                else [
                    title,
                    "Dùng bằng chứng HTTP thật để phân biệt lỗi truyền tải và lỗi dữ liệu.",
                ]
            ),
            "steps": (
                [
                    "Start a SANDBOX with clean data or a named defect.",
                    "Run the example JSON plan and inspect responses and attempts.",
                    "Extend checks to cover the documented contract; use complete/unique/reconcile where required.",
                    "Run again, explain your evidence and submit the JSON test plan.",
                ]
                if lang == "ENG"
                else [
                    "Bắt đầu SANDBOX với dữ liệu sạch hoặc lỗi cụ thể.",
                    "Chạy JSON ví dụ rồi xem response và từng attempt.",
                    "Bổ sung checks cho hợp đồng; dùng complete/unique/reconcile khi cần.",
                    "Chạy lại, giải thích bằng chứng rồi nộp kế hoạch kiểm tra JSON.",
                ]
            ),
            "practice_sql": json.dumps(http.BASE, indent=2),
            "practice_expected": (
                "Status-only checks miss data defects. Inspect HTTP responses before extending the plan."
                if lang == "ENG"
                else "Chỉ kiểm tra status sẽ bỏ sót lỗi dữ liệu. Xem response HTTP trước khi bổ sung kế hoạch."
            ),
            "requirement": theory,
            "hints": (
                [
                    "Use the checks object to define expectations.",
                    "Enable all pages and the checks described in this lesson.",
                    "Contract: required/types; pagination: complete/unique; retry: max_attempts=3 and complete; ingestion: ingest/idempotent and reconcile.",
                ]
                if lang == "ENG"
                else [
                    "Dùng object checks để định nghĩa kỳ vọng.",
                    "Bật toàn bộ trang và các checks được mô tả trong bài.",
                    "Contract: required/types; pagination: complete/unique; retry: max_attempts=3 và complete; ingestion: ingest/idempotent và reconcile.",
                ]
            ),
            "explanation": theory,
        }
