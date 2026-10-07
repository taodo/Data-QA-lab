"""Versioned learner content. Solutions are delivered only by session lifecycle."""
from backend.app.learning.content import LAB_ID, HINTS, EXPLANATION

LANGUAGES = ("ENG", "VIE")
CATALOG = {
    LAB_ID: {
        "order": 4, "level": "FOUNDATION", "minutes": 25,
        "scenarios": ["clean", "missing_order", "equal_count_swap"],
        "ENG": {
            "title": "Equal counts, different orders", "summary": "Prove completeness with business keys.",
            "objectives": ["Distinguish row count from key identity", "Compare keys in both directions"],
            "theory": "COUNT measures size. Two datasets can have equal counts and different order_id values. EXCEPT compares sets; it does not prove uniqueness. Compare orders at order grain, not daily aggregates.",
            "steps": ["Count source_orders and target_orders.", "Look for keys missing from Target.", "Look for unexpected keys in Target.", "Submit the sum of both difference counts."],
            "practice_sql": "SELECT 'SOURCE' AS layer, COUNT(*) AS rows FROM source_orders\nUNION ALL SELECT 'TARGET', COUNT(*) FROM target_orders;",
            "practice_expected": "In the equal_count_swap sandbox, counts match although the keys differ.",
            "requirement": "Return one row with one non-negative integer column named violation_count: the number of missing plus unexpected order keys. Accept clean datasets and detect both missing orders and replaced keys.",
            "hints": list(HINTS), "explanation": EXPLANATION,
        },
        "VIE": {
            "title": "Bằng số lượng, khác bản ghi", "summary": "Chứng minh dữ liệu đầy đủ bằng business key.",
            "objectives": ["Phân biệt số bản ghi và danh tính key", "So sánh key theo cả hai chiều"],
            "theory": "COUNT đo số lượng. Hai tập dữ liệu có thể bằng số lượng nhưng khác order_id. EXCEPT so sánh tập hợp; chưa chứng minh tính duy nhất. Đối soát order ở grain từng order, không so với số dòng tổng hợp ngày.",
            "steps": ["Đếm source_orders và target_orders.", "Tìm key thiếu ở Target.", "Tìm key thừa ở Target.", "Nộp tổng số key khác biệt theo hai chiều."],
            "practice_sql": "SELECT 'SOURCE' AS layer, COUNT(*) AS rows FROM source_orders\nUNION ALL SELECT 'TARGET', COUNT(*) FROM target_orders;",
            "practice_expected": "Trong sandbox equal_count_swap, count bằng nhau nhưng key khác nhau.",
            "requirement": "Trả một dòng, một cột số nguyên không âm tên violation_count: tổng key thiếu và key thừa. Chấp nhận dữ liệu sạch; phát hiện cả mất order và thay key.",
            "hints": ["So sánh cùng grain: order dùng order_id; dữ liệu ngày dùng SUM(order_count).", "Count bằng nhau có thể che key thiếu và key thừa. So sánh hai chiều.", "Dùng EXCEPT từ Source sang Target và ngược lại, rồi cộng số key khác biệt."],
            "explanation": "Count đo số lượng, không đo danh tính. EXCEPT hai chiều phát hiện key thiếu và key thừa, kể cả khi count bằng nhau. Bài này chấm completeness; duplicate, NULL và tính toán cần kiểm tra riêng.",
        },
    }
}

SCHEMA = {
    "source_orders": {"grain": "order_id", "columns": {"order_id": "bigint", "customer_id": "bigint", "ordered_at": "timestamptz (UTC)", "gross_amount": "numeric(14,2)", "discount_amount": "numeric(14,2)", "refund_amount": "numeric(14,2)", "updated_at": "timestamptz (UTC)"}},
    "target_orders": {"grain": "order_id", "columns": {"order_id": "bigint", "customer_id": "bigint", "ordered_at": "timestamptz (UTC)", "net_amount": "numeric(14,2)"}},
    "gold_daily_sales": {"grain": "UTC order_date", "columns": {"order_date": "date", "order_count": "bigint", "net_revenue": "numeric(18,2)"}},
    "target_daily_sales": {"grain": "UTC order_date", "columns": {"order_date": "date", "order_count": "bigint", "net_revenue": "numeric(18,2)"}},
}


