# The UNSW-NB15 Dataset

## الحالة

هذه الصفحة مبنية على نتائج تحقق موثقة. لا تعني الإشارة إلى ملف في ورقة أو README أن الملف فُحص، ويظهر مستوى الفحص صراحةً أدناه.

## المصدر والمؤسسة

- الاسم الرسمي: The UNSW-NB15 Dataset
- المؤسسة/الجامعة: غير متحقق منه
- المنطقة: كانبرا، أستراليا؛ UNSW Canberra at ADFA / Cyber Range Lab.
- فترة الجمع: RDA يذكر تاريخ بيانات 2015-09-30؛ نطاق الالتقاط الأوسع غير متحقق.
- سنة النشر/الإيداع: الورقة الأصلية 2015؛ سجل البيانات يذكر إتاحة 2019.
- طبيعة البيانات: IXIA PerfectStorm ولّد مزيجًا من نشاط طبيعي وسلوك هجوم اصطناعي؛ tcpdump التقط 100GB PCAP وفق الصفحة؛ اشتق Argus وBro-IDS خصائص التدفق. مختلط، ولا يثبت حركة IoT أو MEC حية.
- الترخيص: غير محسوم: صفحة UNSW تسمح أكاديميًا وتطلب اتفاقًا/موافقة للاستخدام التجاري؛ سجل RDA يعرض GPL-3.0. لا تفترض تطابق الشرطين.

## الروابط

- المصدر الرسمي: https://research.unsw.edu.au/projects/unsw-nb15-dataset
- رابط التنزيل: غير متحقق منه

## طريقة الجمع والملفات

IXIA PerfectStorm ولّد مزيجًا من نشاط طبيعي وسلوك هجوم اصطناعي؛ tcpdump التقط 100GB PCAP وفق الصفحة؛ اشتق Argus وBro-IDS خصائص التدفق. مختلط، ولا يثبت حركة IoT أو MEC حية.

- صفحة UNSW تصف 4 ملفات UNSW-NB15_1.csv إلى UNSW-NB15_4.csv بإجمالي 2,540,044 سجلًا؛ UNSW-NB15_features.csv (49 خاصية وحقل فئة)، UNSW-NB15_GT.csv، UNSW-NB15_LIST_EVENTS.csv، training-set (175,341) وtesting-set (82,332).
- فهرس SharePoint يعرض مجلدات PCAP وCSV وArgus وBRO وتقارير وReadMe.pdf؛ الملف لم يُفتح.
- رؤوس/أسماء الأعمدة التفصيلية غير متحقق منها لأن CSV لم يُفحص.

## حالة التنزيل والفحص

فُحصت صفحة UNSW وسجل RDA وصفحة IEEE وفهرس SharePoint؛ لم يُنزّل أو يُفتح أي CSV/PCAP أو ReadMe.pdf.

غير متحقق منه

## الاستخدام في المشروع

- بعد تنزيل نسخة وفحص قاموس الخصائص يمكن استخدام خصائص تدفق كملخصات لحركة شبكة فقط، دون مساواتها بحجم مهمة.
- توليد وصول المهام وCPU وdeadline ومواقع/موارد الخوادم من مصدر منفصل معلن؛ لا تستخدم وسوم الهجوم كقرارات offloading.
- افصل قياسات/خصائص المصدر عن المدخلات الاصطناعية ومخرجات المحاكاة.

## التوصية

ليس مجموعة أساسية لـIoT/MEC/offloading؛ قد يصلح لسياق IDS/شبكة بعد فحص الحقول وتسوية الترخيص.

## المصادر والأبحاث



- https://research.unsw.edu.au/projects/unsw-nb15-dataset
- https://unsw-my.sharepoint.com/:f:/g/personal/z5025758_ad_unsw_edu_au/EnuQZZn3XuNBjgfcUu4DIVMBLCHyoLHqOswirpOQifr1ag?e=gKWkLS
- https://ieeexplore.ieee.org/document/7348942
- https://researchdata.edu.au/the-unsw-nb15-dataset/1957529
- https://doi.org/10.26190/5d7ac5b1e8485
- https://www.gnu.org/licenses/gpl-3.0.html
