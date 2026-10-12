# EUA Dataset — Edge Users Allocation

## الحالة

هذه الصفحة مبنية على نتائج تحقق موثقة. لا تعني الإشارة إلى ملف في ورقة أو README أن الملف فُحص، ويظهر مستوى الفحص صراحةً أدناه.

## المصدر والمؤسسة

- الاسم الرسمي: EUA Dataset — Edge Users Allocation
- المؤسسة/الجامعة: غير متحقق منه
- المنطقة: أستراليا؛ ملفات على مستوى البلاد وأخرى لـMelbourne CBD وMelbourne metropolitan. Swinburne Edge / Swinburne University of Technology؛ مصادر المواقع ACMA وAPNIC وIP-API.
- فترة الجمع: فترة موحدة غير متحقق منها. README ينسب ملف كتل IP الأسترالية إلى APNIC بتاريخ 08/05/2018؛ اصطلاح التاريخ وتاريخ بقية الملفات غير مثبتين. ليست سلسلة زمنية.
- سنة النشر/الإيداع: الورقة الأصلية 2018؛ أنشئ مستودع GitHub في 2018-06-05؛ سجل IEEE DataPort منفصل أنشئ في 2026-02-13.
- طبيعة البيانات: إحداثيات محطات الاتصالات من سجل تراخيص الراديو ACMA بوصفها مواقع حافة افتراضية؛ كتل IP من APNIC وعناوين مختارة أُسندت إلى مواقع تقريبية بواسطة IP-API؛ مواقع إضافية مولدة بانتظام حول المواقع المستخرجة. نطاقات التغطية العشوائية 450–750 م والسعات/الأحمال في الورقة افتراضات/تجارب مولدة، لا قياسات فعلية لهذه المتغيرات.
- الترخيص: المستودع يعلن MIT؛ README يوضح أن بيانات ACMA مملوكة لـACMA ويلزم الالتزام بقواعدها. شروط APNIC/IP-API غير محسومة من MIT وحده.

## الروابط

- المصدر الرسمي: https://github.com/PhuLai/eua-dataset
- رابط التنزيل: غير متحقق منه

## طريقة الجمع والملفات

إحداثيات محطات الاتصالات من سجل تراخيص الراديو ACMA بوصفها مواقع حافة افتراضية؛ كتل IP من APNIC وعناوين مختارة أُسندت إلى مواقع تقريبية بواسطة IP-API؛ مواقع إضافية مولدة بانتظام حول المواقع المستخرجة. نطاقات التغطية العشوائية 450–750 م والسعات/الأحمال في الورقة افتراضات/تجارب مولدة، لا قياسات فعلية لهذه المتغيرات.

- edge-servers/site.csv: README يقول 95,562×10؛ الأعمدة SITE_ID,LATITUDE,LONGITUDE,NAME,STATE,LICENSING_AREA_ID,POSTCODE,SITE_PRECISION,ELEVATION,HCIS_L2؛ الحجم نحو 9.76 MB في شجرة GitHub؛ لم يُفحص المحتوى.
- edge-servers/site-optus-melbCBD.csv: 125 سجلًا وفق README؛ فُحص فعليًا؛ 126 سطرًا مع الرأس؛ الرأس SITE_ID,LATITUDE,LONGITUDE,NAME,STATE,LICENSING_AREA_ID,POSTCODE,SITE_PRECISION,ELEVATION,HCIS_L2.
- all-telco-sites-metro.html وall-optus-sites-metro.html: خرائط HTML موصوفة بـ9,318 و1,464 محطة؛ لم تُفحص.
- users/australia-ip-ranges.csv: كتل CIDR؛ لقطة APNIC حتى التاريخ المذكور في README؛ لم تُفحص.
- users/users-aus.csv: 4,748×7 وفق README؛ فُحص الرأس وعينة وعدد الأسطر؛ IP,Latitude,Longitude,PostCode,City,State,Country.
- users/users-melbcbd-generated.csv: 816×2؛ فُحص؛ Latitude,Longitude؛ مواقع مولدة بتوزيع منتظم في Melbourne CBD.
- users/users-melbmetro-generated.csv: 131,312×2 وفق README، نحو 5.10 MB؛ لم يُنزّل/يُفحص.
- users-melbmetro-generated.zip وخرائط HTML موصوفة فقط؛ لم تُفحص.

## حالة التنزيل والفحص

التنزيل العام متحقق جزئيًا: نُزّلت وفُحصت 3 CSV فقط: site-optus-melbCBD.csv وusers-melbcbd-generated.csv وusers-aus.csv. لم يُنزّل المستودع كاملًا ولا الملفات الكبيرة أو خرائط HTML.

غير متحقق منه

## الاستخدام في المشروع

- إسقاط LATITUDE/LONGITUDE إلى إحداثيات محلية بالمتر حول Melbourne؛ تمثيل المحطات كعقد حافة والمستخدمين كأجهزة، دون محول EUA→EdgeCloudSim رسمي أو تخصيص hosts جاهز.
- تهيئة الأجهزة ونقاط الحافة عبر نماذج الموقع/السيناريو؛ إضافة LoadGenerator مستقل لأوقات وصول المهام والأحجام ودورات CPU والمهل، وNetworkModel مستقل للشبكة.
- التغطية قيد مكاني تجريبي فقط، لا بديل عن قياس latency؛ نتائج سياسات EdgeOrchestrator مخرجات محاكاة لا حقائق من EUA.

## التوصية

مناسب بدرجة جيدة للدراسات المكانية/تموضع الحافة أو خريطة أساس لـEdgeCloudSim، وليس وحده لتدريب/اختبار offloading أو المقارنة الكمية في latency/energy/task workload.

## المصادر والأبحاث



- https://github.com/PhuLai/eua-dataset
- https://raw.githubusercontent.com/PhuLai/eua-dataset/master/edge-servers/README.md
- https://raw.githubusercontent.com/PhuLai/eua-dataset/master/users/README.md
- https://raw.githubusercontent.com/PhuLai/eua-dataset/master/LICENSE
- https://doi.org/10.1007/978-3-030-03596-9_15
- https://doi.org/10.1007/978-3-030-33702-5_8
- https://ieee-dataport.org/documents/eua-dataset
- https://www.acma.gov.au/industry/spectrum/radiocomms-licensing/register-radiocommunications-licences/radiocomms-licence-data