def _text(title, summary, objectives, theory, steps, practice_sql, expected, requirement, hints, explanation):
    return dict(title=title, summary=summary, objectives=objectives, theory=theory,
                steps=steps, practice_sql=practice_sql, practice_expected=expected,
                requirement=requirement, hints=hints, explanation=explanation)


CATALOG.update({
    "lab_002_sql_basics": {
        "order": 1, "level": "FOUNDATION", "minutes": 20, "scenarios": ["clean", "invalid_customer"],
        "ENG": _text(
            "Read data, find invalid values", "Start with SELECT and business rules.",
            ["Read table grain and column types", "Filter with WHERE and count violations"],
            "SELECT chooses columns; WHERE filters rows; ORDER BY controls display order. SQL tables have no guaranteed default order. In this lab every customer_id must be a positive integer. A successful query proves execution, not data validity. Inspect rows first, then express the rule as a reusable check. COUNT(*) counts rows; LIMIT helps exploration but must not limit your validation count.",
            ["Open the dataset reference and identify order_id as the business key.", "Run the example to inspect Target orders.", "Filter rows where customer_id is not positive.", "Count all matching rows and name the output violation_count."],
            "SELECT order_id, customer_id FROM target_orders ORDER BY order_id LIMIT 10;",
            "Clean data has positive customer_id values. The invalid_customer sandbox includes a non-positive value.",
            "Return one integer column violation_count: the number of Target rows with customer_id <= 0. No hardcoded order IDs or LIMIT on the counted rows. NULL and referential integrity are separate checks.",
            ["The rule is customer_id > 0; write its opposite to find defects.", "WHERE customer_id <= 0 selects both zero and negative values.", "Apply COUNT(*) to the filtered Target rows and alias it violation_count."],
            "WHERE expresses the violated rule; COUNT(*) measures its extent. The check accepts clean data and catches invalid values at different keys. This does not prove the customer exists in a customer table or that NULLs are absent."),
        "VIE": _text(
            "Đọc dữ liệu, tìm giá trị sai", "Bắt đầu với SELECT và quy tắc nghiệp vụ.",
            ["Đọc grain và kiểu dữ liệu", "Lọc bằng WHERE và đếm vi phạm"],
            "SELECT chọn cột; WHERE lọc dòng; ORDER BY quyết định thứ tự hiển thị. Bảng SQL không có thứ tự mặc định được đảm bảo. Bài này quy định customer_id là số nguyên dương. Truy vấn chạy thành công chỉ chứng minh thực thi, chưa chứng minh dữ liệu hợp lệ. Quan sát bản ghi trước rồi viết kiểm tra dùng lại được. COUNT(*) đếm dòng; LIMIT dùng để khám phá, không dùng để cắt số vi phạm cần đếm.",
            ["Mở mô tả bảng và xác định order_id là business key.", "Chạy ví dụ để xem order ở Target.", "Lọc các dòng có customer_id không dương.", "Đếm tất cả dòng vi phạm và đặt tên cột violation_count."],
            "SELECT order_id, customer_id FROM target_orders ORDER BY order_id LIMIT 10;",
            "Dữ liệu sạch có customer_id dương. Sandbox invalid_customer chứa giá trị không dương.",
            "Trả một cột số nguyên violation_count: số dòng Target có customer_id <= 0. Không hardcode order_id hoặc LIMIT tập vi phạm. NULL và khóa ngoại là kiểm tra riêng.",
            ["Quy tắc là customer_id > 0; viết điều kiện ngược để tìm lỗi.", "WHERE customer_id <= 0 bắt cả số 0 và số âm.", "Dùng COUNT(*) trên các dòng Target đã lọc, đặt alias violation_count."],
            "WHERE biểu diễn quy tắc bị vi phạm; COUNT(*) đo phạm vi lỗi. Kiểm tra chấp nhận dữ liệu sạch và bắt lỗi ở các key khác nhau. Nó chưa chứng minh customer tồn tại trong bảng customer hoặc không có NULL."),
    },
    "lab_003_nulls": {
        "order": 2, "level": "FOUNDATION", "minutes": 20, "scenarios": ["clean", "null_net_amount"],
        "ENG": _text(
            "Missing values: NULL is not zero", "Check required fields with IS NULL.",
            ["Understand SQL unknown values", "Choose the correct count expression"],
            "NULL means unknown or absent. A net amount of 0.00 is a known value and can be legitimate. Comparisons such as net_amount = NULL do not return TRUE; use IS NULL. COUNT(net_amount) excludes NULLs whereas COUNT(*) counts every row. The Target copy intentionally permits defects so you can validate the business requirement: net_amount must be populated.",
            ["Compare total rows and populated amounts in the example.", "Inspect rows using WHERE net_amount IS NULL.", "Count NULL rows without rejecting legitimate zeros.", "Submit a violation_count covering the whole Target."],
            "SELECT COUNT(*) AS total_rows, COUNT(net_amount) AS populated_amounts FROM target_orders;",
            "On a null_net_amount snapshot, populated_amounts is lower than total_rows. On clean data they match.",
            "Return violation_count equal to the number of Target rows with NULL net_amount. Zero amounts are valid; do not treat them as missing.",
            ["NULL cannot be tested with = NULL.", "Use IS NULL on the required column.", "Count the rows selected by net_amount IS NULL, or subtract COUNT(net_amount) from COUNT(*)."],
            "IS NULL detects missing data; COUNT(*) over the filtered rows gives its exact extent. The alternative total-minus-populated count is also correct. This check does not prove the non-NULL amount was calculated correctly."),
        "VIE": _text(
            "Giá trị thiếu: NULL khác số 0", "Kiểm tra trường bắt buộc bằng IS NULL.",
            ["Hiểu giá trị chưa biết trong SQL", "Chọn biểu thức COUNT phù hợp"],
            "NULL là giá trị chưa biết hoặc bị thiếu. Net amount bằng 0.00 là giá trị đã biết và có thể hợp lệ. So sánh net_amount = NULL không trả TRUE; phải dùng IS NULL. COUNT(net_amount) bỏ qua NULL còn COUNT(*) đếm mọi dòng. Bản sao Target cố ý cho phép lỗi để bạn kiểm tra yêu cầu nghiệp vụ: net_amount phải có dữ liệu.",
            ["So sánh tổng số dòng và số amount có dữ liệu trong ví dụ.", "Xem các dòng bằng WHERE net_amount IS NULL.", "Đếm dòng NULL, không loại nhầm số 0 hợp lệ.", "Nộp violation_count trên toàn bộ Target."],
            "SELECT COUNT(*) AS total_rows, COUNT(net_amount) AS populated_amounts FROM target_orders;",
            "Snapshot null_net_amount có populated_amounts nhỏ hơn total_rows. Dữ liệu sạch có hai số bằng nhau.",
            "Trả violation_count bằng số dòng Target có net_amount NULL. Số 0 hợp lệ; không coi nó là dữ liệu thiếu.",
            ["Không kiểm tra NULL bằng = NULL.", "Dùng IS NULL cho cột bắt buộc.", "Đếm dòng net_amount IS NULL, hoặc lấy COUNT(*) trừ COUNT(net_amount)."],
            "IS NULL phát hiện dữ liệu thiếu; COUNT(*) trên tập đã lọc cho số vi phạm chính xác. Lấy tổng số dòng trừ số amount có dữ liệu cũng đúng. Kiểm tra này chưa chứng minh amount khác NULL được tính đúng."),
    },
    "lab_004_duplicates": {
        "order": 3, "level": "FOUNDATION", "minutes": 25, "scenarios": ["clean", "duplicate_order"],
        "ENG": _text(
            "One order, one business key", "Find duplicates with GROUP BY and HAVING.",
            ["Distinguish duplicate keys from duplicate rows", "Count groups that violate uniqueness"],
            "The intended Target grain is one row per order_id. GROUP BY collects rows sharing a key. HAVING filters groups after aggregation, while WHERE filters input rows. A key occurring three times is one duplicated key and two excess rows. Those are different metrics. This exercise asks for duplicated key groups, even when other fields differ.",
            ["Inspect row frequency per order_id.", "Retain groups with COUNT(*) > 1 using HAVING.", "Wrap these groups in a subquery and count them.", "Explain why this differs from counting excess rows."],
            "SELECT order_id, COUNT(*) AS occurrences FROM target_orders GROUP BY order_id ORDER BY occurrences DESC, order_id LIMIT 10;",
            "Clean data has one occurrence per key. The duplicate_order sandbox repeats a key.",
            "Return violation_count as the number of distinct order_id groups occurring more than once in Target, not the number of excess rows.",
            ["Group by the business key, not every column.", "HAVING COUNT(*) > 1 isolates duplicate groups.", "Count the rows of that grouped subquery and alias the count violation_count."],
            "GROUP BY order_id with HAVING COUNT(*) > 1 identifies violated key groups. The outer count returns the requested metric. Whole-row DISTINCT can hide key duplication when values differ; excess-row counts answer a different question."),
        "VIE": _text(
            "Một order, một business key", "Tìm trùng bằng GROUP BY và HAVING.",
            ["Phân biệt key trùng và dòng trùng", "Đếm nhóm vi phạm uniqueness"],
            "Grain mong muốn của Target là một dòng cho mỗi order_id. GROUP BY gom các dòng cùng key. HAVING lọc nhóm sau tổng hợp; WHERE lọc dòng đầu vào. Một key xuất hiện ba lần là một key trùng và hai dòng dư. Đây là hai chỉ số khác nhau. Bài này yêu cầu đếm nhóm key trùng, kể cả khi các trường khác khác nhau.",
            ["Xem số lần xuất hiện của từng order_id.", "Dùng HAVING giữ nhóm COUNT(*) > 1.", "Bọc các nhóm trong subquery rồi đếm số nhóm.", "Giải thích vì sao kết quả khác số dòng dư."],
            "SELECT order_id, COUNT(*) AS occurrences FROM target_orders GROUP BY order_id ORDER BY occurrences DESC, order_id LIMIT 10;",
            "Dữ liệu sạch có một dòng mỗi key. Sandbox duplicate_order lặp lại một key.",
            "Trả violation_count là số nhóm order_id xuất hiện nhiều hơn một lần ở Target, không phải số dòng dư.",
            ["GROUP BY business key, không gom theo mọi cột.", "HAVING COUNT(*) > 1 lọc nhóm key trùng.", "Đếm số dòng của subquery đã nhóm và đặt alias violation_count."],
            "GROUP BY order_id và HAVING COUNT(*) > 1 tìm nhóm key vi phạm. COUNT bên ngoài trả đúng chỉ số yêu cầu. DISTINCT toàn dòng có thể bỏ sót key trùng khi giá trị khác nhau; đếm dòng dư trả lời câu hỏi khác."),
    },
    "lab_005_calculations": {
        "order": 5, "level": "FOUNDATION", "minutes": 30, "scenarios": ["clean", "wrong_net_amount"],
        "ENG": _text(
            "Reconcile exact amounts", "Use JOIN to validate transformations.",
            ["Match rows by business key", "Validate money with exact decimals and NULL-safe comparison"],
            "The rule is net_amount = gross_amount - discount_amount - refund_amount. For example 100.00 - 10.00 - 5.00 = 85.00. Match Source and Target by order_id before comparing fields. PostgreSQL NUMERIC preserves decimal money; do not cast to floating point or round away a cent. IS DISTINCT FROM treats a NULL versus a known amount as different. Inner JOIN checks matching keys only, so completeness and uniqueness require separate checks.",
            ["Join source_orders and target_orders on order_id.", "Calculate the expected amount from Source.", "Compare expected and actual using IS DISTINCT FROM.", "Return the count of mismatched matching rows."],
            "SELECT s.order_id, s.gross_amount-s.discount_amount-s.refund_amount AS expected_net, t.net_amount AS actual_net FROM source_orders s JOIN target_orders t ON s.order_id=t.order_id ORDER BY s.order_id LIMIT 10;",
            "The wrong_net_amount sandbox has a one-cent mismatch. Both layers still have the same row count.",
            "Return violation_count equal to the number of joined Source/Target rows with incorrect net_amount, including NULL actual amounts. Compare exact NUMERIC values; key completeness is outside this lesson.",
            ["Join on order_id; do not compare unrelated row positions.", "Derive gross_amount-discount_amount-refund_amount from Source.", "Filter with t.net_amount IS DISTINCT FROM the expected expression, then COUNT(*)."],
            "A keyed JOIN aligns the records. The exact Source formula is the oracle; IS DISTINCT FROM also catches NULL actual values. Pipeline SUCCESS and equal counts cannot prove transformations correct. This check alone does not detect missing or duplicate keys."),
        "VIE": _text(
            "Đối soát số tiền chính xác", "Dùng JOIN để kiểm tra phép biến đổi.",
            ["Ghép dòng theo business key", "Kiểm tra tiền bằng decimal và so sánh an toàn với NULL"],
            "Quy tắc: net_amount = gross_amount - discount_amount - refund_amount. Ví dụ 100.00 - 10.00 - 5.00 = 85.00. Ghép Source và Target bằng order_id trước khi so trường. NUMERIC của PostgreSQL giữ số tiền thập phân chính xác; không đổi sang float hoặc làm tròn mất một cent. IS DISTINCT FROM coi NULL khác số tiền đã biết. INNER JOIN chỉ kiểm tra key khớp, nên completeness và uniqueness cần kiểm tra riêng.",
            ["JOIN source_orders và target_orders bằng order_id.", "Tính amount kỳ vọng từ Source.", "So kỳ vọng và thực tế bằng IS DISTINCT FROM.", "Trả số dòng khớp key nhưng sai giá trị."],
            "SELECT s.order_id, s.gross_amount-s.discount_amount-s.refund_amount AS expected_net, t.net_amount AS actual_net FROM source_orders s JOIN target_orders t ON s.order_id=t.order_id ORDER BY s.order_id LIMIT 10;",
            "Sandbox wrong_net_amount lệch một cent. Hai tầng vẫn có cùng số dòng.",
            "Trả violation_count bằng số dòng Source/Target đã JOIN có net_amount sai, bao gồm actual NULL. So NUMERIC chính xác; completeness ngoài phạm vi bài này.",
            ["JOIN bằng order_id; không ghép theo vị trí dòng.", "Tính gross_amount-discount_amount-refund_amount từ Source.", "Lọc t.net_amount IS DISTINCT FROM biểu thức kỳ vọng rồi COUNT(*)."],
            "JOIN theo key căn chỉnh bản ghi. Công thức Source là chuẩn đối chiếu; IS DISTINCT FROM bắt cả actual NULL. Pipeline SUCCESS và count bằng nhau chưa chứng minh biến đổi đúng. Kiểm tra này riêng lẻ không phát hiện key thiếu hoặc trùng."),
    },
    "lab_006_capstone": {
        "order": 6, "level": "FOUNDATION", "minutes": 45, "scenarios": ["clean", "mixed_order_faults", "daily_wrong"],
        "ENG": _text(
            "Investigate a successful, incorrect pipeline", "Combine order checks and daily reconciliation.",
            ["Separate execution success from quality", "Combine independent checks across explicit grains"],
            "Order tables have order grain. Gold and daily Target have UTC day grain: compare SUM(order_count), not COUNT(*) of daily rows, to the number of orders. FULL JOIN by order_date can find missing days and mismatched totals. A robust investigation combines key completeness, NULLs, duplicate keys, keyed net calculations and daily aggregates. Different checks may flag the same underlying defect; their sum is a defined diagnostic score, not a count of unique bad orders.",
            ["Inspect count and revenue at order and daily grains.", "Reuse the key, NULL, duplicate and calculation checks.", "FULL JOIN the daily datasets and compare both order_count and net_revenue, including missing days.", "Add the five check outputs and explain the evidence and remaining limitations."],
            "SELECT COUNT(*) AS daily_rows, SUM(order_count) AS represented_orders, SUM(net_revenue) AS revenue FROM gold_daily_sales;",
            "daily_rows counts days; represented_orders counts orders. The daily_wrong sandbox changes revenue without changing row counts.",
            "Return violation_count as the sum of: missing plus unexpected order keys; NULL net_amount rows; duplicated order_id groups; joined order rows whose net_amount differs from the Source formula (including NULL); and daily FULL JOIN rows with missing dates, unequal order_count or unequal net_revenue. One daily row counts once even if both totals differ. Use Gold as the day-level baseline. A defect may contribute to more than one check.",
            ["Make each check return a scalar count and test it separately.", "Use FULL JOIN for daily completeness; compare fields with IS DISTINCT FROM.", "Add the completeness, NULL, duplicate, calculation and daily mismatch scalar counts into violation_count."],
            "The composite check retains the different grains and validation meanings. EXCEPT covers keys, grouped counts cover duplicates, IS NULL covers required amounts, keyed comparisons cover transformations and FULL JOIN covers day-level differences. The score sums rule violations; a NULL amount can count in both required-field and calculation checks. Explain the evidence instead of calling it a count of unique defective orders."),
        "VIE": _text(
            "Điều tra pipeline thành công nhưng sai dữ liệu", "Kết hợp kiểm tra order và đối soát theo ngày.",
            ["Tách thực thi thành công và chất lượng dữ liệu", "Kết hợp kiểm tra độc lập ở grain rõ ràng"],
            "Bảng order có grain từng order. Gold và Target ngày có grain ngày UTC: dùng SUM(order_count), không dùng COUNT(*) dòng ngày, để so với số order. FULL JOIN theo order_date tìm ngày thiếu và tổng sai. Điều tra cần completeness theo key, NULL, duplicate key, phép tính net theo key và tổng hợp ngày. Nhiều kiểm tra có thể bắt cùng một lỗi gốc; tổng của chúng là điểm vi phạm được định nghĩa, không phải số order lỗi duy nhất.",
            ["Xem count và revenue ở grain order và ngày.", "Dùng lại kiểm tra key, NULL, duplicate và phép tính.", "FULL JOIN bảng ngày, so cả order_count và net_revenue, bao gồm ngày thiếu.", "Cộng năm kết quả kiểm tra và ghi kết luận về bằng chứng, giới hạn."],
            "SELECT COUNT(*) AS daily_rows, SUM(order_count) AS represented_orders, SUM(net_revenue) AS revenue FROM gold_daily_sales;",
            "daily_rows đếm ngày; represented_orders đếm order. Sandbox daily_wrong đổi revenue nhưng không đổi count.",
            "Trả violation_count bằng tổng: key order thiếu và thừa; dòng net_amount NULL; nhóm order_id trùng; dòng order đã JOIN có net_amount khác công thức Source (kể cả NULL); và dòng FULL JOIN ngày có ngày thiếu, order_count khác hoặc net_revenue khác. Một dòng ngày chỉ tính một lần dù cả hai tổng sai. Dùng Gold làm chuẩn theo ngày. Một lỗi có thể bị nhiều kiểm tra cùng bắt.",
            ["Cho mỗi kiểm tra trả một số đếm và chạy riêng trước.", "FULL JOIN để bắt ngày thiếu; IS DISTINCT FROM để so trường.", "Cộng số vi phạm completeness, NULL, duplicate, phép tính và đối soát ngày thành violation_count."],
            "Kiểm tra tổng hợp giữ grain và ý nghĩa từng quy tắc. EXCEPT kiểm tra key, nhóm đếm kiểm tra duplicate, IS NULL kiểm tra amount bắt buộc, so theo key kiểm tra phép biến đổi và FULL JOIN đối soát ngày. Điểm cộng số vi phạm quy tắc; một amount NULL có thể được tính ở cả kiểm tra bắt buộc và phép tính. Giải thích bằng chứng, không gọi kết quả là số order lỗi duy nhất."),
    },
})


