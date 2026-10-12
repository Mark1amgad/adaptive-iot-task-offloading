# Image Recognition Task Execution Times in Mobile Edge Computing

## الحالة

هذه الصفحة مبنية على نتائج تحقق موثقة. لا تعني الإشارة إلى ملف في ورقة أو README أن الملف فُحص، ويظهر مستوى الفحص صراحةً أدناه.

## المصدر والمؤسسة

- الاسم الرسمي: Image Recognition Task Execution Times in Mobile Edge Computing
- المؤسسة/الجامعة: غير متحقق منه
- المنطقة: موقع القياس غير متحقق؛ مقدمو المجموعة مرتبطون بجامعة Glasgow وفق UCI.
- فترة الجمع: 26 نوفمبر 2020؛ طوابع CSV تقريبًا 13:05–17:03 وفق الوقت المكتوب.
- سنة النشر/الإيداع: غير متحقق منه
- طبيعة البيانات: قياس تنفيذ مهمة تعرف صور باستخدام ImageAI.Prediction على MacBook Pro 1 و2 وUbuntu VM على VirtualBox وRaspberry Pi 4B. العميل الطرفي المتنقل ممثل بعملية محاكاة؛ الحمل بوتيرة مضبوطة. قياسات فعلية في إعداد تجريبي، لا أثر شبكة جوال ميداني.
- الترخيص: CC BY 4.0 وفق صفحة UCI.

## الروابط

- المصدر الرسمي: https://archive.ics.uci.edu/dataset/859/image+recognition+task+execution+times+in+mobile+edge+comput
- رابط التنزيل: غير متحقق منه

## طريقة الجمع والملفات

قياس تنفيذ مهمة تعرف صور باستخدام ImageAI.Prediction على MacBook Pro 1 و2 وUbuntu VM على VirtualBox وRaspberry Pi 4B. العميل الطرفي المتنقل ممثل بعملية محاكاة؛ الحمل بوتيرة مضبوطة. قياسات فعلية في إعداد تجريبي، لا أثر شبكة جوال ميداني.

- الأرشيف الخارجي TATDescriptionDataset.zip ويحتوي أرشيفًا داخليًا؛ الملف DatasetExpeirmentalDescription.pdf (التهجئة كما في الملف).
- MacBookPro1.csv، MacBookPro2.csv، VM.csv، RasberryPi.csv (تهجئة كما في الملف)، كل منها 1,000 صف وعمودان فعليان: Time, Execution Time؛ 4,000 سجل إجمالًا.
- وصف التجربة: صورة ترسل كل ثانية؛ Execution Time هو زمن الدوران من بدء نقل الصورة حتى وصول نتيجة التعرف، بحسب وصف التجربة. لا task ID أو حجم input.

## حالة التنزيل والفحص

مكتمل: نُزّل وفُك الأرشيف الرسمي؛ فُحص PDF وCSV الأربعة؛ 1,000 سجل لكل ملف. Execution Time المرصود في المجموعة المفحوصة نحو 0.093–20.789 ثانية وفق النتائج المقدمة.

غير متحقق منه

## الاستخدام في المشروع

- استيراد الملفات كآثار زمنية لكل نوع خادم؛ استخدام Time كتوقيت حمل مع التصريح بأن إيقاع الإرسال كل ثانية من وصف التجربة.
- استخدام Execution Time كزمن دوران شامل أو لمعايرة توزيع latency؛ لا تجمعه مع مكونات شبكة/معالجة أخرى إذا أدى ذلك إلى عد مزدوج.
- لا تستنتج حجم صورة أو CPU cycles أو bandwidth أو مواقع؛ إذا لزم إدخال هذه الحقول في EdgeCloudSim فأنشئ افتراضات منفصلة ووسمها اصطناعية.
- قرارات الخادم التي ينتجها EdgeOrchestrator محاكاة جديدة وليست labels في UCI.

## التوصية

الرئيسية لمعايرة/مقارنة زمن دوران مهمة تعرف صور عبر أربعة أنواع خادم، لا كبيانات كاملة لتدريب أو اختبار task offloading.

## المصادر والأبحاث



- https://archive.ics.uci.edu/dataset/859/image+recognition+task+execution+times+in+mobile+edge+comput
- https://archive.ics.uci.edu/static/public/859/image+recognition+task+execution+times+in+mobile+edge+computing.zip
- https://doi.org/10.24432/C5N617
- https://doi.org/10.1109/WD.2019.8734210
- https://eprints.gla.ac.uk/179591/
- https://creativecommons.org/licenses/by/4.0/legalcode
