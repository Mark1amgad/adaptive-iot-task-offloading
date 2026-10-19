# Google Cluster Data — Borg workload traces v3

## الحالة

هذه الصفحة مبنية على نتائج تحقق موثقة. لا تعني الإشارة إلى ملف في ورقة أو README أن الملف فُحص، ويظهر مستوى الفحص صراحةً أدناه.

## المصدر والمؤسسة

- الاسم الرسمي: Google Cluster Data — Borg workload traces v3
- المؤسسة/الجامعة: غير متحقق منه
- المنطقة: خلايا Google/Borg؛ الموقع الجغرافي/الدولة غير متحققين.
- فترة الجمع: v3: مايو 2019 في ثماني خلايا Borg. v2.1: مايو 2011، خلية واحدة ونحو 12.5 ألف آلة و29 يومًا. v1: سبع ساعات في 2009.
- سنة النشر/الإيداع: إتاحة/وصف v3 وورقة Borg: The Next Generation في 2020؛ الجمع 2019.
- طبيعة البيانات: أثر تشغيل فعلي لنظام إدارة Borg: أحداث تقديم وجدولة وإنهاء/إخلاء، طلبات موارد واستخدام CPU/ذاكرة. الاستخدام ضمن نوافذ غالبًا خمس دقائق مع عينات تقريبية كل ثانية. بعض القيم محجوبة/مطبعة لأسباب السرية.
- الترخيص: CC BY 4.0 بحسب المستودع ووثيقة v3.

## الروابط

- المصدر الرسمي: https://github.com/google/cluster-data
- رابط التنزيل: غير متحقق منه

## طريقة الجمع والملفات

أثر تشغيل فعلي لنظام إدارة Borg: أحداث تقديم وجدولة وإنهاء/إخلاء، طلبات موارد واستخدام CPU/ذاكرة. الاستخدام ضمن نوافذ غالبًا خمس دقائق مع عينات تقريبية كل ثانية. بعض القيم محجوبة/مطبعة لأسباب السرية.

- خمسة جداول JSON مضغوطة gzip أو BigQuery: collection_events (أحداث المجموعة، الزمن، النوع، المستخدم، scheduler وحقول أخرى)، instance_events (أحداث المهمة، machine_id، resource_request، constraint)، machine_events (capacity وswitch/platform)، machine_attributes (name/value)، instance_usage (CPU distributions/usage وassigned_memory وحقول usage أخرى).
- نُزّلت وفُحصت ملفات schema JSON الخمسة من GCS؛ لم تُقرأ صفوف بيانات.
- ملفات مساعدة في المستودع تشمل proto ودفاتر تحليل ووثائق ETA وPowerData2019 المنفصلة؛ ليست جداول workload v3 المفحوصة.

## حالة التنزيل والفحص

لم يُنزّل shard بيانات. فحص HEAD لملف instance_usage أظهر HTTP 200 وحجمًا معلنًا 498,371,634 بايتًا لذلك الشارد وحده. وثيقة Google تذكر نحو 2.4 TiB مضغوطة. schemas فقط هي التي نُزلت وفُحصت؛ استعلام BigQuery لم يُختبر.

غير متحقق منه

## الاستخدام في المشروع

- قراءة BigQuery أو JSON.gz مع الحفاظ على SUBMIT/SCHEDULE/EVICT/FAIL/FINISH، وربط instance_events بالاستخدام التاريخي.
- يمكن ربط resource_request وusage وmachine capacity بموارد عقد افتراضية، مع توثيق وحدات الموارد المطبعة.
- لا تعتبر machine_id نموذج شبكة MEC أو قرار offloading؛ أضف أحجام المهام والمهل والشبكة والطاقة والمواقع والحركة من مصدر مستقل/افتراض معلن.
- تحليل فترة/خلية صغيرة أولًا بسبب الحجم؛ قارن إعادة تشغيل التخصيصات التاريخية دون وصفها بأنها MEC.

## التوصية

قوي لأبحاث أحمال وجدولة وموارد مراكز البيانات الحقيقية؛ غير مناسب وحده لبيانات IoT/MEC أو تدريب/تقييم task offloading.

## المصادر والأبحاث



- https://github.com/google/cluster-data
- https://github.com/google/cluster-data/blob/master/ClusterData2019.md
- https://raw.githubusercontent.com/google/cluster-data/master/clusterdata_trace_format_v3.proto
- https://storage.googleapis.com/clusterdata_2019_schema/collection_events.schema.json
- https://storage.googleapis.com/clusterdata_2019_schema/instance_events.schema.json
- https://storage.googleapis.com/clusterdata_2019_schema/machine_events.schema.json
- https://storage.googleapis.com/clusterdata_2019_schema/machine_attributes.schema.json
- https://storage.googleapis.com/clusterdata_2019_schema/instance_usage.schema.json
- https://doi.org/10.1145/3342195.3387517
- https://creativecommons.org/licenses/by/4.0/