from backend.app.learning.advanced_lessons import CATALOG as ADVANCED_CATALOG, SCHEMA as ADVANCED_SCHEMA
from backend.app.learning.advanced_profiles import SPECS
CATALOG.update(ADVANCED_CATALOG)
SCHEMA.update(ADVANCED_SCHEMA)
for key, definition in ADVANCED_CATALOG.items():
    definition["scenarios"] = ["clean", *SPECS[key][0]]


from backend.app.learning.task10_content import CATALOG as TASK10_CATALOG, SCHEMA as TASK10_SCHEMA
CATALOG.update(TASK10_CATALOG)
SCHEMA.update(TASK10_SCHEMA)

from backend.app.learning.cloud_content import CATALOG as CLOUD_CATALOG, SCHEMA as CLOUD_SCHEMA
CATALOG.update(CLOUD_CATALOG)
SCHEMA.update(CLOUD_SCHEMA)
from backend.app.learning.foundations_content import CATALOG as FOUNDATIONS_CATALOG, SCHEMA as FOUNDATIONS_SCHEMA
CATALOG.update(FOUNDATIONS_CATALOG)
SCHEMA.update(FOUNDATIONS_SCHEMA)


from backend.app.learning.sql_guidance import apply_guidance
apply_guidance(CATALOG)

