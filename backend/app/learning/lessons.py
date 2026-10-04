"""Versioned learner content. Solutions are delivered only by session lifecycle."""
from backend.app.learning.content import LAB_ID, HINTS, EXPLANATION

LANGUAGES = ("ENG", "VIE")
CATALOG = {
    LAB_ID: {
        "order": 4, "level": "FOUNDATION", "minutes": 25,
        "scenarios": ["missing_order", "equal_count_swap"],
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


def lesson(lab_id, language="VIE"):
    if language not in LANGUAGES:
        raise ValueError("Unsupported language")
    definition = CATALOG[lab_id]
    text = definition[language]
    return {"id": lab_id, "language": language, "order": definition["order"],
            "level": definition["level"], "minutes": definition["minutes"],
            "scenarios": definition["scenarios"], "schema": SCHEMA,
            **{key: value for key, value in text.items() if key not in {"hints", "explanation"}}}


def localize_session(payload, language):
    """Keep private fields excluded; translate only already-visible learner content."""
    definition = CATALOG[payload["lab_id"]][language]
    result = {**payload, "language": language, "title": definition["title"],
              "requirement": definition["requirement"], "learning_objectives": definition["objectives"],
              "hints": definition["hints"][:payload["hints_used"]]}
    if "explanation" in result:
        result["explanation"] = definition["explanation"]
    return result
