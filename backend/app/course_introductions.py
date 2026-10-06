"""Beginner introductions, authored separately for each course and language."""


def _entry(definition, concepts, example, uses, qa, course_connection):
    return dict(definition=definition, concepts=concepts, example=example,
                uses=uses, qa=qa, course_connection=course_connection)


INTRODUCTIONS = {
    "sql-data-qa": {
        "ENG": _entry(
            "SQL (Structured Query Language) is a language for asking questions of data stored in database tables. You describe the result you want, and the database finds the matching records.",
            ["Tables contain rows (records) and columns (fields). A key identifies a record; grain describes what one row represents.",
             "SELECT reads data, WHERE filters it, JOIN connects tables, and GROUP BY calculates totals for groups.",
             "NULL means a value is missing. Window functions compare or rank related rows without collapsing them into one total."],
            "A shop stores orders and customers in separate tables. A SQL query joins them and sums each customer's paid orders to produce a monthly sales report.",
            ["Find missing values, duplicate keys and records that break business rules.", "Compare source and report tables by key, then check amounts, dates and history rather than trusting equal row counts."],
            "Data QA uses SQL to turn a suspicion into a repeatable check with evidence: which order is missing, which amount differs, and why the result matters.",
            "This course starts with reading rows and detecting defects, then covers JOIN grain, CTEs, version ranking, incremental replay, UTC freshness and customer history."),
        "VIE": _entry(
            "SQL (Structured Query Language) là ngôn ngữ để đặt câu hỏi với dữ liệu trong các bảng của cơ sở dữ liệu. Bạn mô tả kết quả cần lấy, còn cơ sở dữ liệu tìm các bản ghi phù hợp.",
            ["Bảng có hàng (bản ghi) và cột (trường dữ liệu). Khóa nhận diện bản ghi; grain cho biết một hàng đại diện cho điều gì.",
             "SELECT đọc dữ liệu, WHERE lọc, JOIN nối bảng và GROUP BY tính tổng theo nhóm.",
             "NULL nghĩa là thiếu giá trị. Hàm cửa sổ giúp so sánh hoặc xếp hạng các hàng liên quan mà không gộp chúng thành một tổng."],
            "Cửa hàng lưu đơn hàng và khách hàng ở hai bảng. Câu SQL nối hai bảng rồi cộng các đơn đã thanh toán của từng khách để tạo báo cáo bán hàng tháng.",
            ["Tìm giá trị thiếu, khóa trùng và bản ghi vi phạm quy tắc nghiệp vụ.", "Đối soát bảng nguồn và báo cáo theo khóa, rồi kiểm tra số tiền, ngày và lịch sử thay vì chỉ tin số hàng bằng nhau."],
            "Data QA dùng SQL để biến nghi ngờ thành kiểm tra có thể chạy lại và có bằng chứng: thiếu đơn nào, sai số tiền nào và sai lệch đó ảnh hưởng ra sao.",
            "Khóa học bắt đầu từ đọc bản ghi và tìm lỗi, rồi học grain khi JOIN, CTE, xếp hạng phiên bản, chạy lại dữ liệu incremental, độ mới theo UTC và lịch sử khách hàng."),
    },
    "etl-testing": {
        "ENG": _entry(
            "ETL means Extract, Transform, Load: take data from a source, reshape it, then put it into a destination. ELT loads first and transforms inside the destination. Testing checks that these steps preserve the intended meaning.",
            ["Source and Target are the input and output. A mapping says which input field becomes which output field.",
             "Transformations clean, combine or calculate values. Rejected records are held aside when they cannot safely be loaded.",
             "A batch groups work. An incremental load handles changes; a checkpoint records progress so a failed batch can resume."],
            "Every night, a retailer imports store sales, maps store customer codes to central IDs and calculates exact order totals for its reporting database.",
            ["Combine inconsistent data from several systems into a usable reporting dataset.", "Load new changes reliably, keep invalid records observable and recover without losing or duplicating orders."],
            "Data QA checks mapping rules, decimal calculations, rejected rows and Source/Target keys. A job marked successful can still publish incomplete or incorrect data.",
            "The five lessons exercise reference mapping, transformation contracts, rejects, actual PostgreSQL batches/replay and recovery after a failed publication."),
        "VIE": _entry(
            "ETL là Extract, Transform, Load: lấy dữ liệu từ nguồn, biến đổi rồi nạp vào nơi đích. ELT nạp trước và biến đổi ngay tại đích. Kiểm thử xác nhận các bước này giữ đúng ý nghĩa dữ liệu.",
            ["Source và Target là đầu vào và đầu ra. Mapping chỉ rõ trường nguồn được chuyển thành trường đích nào.",
             "Transformation làm sạch, kết hợp hoặc tính toán giá trị. Bản ghi reject được giữ riêng khi chưa thể nạp an toàn.",
             "Batch là một đợt xử lý. Load incremental xử lý thay đổi; checkpoint ghi mốc tiến độ để tiếp tục sau khi batch lỗi."],
            "Mỗi đêm, nhà bán lẻ nhập giao dịch từ cửa hàng, ánh xạ mã khách về ID chung và tính số tiền đơn hàng chính xác cho cơ sở dữ liệu báo cáo.",
            ["Gộp dữ liệu có cách ghi khác nhau từ nhiều hệ thống thành bộ dữ liệu báo cáo dùng được.", "Nạp thay đổi đáng tin cậy, theo dõi dòng không hợp lệ và khôi phục mà không mất hoặc trùng đơn."],
            "Data QA kiểm tra mapping, phép tính tiền, dòng reject và khóa Source/Target. Job báo thành công vẫn có thể xuất dữ liệu thiếu hoặc sai.",
            "Năm bài học thực hành mapping dữ liệu tham chiếu, hợp đồng biến đổi, reject, batch/replay PostgreSQL thực tế và khôi phục sau khi publish lỗi."),
    },
    "api-testing": {
        "ENG": _entry(
            "An API (Application Programming Interface) is an agreed way for one program to ask another for information or an action. A data contract describes the fields, types and rules that callers can rely on.",
            ["An endpoint is an address for a request. HTTP methods describe the action; status codes report its outcome.",
             "JSON carries named fields and values. A contract defines required fields, types and the meaning of missing values.",
             "Pagination splits results into pages. Retries repeat failed requests; idempotency means repeating an operation does not create extra effects."],
            "A delivery company requests orders from a shop's API in pages, retries a temporary failure and stores each order once in its own database.",
            ["Exchange data between systems without directly accessing each other's databases.", "Build dependable ingestion when responses are paged, delayed, incomplete or temporarily unavailable."],
            "Data QA inspects actual HTTP responses and reconciles returned keys with stored records. HTTP 200 alone does not prove every page or required field is present.",
            "The lessons cover JSON/status contracts, complete pagination, bounded retries and idempotent HTTP-to-PostgreSQL ingestion using a local HTTP playground."),
        "VIE": _entry(
            "API (Application Programming Interface) là cách đã thống nhất để chương trình này hỏi chương trình khác lấy thông tin hoặc thực hiện hành động. Data contract mô tả các trường, kiểu và quy tắc mà bên gọi có thể dựa vào.",
            ["Endpoint là địa chỉ gửi yêu cầu. Phương thức HTTP mô tả hành động; mã trạng thái cho biết kết quả xử lý.",
             "JSON chứa các trường có tên và giá trị. Contract quy định trường bắt buộc, kiểu dữ liệu và ý nghĩa của giá trị thiếu.",
             "Pagination chia kết quả thành nhiều trang. Retry gửi lại yêu cầu lỗi; idempotency nghĩa là lặp thao tác không tạo thêm tác động."],
            "Công ty giao hàng lấy đơn từ API cửa hàng theo từng trang, thử lại khi lỗi tạm thời và lưu mỗi đơn đúng một lần vào cơ sở dữ liệu riêng.",
            ["Trao đổi dữ liệu giữa hệ thống mà không cần truy cập trực tiếp cơ sở dữ liệu của nhau.", "Nạp dữ liệu đáng tin cậy khi response bị chia trang, chậm, thiếu hoặc tạm thời không truy cập được."],
            "Data QA xem response HTTP thật và đối soát khóa trả về với bản ghi đã lưu. HTTP 200 chưa chứng minh đủ mọi trang hay mọi trường bắt buộc.",
            "Các bài học kiểm tra contract JSON/mã trạng thái, pagination đầy đủ, retry có giới hạn và nạp HTTP vào PostgreSQL không trùng khi chạy lại, qua HTTP playground local."),
    },
    "fabric-testing": {
        "ENG": _entry(
            "Microsoft Fabric brings data collection, preparation, analysis and reporting into one shared platform. Teams can work on the same data instead of building a separate connection for every analytics tool.",
            ["A workspace groups related items and team access. OneLake provides shared data storage.",
             "A lakehouse holds files and tables; a warehouse organizes data for SQL analysis. Pipelines move data, and notebooks can transform it.",
             "Power BI presents reports. Bronze, Silver and Gold are common names for raw, cleaned and business-ready data layers."],
            "A supermarket collects sales into Bronze, cleans product codes in Silver and publishes daily revenue in Gold for a Power BI dashboard.",
            ["Coordinate data engineering and reporting around shared datasets.", "Trace which upstream load produced a report and where a schema or amount changed across layers."],
            "Data QA follows run IDs and dependencies, checks schema agreements and reconciles layer keys and amounts before trusting a dashboard.",
            "The three lessons investigate lineage, schema drift and layer reconciliation using local PostgreSQL simulations or imported evidence. They do not connect to live Fabric."),
        "VIE": _entry(
            "Microsoft Fabric tập hợp việc thu thập, chuẩn bị, phân tích và báo cáo dữ liệu trong một nền tảng chung. Các nhóm có thể dùng cùng dữ liệu thay vì xây kết nối riêng cho từng công cụ phân tích.",
            ["Workspace nhóm các tài nguyên liên quan và quyền truy cập của nhóm. OneLake cung cấp nơi lưu dữ liệu chung.",
             "Lakehouse chứa tệp và bảng; warehouse tổ chức dữ liệu để phân tích bằng SQL. Pipeline di chuyển dữ liệu, còn notebook có thể biến đổi dữ liệu.",
             "Power BI trình bày báo cáo. Bronze, Silver và Gold thường chỉ các lớp dữ liệu thô, đã làm sạch và sẵn sàng cho nghiệp vụ."],
            "Siêu thị thu doanh số vào Bronze, chuẩn hóa mã sản phẩm ở Silver rồi xuất doanh thu ngày ở Gold cho dashboard Power BI.",
            ["Phối hợp xử lý dữ liệu và báo cáo dựa trên bộ dữ liệu chung.", "Truy ngược báo cáo về đợt nạp nguồn và xác định lớp nào đã đổi schema hoặc số tiền."],
            "Data QA theo run ID và dependency, kiểm tra hợp đồng schema, đối soát khóa và số tiền giữa các lớp trước khi tin dashboard.",
            "Ba bài học điều tra lineage, schema drift và đối soát layer qua mô phỏng PostgreSQL local hoặc evidence nhập từ tệp. Các bài không kết nối Fabric thật."),
    },
    "adf-testing": {
        "ENG": _entry(
            "Azure Data Factory (ADF) is a service for moving data and coordinating processing steps. Think of it as a timetable and coordinator for jobs that must run in the right order.",
            ["A pipeline groups activities such as copying data or invoking processing. Dependencies say which activity must finish first.",
             "Linked services describe connections, datasets describe the data to read or write, and an integration runtime provides the execution environment.",
             "Triggers start work on a schedule or event. Run/activity records show outcomes; watermarks mark the boundary of changes already processed."],
            "A company schedules a nightly database-to-lake copy, waits for it to finish, then builds a report. After a failure it resumes from a recorded checkpoint.",
            ["Automate movement between different storage systems and coordinate dependent jobs.", "Track incremental copies and recover failed workflows without silently skipping or duplicating changes."],
            "Data QA compares copy metrics with actual records, checks watermark boundaries and proves that downstream publication waited for valid upstream data.",
            "The three lessons validate copy evidence, late-arrival/replay behavior and dependency recovery with local simulations or file imports. No live ADF factory is required."),
        "VIE": _entry(
            "Azure Data Factory (ADF) là dịch vụ di chuyển dữ liệu và điều phối các bước xử lý. Có thể hình dung nó như lịch trình và người điều phối để các job chạy đúng thứ tự.",
            ["Pipeline nhóm các activity như sao chép dữ liệu hoặc gọi bước xử lý. Dependency cho biết activity nào phải hoàn tất trước.",
             "Linked service mô tả kết nối, dataset mô tả dữ liệu cần đọc hoặc ghi, còn integration runtime cung cấp môi trường thực thi.",
             "Trigger khởi chạy theo lịch hoặc sự kiện. Bản ghi run/activity cho biết kết quả; watermark đánh dấu ranh giới thay đổi đã xử lý."],
            "Công ty lên lịch copy dữ liệu từ database vào lake mỗi đêm, đợi copy xong mới tạo báo cáo. Nếu lỗi, luồng tiếp tục từ checkpoint đã ghi.",
            ["Tự động di chuyển dữ liệu giữa các nơi lưu trữ và phối hợp các job phụ thuộc nhau.", "Theo dõi copy incremental và khôi phục luồng lỗi mà không âm thầm bỏ sót hoặc nhân đôi thay đổi."],
            "Data QA so sánh chỉ số copy với bản ghi thật, kiểm tra ranh giới watermark và chứng minh bước xuất đích đã chờ nguồn hợp lệ.",
            "Ba bài học kiểm tra evidence copy, dữ liệu đến muộn/replay và khôi phục dependency qua mô phỏng local hoặc tệp nhập. Không cần factory ADF thật."),
    },
    "onelake-testing": {
        "ENG": _entry(
            "OneLake is Microsoft Fabric's shared logical data lake: a common place to organize and access analytical data across teams. Storage is shared, while access still depends on permissions.",
            ["Workspaces and items organize files and tables. A partition groups data, often by a date such as the sales day.",
             "A shortcut points to data in another location so it can be accessed without making a separate full copy.",
             "A file manifest lists expected files or partitions. A refresh timestamp describes data age; seeing a file does not prove its contents are complete or current."],
            "Regional stores share daily sales partitions. A reporting team uses a shortcut to product reference data, but yesterday's missing partition or an old reference can distort today's report.",
            ["Reuse analytical data across teams while reducing separate copies and isolated storage.", "Organize large datasets into manageable partitions and locate shared reference data."],
            "Data QA checks expected partition coverage, duplicate file keys and reference freshness against a stated deadline, including missing and future timestamps.",
            "The two lessons examine partition manifests and reference freshness using local evidence. They do not read live OneLake files or resolve real shortcuts."),
        "VIE": _entry(
            "OneLake là data lake logic dùng chung của Microsoft Fabric: nơi chung để tổ chức và truy cập dữ liệu phân tích giữa các nhóm. Dữ liệu được dùng chung nhưng quyền truy cập vẫn được kiểm soát.",
            ["Workspace và item tổ chức tệp và bảng. Partition nhóm dữ liệu, thường theo ngày như ngày bán hàng.",
             "Shortcut trỏ tới dữ liệu ở vị trí khác để có thể truy cập mà không cần tạo một bản sao đầy đủ riêng.",
             "File manifest liệt kê tệp hoặc partition mong đợi. Thời điểm refresh cho biết tuổi dữ liệu; thấy tệp chưa chứng minh nội dung đủ hoặc còn mới."],
            "Các cửa hàng vùng chia sẻ partition doanh số theo ngày. Nhóm báo cáo dùng shortcut tới dữ liệu sản phẩm, nhưng thiếu partition hôm qua hoặc reference cũ có thể làm sai báo cáo hôm nay.",
            ["Tái sử dụng dữ liệu phân tích giữa các nhóm, giảm bản sao riêng và nơi lưu trữ tách biệt.", "Chia bộ dữ liệu lớn thành partition dễ quản lý và tìm dữ liệu tham chiếu dùng chung."],
            "Data QA kiểm tra đủ partition mong đợi, khóa tệp trùng và độ mới reference theo hạn đã định, kể cả timestamp thiếu hoặc nằm trong tương lai.",
            "Hai bài học xem manifest partition và freshness reference qua evidence local. Chúng không đọc tệp OneLake thật hay phân giải shortcut thật."),
    },
    "azure-testing": {
        "ENG": _entry(
            "Azure Data Platform is a way to describe a data solution built from Azure services, rather than one single product. You choose connected services to collect, store, process and serve data.",
            ["Storage such as Azure Data Lake Storage keeps files; databases and warehouses serve structured queries.",
             "Orchestration schedules work, processing engines transform data, and reports help people use the results.",
             "Identity and access controls decide who can read or change data. Monitoring and governance track health, ownership and how data moves."],
            "A logistics company lands delivery files in a lake, processes them into warehouse tables and publishes a daily late-delivery report with access limited to the right teams.",
            ["Design an end-to-end data path across storage, processing and reporting services.", "Choose clear interfaces and responsibilities so teams can diagnose failures and control access."],
            "Data QA checks boundaries between services: did every delivery arrive, were identifiers preserved, and can the report be traced to the correct source and refresh time?",
            "The two runnable local lessons reconcile expected file paths and routes, then investigate access observations. They build on OneLake completeness and SQL reconciliation while separating denied access from data defects. No live Azure authorization is evaluated."),
        "VIE": _entry(
            "Azure Data Platform là cách gọi một giải pháp dữ liệu ghép từ các dịch vụ Azure, không phải một sản phẩm duy nhất. Bạn chọn và kết nối dịch vụ để thu thập, lưu, xử lý và cung cấp dữ liệu.",
            ["Nơi lưu trữ như Azure Data Lake Storage giữ tệp; database và warehouse phục vụ truy vấn dữ liệu có cấu trúc.",
             "Orchestration lên lịch công việc, engine xử lý biến đổi dữ liệu và báo cáo giúp người dùng khai thác kết quả.",
             "Identity và quyền truy cập quyết định ai được đọc hoặc sửa. Monitoring và governance theo dõi sức khỏe, trách nhiệm quản lý và luồng dữ liệu."],
            "Công ty logistics nhận tệp giao hàng vào lake, xử lý thành bảng warehouse và xuất báo cáo giao trễ hằng ngày, chỉ cho các nhóm phù hợp truy cập.",
            ["Thiết kế đường đi dữ liệu xuyên suốt nơi lưu trữ, xử lý và báo cáo.", "Chọn giao diện và trách nhiệm rõ ràng để các nhóm tìm nguyên nhân lỗi và kiểm soát truy cập."],
            "Data QA kiểm tra ranh giới giữa dịch vụ: đã nhận đủ chuyến giao chưa, ID có được giữ đúng không và có truy ngược báo cáo về nguồn cùng thời điểm refresh không?",
            "Hai bài local chạy được đối soát path/route file kỳ vọng rồi điều tra observation truy cập. Bài học nối kiến thức completeness OneLake và đối soát SQL, tách denied access khỏi lỗi dữ liệu. Không đánh giá cấp quyền Azure thật."),
    },
    "databricks-testing": {
        "ENG": _entry(
            "Databricks is a platform for working with data in a lakehouse: combining file-based lake storage with managed tables for analysis. Teams write and run processing code together on large datasets.",
            ["Notebooks combine code and explanations; jobs run processing steps repeatedly. SQL and Spark are ways to query or transform data.",
             "Delta Lake adds a transaction log to tables so changes and versions can be tracked reliably.",
             "Bronze, Silver and Gold organize raw, cleaned and business-ready data. A catalog manages discovery and access to datasets."],
            "A transport company combines millions of vehicle events with trip records, removes repeated events and publishes daily distance totals for analysts.",
            ["Process large or continuously arriving datasets and collaborate on repeatable transformations.", "Maintain reliable table updates and inspect versions when a transformation changes a business metric."],
            "Data QA proves transformation rules, event uniqueness and the meaning of a row at each layer, then compares versions to detect lost or unexpectedly changed records.",
            "Two runnable PostgreSQL simulations account for accepted/rejected/quarantined records and compare version-aware before/after snapshots. They extend SQL grain and ETL replay skills; they do not run Spark or reproduce Delta Lake transactions or time travel."),
        "VIE": _entry(
            "Databricks là nền tảng làm việc với dữ liệu trong lakehouse: kết hợp nơi lưu tệp của data lake với các bảng được quản lý để phân tích. Các nhóm cùng viết và chạy mã xử lý trên bộ dữ liệu lớn.",
            ["Notebook kết hợp mã và giải thích; job chạy lặp các bước xử lý. SQL và Spark giúp truy vấn hoặc biến đổi dữ liệu.",
             "Delta Lake bổ sung nhật ký giao dịch cho bảng để theo dõi thay đổi và phiên bản đáng tin cậy.",
             "Bronze, Silver và Gold tổ chức dữ liệu thô, đã làm sạch và sẵn sàng cho nghiệp vụ. Catalog quản lý việc tìm và truy cập bộ dữ liệu."],
            "Công ty vận tải kết hợp hàng triệu sự kiện xe với thông tin chuyến đi, loại sự kiện lặp và xuất tổng quãng đường ngày cho nhóm phân tích.",
            ["Xử lý bộ dữ liệu lớn hoặc đến liên tục và cộng tác trên các phép biến đổi có thể chạy lại.", "Cập nhật bảng đáng tin cậy và xem phiên bản khi phép biến đổi làm thay đổi chỉ số nghiệp vụ."],
            "Data QA chứng minh quy tắc biến đổi, tính duy nhất của sự kiện và ý nghĩa một hàng ở từng lớp, rồi so sánh phiên bản để phát hiện mất hoặc đổi bản ghi ngoài ý muốn.",
            "Hai mô phỏng PostgreSQL chạy được đối soát dòng accepted/rejected/quarantined và snapshot before/after theo version. Bài nối kỹ năng grain SQL và replay ETL; không chạy Spark hoặc tái tạo transaction hay time travel Delta Lake."),
    },
    "synapse-testing": {
        "ENG": _entry(
            "Azure Synapse Analytics brings warehouse queries, large-scale processing and data integration into one analytics workspace. It helps teams turn stored business data into reports and investigations.",
            ["SQL pools support warehouse analysis; serverless SQL can query supported data in lake files without a dedicated SQL pool.",
             "Spark pools process large datasets. Pipelines coordinate movement and processing, while Synapse Studio is the workspace for these tasks.",
             "Fact tables record events such as sales; dimension tables describe customers or products. Their keys and grain determine whether a report's totals are meaningful."],
            "An insurer combines policy and claims data, builds warehouse facts and dimensions, then calculates claims totals by region without counting one claim several times.",
            ["Analyze warehouse and lake data and coordinate the preparation needed for business reporting.", "Create shared analytical models when raw operational tables are difficult to query directly."],
            "Data QA checks fact/dimension joins, missing keys, totals and load freshness, and reconciles published warehouse results with operational sources.",
            "Two runnable local lessons validate staging-to-fact publication with dimension keys and reporting grain with independent totals. They build on JOIN and ETL reconciliation; PostgreSQL does not reproduce dedicated/serverless Synapse execution or its distributed architecture."),
        "VIE": _entry(
            "Azure Synapse Analytics tập hợp truy vấn warehouse, xử lý dữ liệu lớn và tích hợp dữ liệu trong một workspace phân tích. Nó giúp các nhóm biến dữ liệu nghiệp vụ đã lưu thành báo cáo và thông tin điều tra.",
            ["SQL pool hỗ trợ phân tích warehouse; serverless SQL truy vấn dữ liệu được hỗ trợ trong tệp lake mà không cần SQL pool chuyên dụng.",
             "Spark pool xử lý bộ dữ liệu lớn. Pipeline điều phối việc di chuyển và xử lý, còn Synapse Studio là nơi làm các công việc này.",
             "Bảng fact ghi sự kiện như bán hàng; bảng dimension mô tả khách hoặc sản phẩm. Khóa và grain quyết định tổng trong báo cáo có đúng ý nghĩa không."],
            "Công ty bảo hiểm gộp dữ liệu hợp đồng và bồi thường, xây fact/dimension warehouse rồi tính tổng bồi thường theo vùng mà không đếm một yêu cầu nhiều lần.",
            ["Phân tích dữ liệu warehouse và lake, điều phối việc chuẩn bị dữ liệu cho báo cáo nghiệp vụ.", "Tạo mô hình phân tích chung khi các bảng vận hành thô khó truy vấn trực tiếp."],
            "Data QA kiểm tra JOIN fact/dimension, khóa thiếu, tổng và độ mới của đợt nạp; đối soát kết quả warehouse đã xuất với nguồn vận hành.",
            "Hai bài local chạy được kiểm tra publication staging-to-fact với key dimension và grain báo cáo theo tổng độc lập. Bài nối JOIN và đối soát ETL; PostgreSQL không tái tạo thực thi Synapse dedicated/serverless hay kiến trúc phân tán."),
    },
}


def introduction(course_id, subject_title, language):
    content = INTRODUCTIONS[course_id]["ENG" if language == "ENG" else "VIE"]
    return {
        "what_title": f"What is {subject_title}?" if language == "ENG" else f"{subject_title} là gì?",
        "uses_title": "What is it used for?" if language == "ENG" else "Dùng để làm gì?",
        **content,
    }