from backend.app.learning.etl_guidance import apply_guidance as apply_etl_guidance
apply_etl_guidance(CATALOG)

from backend.app.learning.api_guidance import apply_guidance as apply_api_guidance
apply_api_guidance(CATALOG)

from backend.app.learning.cloud_guidance import apply_guidance as apply_cloud_guidance
apply_cloud_guidance(CATALOG)

from backend.app.learning.foundations_guidance import apply_guidance as apply_foundations_guidance
apply_foundations_guidance(CATALOG)


def course_id(lab_id):
    return CATALOG[lab_id].get("course_id", "sql-data-qa")


def lesson(lab_id, language="VIE"):
    if language not in LANGUAGES:
        raise ValueError("Unsupported language")
    from backend.app.learning.profiles import PROFILES
    definition = CATALOG[lab_id]
    text = definition[language]
    offsets={"etl-testing":13,"api-testing":18,"fabric-testing":22,"adf-testing":25,"onelake-testing":28,
             'databricks-testing':30,'synapse-testing':32,'azure-testing':34}
    position=definition["order"] - offsets.get(course_id(lab_id),0)
    return {"id": lab_id, "language": language, "order": position,
            "level": definition["level"], "minutes": definition["minutes"],
            "track": definition.get("track", "FOUNDATION"), "course_id": course_id(lab_id), "exercise_type": definition.get("exercise_type", "SQL"),
            "scenarios": definition["scenarios"],
            "schema": {key:SCHEMA[key] for key in PROFILES[lab_id].datasets},
            **{key: value for key, value in text.items() if key not in {"hints", "explanation"}}}


def localize_session(payload, language):
    """Keep private fields excluded; translate only already-visible learner content."""
    definition = CATALOG[payload["lab_id"]][language]
    result = {**payload, "language": language, "course_id":course_id(payload["lab_id"]), "exercise_type":CATALOG[payload["lab_id"]].get("exercise_type","SQL"), "title": definition["title"],
              "requirement": definition["requirement"], "learning_objectives": definition["objectives"],
              "hints": definition["hints"][:payload["hints_used"]]}
    if "explanation" in result:
        result["explanation"] = definition["explanation"]
    return result
