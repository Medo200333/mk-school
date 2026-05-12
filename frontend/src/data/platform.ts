export type PlatformModule = {
  code: string;
  title: string;
  scope: string;
  description: string;
  href: string;
  status: string;
  badge: string;
  metrics: string[];
  responsibilities: string[];
};

export const platformModules: PlatformModule[] = [
  {
    code: "core",
    title: "النواة المشتركة",
    scope: "Core Platform",
    description: "المؤسسات، المستخدمون، الصلاحيات، الوثائق، التدقيق، الإعدادات، وسجل التحديثات.",
    href: "/platform",
    status: "جاهز",
    badge: "Core",
    metrics: ["organizations", "users", "documents", "modules"],
    responsibilities: ["هوية موحدة", "صلاحيات مركزية", "Audit", "Migration Registry"]
  },
  {
    code: "hr",
    title: "برنامج الموظفين",
    scope: "HR / Employee Program",
    description: "الموظفون، المدرسون، الأقسام، الوظائف، الحضور، الإجازات، المرتبات، العقود، والأداء.",
    href: "/hr",
    status: "مخطط البيانات جاهز",
    badge: "HR",
    metrics: ["employees", "teachers", "attendance_records", "leave_requests"],
    responsibilities: ["ملف موظف", "ربط المدرسين بالجدول", "حضور وانصراف", "إجازات ومرتبات"]
  },
  {
    code: "school",
    title: "برنامج المدارس",
    scope: "School Program",
    description: "المعاهد، المراحل، الصفوف، الفصول، الطلاب، أولياء الأمور، المواد، والقاعات.",
    href: "/school",
    status: "مخطط البيانات جاهز",
    badge: "School",
    metrics: ["institutes", "students", "guardians", "classrooms"],
    responsibilities: ["معاهد ومدارس", "طلاب وفصول", "أولياء أمور", "قاعات ومراحل"]
  },
  {
    code: "timetable",
    title: "الجدول المدرسي",
    scope: "School Timetable",
    description: "الأيام، الحصص، المدرسون، القاعات، الفصول، المواد، نصاب المدرس، ومنع التعارض.",
    href: "/timetable",
    status: "تشغيل فعلي",
    badge: "Timetable",
    metrics: ["days", "periods", "subjects", "curriculum_plans", "lessons", "generation_runs", "conflicts"],
    responsibilities: ["Curriculum Matrix", "Hard/Soft Constraints", "Generation Center", "Quality Score", "Approval/Publication"]
  },
  {
    code: "education-control",
    title: "برنامج الكنترول",
    scope: "Education Control",
    description: "اللجان، أرقام الجلوس، الرصد، النتائج، الدور الثاني، التفعيل، والتقارير.",
    href: "/education-control",
    status: "بدأ التنفيذ",
    badge: "Control",
    metrics: ["subjects", "committees", "scores", "results"],
    responsibilities: ["مواد ورصد", "لجان وأرقام جلوس", "نتائج وترتيب", "دور ثاني"]
  },
  {
    code: "access-mirror",
    title: "مرآة Access",
    scope: "Access Mirror",
    description: "حفظ جداول Access كاملة كمرجع خام قبل التحويل إلى جداول التشغيل المنظمة.",
    href: "/access-mirror",
    status: "بدأ التنفيذ",
    badge: "Raw Mirror",
    metrics: ["batches", "snapshots"],
    responsibilities: ["Raw Mirror", "قاموس أعمدة", "عينات صفوف", "Mapping Rules"]
  },
  {
    code: "operations",
    title: "التشغيل والتقارير",
    scope: "Operations",
    description: "السكانر، الاستيراد، الإحصائيات، الطباعة، التصدير، اللقطات، وFeature Flags.",
    href: "/operations",
    status: "مخطط البيانات جاهز",
    badge: "Ops",
    metrics: ["import_jobs", "reports", "feature_flags", "scanner_batches"],
    responsibilities: ["استيراد", "سكانر", "تقارير", "Snapshot"]
  }
];

export function findPlatformModule(code: string) {
  return platformModules.find((module) => module.code === code);
}
