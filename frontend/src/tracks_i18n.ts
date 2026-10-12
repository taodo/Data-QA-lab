import type {Language} from './types';

const ENG={
  title:'Unified QA Learning Platform',eyebrow:'ONE PLATFORM · THREE LEARNING TRACKS',
  intro:'Learn to verify data, understand banking rules and build automation tests. Choose a track, inspect evidence and explain what the results prove.',
  navigation:'Learning tracks',home:'Learning platform',choose:'Choose your learning track',
  approachTitle:'Evidence before conclusions',approach:'A successful request or test run is an observation. Compare it with the requirement and supporting evidence; reading a page does not complete a lesson.',
  data:'Data QA',banking:'Banking QA',automation:'Automation QA',available:'Available',planned:'Planned / Coming Soon',
  dataSummary:'Investigate SQL, ETL, API and cloud data quality with executable labs and observable pipeline evidence.',
  dataTopics:'SQL · ETL · API · Cloud · Pipelines',dataAction:'Explore Data QA',dataCourses:'Data QA courses',
  executableCourses:'executable courses',labs:'labs',
  bankingSummary:'Learn to check accounts, transfers, ledger entries and safe replay against synthetic banking rules.',
  bankingTopics:'Accounts · Transfers · Ledger · Idempotency',bankingAction:'Explore Banking QA',
  bankingIntro:'The Banking learning integration is under development. This track explains the planned learning goals; interactive practice is not available yet.',
  bankingObjectives:'What this track will teach',bankingGoals:[
    'Check API responses and account ownership against explicit requirements.',
    'Reconcile transfer amounts, account changes and paired ledger entries.',
    'Verify idempotency: retrying the same operation must not move money twice.',
    'Validate transactions: related writes must commit together or leave no partial effects.'
  ],simulator:'Banking simulator',simulatorPlan:'Future synthetic account and transfer practice. No live balances, bank login or transfer controls are available here.',
  challenges:'Banking QA challenges',challengesPlan:'Future guided questions and evidence review for API and financial integrity. No challenge execution or completion is recorded here.',
  bankingBoundary:'MiniBanking remains the banking domain project. Its API and database are not connected to this page.',
  automationSummary:'Start with the available automation tutorial, then follow the planned Python, pytest, Playwright and CI learning roadmap.',
  automationTopics:'Python · pytest · Playwright · CI',automationAction:'Explore Automation QA',
  automationIntro:'Read tutorials and review examples here; run Python tests on your own machine. The introductory lesson is available, while the remaining curriculum is planned.',
  openCourse:'View automation course',openLesson:'Read introductory lesson',tutorials:'tutorial lesson',entries:'lesson entries',modules:'modules',
  availableLessons:'available',plannedLessons:'planned',
  automationBoundary:'Independent Automation-QA-Lab framework integration is future work. This page uses the existing platform course; it runs no code and connects to no AI service.',
  progressBoundary:'Tutorial reading and local self-verification are not automatically graded. Tutorial progress is not saved.',
  returnHome:'All learning tracks',loading:'Loading course availability…',unavailable:'Course availability could not be loaded.',retry:'Retry'
};
const VIE:typeof ENG={
  title:'Nền tảng học QA thống nhất',eyebrow:'MỘT NỀN TẢNG · BA LỘ TRÌNH HỌC',
  intro:'Học cách kiểm chứng dữ liệu, hiểu quy tắc banking và xây dựng kiểm thử tự động. Chọn lộ trình, xem bằng chứng và giải thích kết quả chứng minh điều gì.',
  navigation:'Các lộ trình học',home:'Nền tảng học QA',choose:'Chọn lộ trình học của bạn',
  approachTitle:'Có bằng chứng trước khi kết luận',approach:'Request hoặc test chạy thành công mới là một quan sát. Hãy đối chiếu với yêu cầu và bằng chứng; đọc trang không đồng nghĩa với hoàn thành bài.',
  data:'Data QA',banking:'Banking QA',automation:'Automation QA',available:'Sẵn sàng',planned:'Dự kiến / Sắp có',
  dataSummary:'Điều tra chất lượng dữ liệu SQL, ETL, API và cloud qua các lab chạy được và bằng chứng pipeline có thể quan sát.',
  dataTopics:'SQL · ETL · API · Cloud · Pipeline',dataAction:'Khám phá Data QA',dataCourses:'Các khóa Data QA',
  executableCourses:'khóa có lab chạy được',labs:'lab',
  bankingSummary:'Học cách kiểm tra tài khoản, chuyển tiền, bút toán ledger và replay an toàn theo quy tắc banking giả lập.',
  bankingTopics:'Tài khoản · Chuyển tiền · Ledger · Idempotency',bankingAction:'Khám phá Banking QA',
  bankingIntro:'Phần tích hợp học Banking đang được phát triển. Lộ trình này giới thiệu mục tiêu dự kiến; chưa có thực hành tương tác.',
  bankingObjectives:'Bạn sẽ học những gì',bankingGoals:[
    'Kiểm tra response API và quyền sở hữu tài khoản theo yêu cầu rõ ràng.',
    'Đối soát số tiền chuyển, thay đổi từng tài khoản và cặp bút toán ledger.',
    'Kiểm chứng idempotency: retry cùng một thao tác không được chuyển tiền hai lần.',
    'Kiểm tra transaction: các thay đổi liên quan phải cùng commit hoặc không để lại tác động dang dở.'
  ],simulator:'Simulator Banking',simulatorPlan:'Dự kiến thực hành tài khoản và chuyển tiền giả lập. Tại đây chưa có số dư live, đăng nhập ngân hàng hoặc điều khiển chuyển tiền.',
  challenges:'Thử thách Banking QA',challengesPlan:'Dự kiến câu hỏi có hướng dẫn và review bằng chứng API, tính toàn vẹn tài chính. Tại đây không chạy challenge hoặc ghi nhận hoàn thành.',
  bankingBoundary:'MiniBanking vẫn là dự án sở hữu nghiệp vụ banking. API và database của dự án đó chưa kết nối với trang này.',
  automationSummary:'Bắt đầu với tutorial automation đã sẵn sàng, rồi theo lộ trình Python, pytest, Playwright và CI đang dự kiến.',
  automationTopics:'Python · pytest · Playwright · CI',automationAction:'Khám phá Automation QA',
  automationIntro:'Đọc tutorial và review ví dụ tại đây; chạy test Python trên máy của bạn. Bài nhập môn đã sẵn sàng, nội dung còn lại đang dự kiến.',
  openCourse:'Xem khóa automation',openLesson:'Đọc bài nhập môn',tutorials:'bài tutorial',entries:'mục bài học',modules:'module',
  availableLessons:'sẵn sàng',plannedLessons:'dự kiến',
  automationBoundary:'Tích hợp framework từ Automation-QA-Lab độc lập là phần tương lai. Trang này dùng khóa học hiện có của platform; không chạy code hoặc kết nối dịch vụ AI.',
  progressBoundary:'Đọc tutorial và tự kiểm chứng local không được chấm tự động. Tiến độ tutorial chưa được lưu.',
  returnHome:'Tất cả lộ trình học',loading:'Đang tải trạng thái khóa học…',unavailable:'Không tải được trạng thái khóa học.',retry:'Thử lại'
};
export const trackCopy=(language:Language)=>language==='ENG'?ENG:VIE;
export const learningTracks=[{id:'data-qa',key:'data',path:'/learn/data'},{id:'banking-qa',key:'banking',path:'/learn/banking'},{id:'automation-qa',key:'automation',path:'/learn/automation'}] as const;
export type TrackKey=typeof learningTracks[number]['key'];
