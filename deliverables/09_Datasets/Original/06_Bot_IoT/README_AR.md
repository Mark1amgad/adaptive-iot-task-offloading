# The Bot-IoT Dataset

## الحالة

هذه الصفحة مبنية على نتائج تحقق موثقة. لا تعني الإشارة إلى ملف في ورقة أو README أن الملف فُحص، ويظهر مستوى الفحص صراحةً أدناه.

## المصدر والمؤسسة

- الاسم الرسمي: The Bot-IoT Dataset
- المؤسسة/الجامعة: غير متحقق منه
- المنطقة: كانبيرا، أستراليا؛ UNSW Canberra Cyber / Cyber Range Lab.
- فترة الجمع: تاريخ/فترة تقويمية غير متحقق؛ الورقة تذكر 16 ساعة للحركة السليمة والهجمات ضمن تجارب منفصلة.
- سنة النشر/الإيداع: ورقة المجلة وسجل IEEE DataPort في 2019؛ صفحة UNSW آخر تحديث مذكور 2021.
- طبيعة البيانات: testbed افتراضي/مختبري في Cyber Range؛ خمس خدمات منزل ذكي موصوفة بأنها محاكاة Node-RED، حركة عادية مولدة بـOstinato وهجمات من Kali؛ التقطت الحركة فعليًا ثم اشتقت التدفقات. لا يمثل قياسًا ميدانيًا لأجهزة IoT منشورة.
- الترخيص: صفحة UNSW تذكر استخدامًا أكاديميًا مجانيًا، واستخدامًا تجاريًا يتطلب اتفاقًا مع المؤلفين؛ لم يُتحقق من ترخيص مفتوح معياري.

## الروابط

- المصدر الرسمي: https://research.unsw.edu.au/projects/bot-iot-dataset
- رابط التنزيل: غير متحقق منه

## طريقة الجمع والملفات

testbed افتراضي/مختبري في Cyber Range؛ خمس خدمات منزل ذكي موصوفة بأنها محاكاة Node-RED، حركة عادية مولدة بـOstinato وهجمات من Kali؛ التقطت الحركة فعليًا ثم اشتقت التدفقات. لا يمثل قياسًا ميدانيًا لأجهزة IoT منشورة.

- SharePoint يبين مجلدات PCAPs وGround Truth وDataset وARGUS، وملفي PDF؛ أسماء الملفات الداخلية لم تُفحص.
- الوصف يذكر PCAP نحو 69.3 GB وأكثر من 72 مليون سجل، CSV تدفقات 16.7 GB؛ عينة 5% أربعة ملفات نحو 1.07 GB.
- ملف DataPort المفهرس UNSW_2018_IoT_Botnet_Full5pc_1.csv بحجم 259.72 MB يتطلب دخولًا وفق الوصف؛ لم يُنزّل.
- أعمدة منشورة في الورقة: pkSeqID, Stime, flgs, Proto, saddr, sport, daddr, dport, pkts, bytes, state, ltime, dur, mean, stddev, sum, min, max, spkts, dpkts, sbytes, dbytes, rate, srate, drate, attack, category, subcategory وغيرها؛ لم تُفحص ملفات CSV فعليًا.

## حالة التنزيل والفحص

فُحصت الصفحة الرسمية والورقة وفهرس SharePoint؛ لم يُنزّل أو يُفحص أي PCAP/CSV/Argus. إمكانية التنزيل الفعلي من SharePoint دون تسجيل دخول غير متحققة؛ DataPort يتطلب دخولًا/اشتراكًا بحسب الوصف.

غير متحقق منه

## الاستخدام في المشروع

- يمكن إعادة تشغيل أنماط حركة/هجمات أو استخدام Stime وbytes كـproxy مشتق لحركة الشبكة بعد فحص الملف، لا كمهام حقيقية.
- توليد CPU/deadlines/energy/المواقع وقرار offloading في نموذج مستقل معلن؛ افصل نتائج المحاكاة عن بيانات Bot-IoT.

## التوصية

مناسب لكشف التسلل وتحليل حركة IoT في testbed؛ غير مناسب كبيانات حقيقة لتقييم task offloading.

## المصادر والأبحاث



- https://research.unsw.edu.au/projects/bot-iot-dataset
- https://unsw-my.sharepoint.com/:f:/g/personal/z5131399_ad_unsw_edu_au/EjlBDf2KODxPgXmqbO3MxxsBBVARCKZxGUG47OiFHb_AnQ
- https://ieee-dataport.org/documents/bot-iot-dataset
- https://doi.org/10.1016/j.future.2019.05.041
- https://arxiv.org/abs/1811.00701
