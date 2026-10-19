# ToN_IoT Datasets

## الحالة

هذه الصفحة مبنية على نتائج تحقق موثقة. لا تعني الإشارة إلى ملف في ورقة أو README أن الملف فُحص، ويظهر مستوى الفحص صراحةً أدناه.

## المصدر والمؤسسة

- الاسم الرسمي: ToN_IoT Datasets
- المؤسسة/الجامعة: غير متحقق منه
- المنطقة: أستراليا؛ مختبرات Cyber Range وIoT في UNSW Canberra.
- فترة الجمع: غير متحقق منه
- سنة النشر/الإيداع: سجل المجموعة 2019؛ ورقة telemetry 2020؛ ورقة شبكة 2021. لا تخلط هذه التواريخ.
- طبيعة البيانات: testbed مختبري شبكي يمثل بيئة IoT/IIoT متوسطة الحجم بطبقات Edge/Fog/Cloud؛ telemetry وحركة شبكة وسجلات Linux/Windows، مع سيناريوهات طبيعية وهجمات مضبوطة. مختلط/مختبري؛ لا يثبت أنه تشغيل إنتاجي ميداني.
- الترخيص: سجل Research Data Australia يذكر GPL-3.0؛ صفحة UNSW لا تعرض ترخيصًا بنفسها ولم تُفحص ملفات الحزمة، لذا يلزم التأكيد على نسخة الملفات. CC BY 4.0 للورقة لا يثبت ترخيص البيانات.

## الروابط

- المصدر الرسمي: https://research.unsw.edu.au/projects/toniot-datasets
- رابط التنزيل: غير متحقق منه

## طريقة الجمع والملفات

testbed مختبري شبكي يمثل بيئة IoT/IIoT متوسطة الحجم بطبقات Edge/Fog/Cloud؛ telemetry وحركة شبكة وسجلات Linux/Windows، مع سيناريوهات طبيعية وهجمات مضبوطة. مختلط/مختبري؛ لا يثبت أنه تشغيل إنتاجي ميداني.

- صفحة UNSW تصف بيانات IoT/IIoT خام log وCSV؛ شبكة pcap وlog وCSV من Zeek؛ Linux بصيغ TXT/CSV وأداة atop؛ Windows بصيغ BLG وCSV.
- مجلدات موصوفة: Raw datasets, Processed datasets, Train_Test_datasets, Description_stats_datasets, SecurityEvents_GroundTruth_datasets؛ لم تُفحص محتوياتها.
- ورقة telemetry تصف سبع فئات: Fridge, Garage, GPS Tracker, Modbus, Light Motion, Thermostat, Weather؛ الحقول التفصيلية واردة في الورقة لا من فحص ملفات.
- ورقة الشبكة تصف 44 خاصية تدفق مشتقة بواسطة Zeek؛ أسماء الأعمدة الكاملة غير متحققة مباشرة.

## حالة التنزيل والفحص

لم يُنزّل أي ملف بيانات. رابط SharePoint أعاد HTTP 200 إلى واجهة OneDrive لكن فهرس الملفات لم يظهر بالاستخراج غير التفاعلي؛ CloudStor تعذر حل نطاقه، وDataPort يقول إن الملفات غير مرفوعة ويتطلب اشتراكًا.

غير متحقق منه

## الاستخدام في المشروع

- يمكن استعمال timestamps وسجلات CPU/ذاكرة كسياق حمل خلفي على مستوى المضيف فقط بعد التحقق من الدقة والهوية.
- قد تُشتق حركة من pcap/Zeek بعد فحص الحقول، لكن لا تسمى bandwidth مسجلة ولا task latency.
- إنشاء المهام ومواصفاتها والمهل منفصلًا وبافتراضات معلنة؛ لا تستخدم label/type كقرارات تفريغ.

## التوصية

مكمل لسياق IoT/IIoT أو أمن الشبكات أو بعض موارد المضيف بعد استلام الملفات؛ غير مباشر لبحث MEC task offloading وEdgeCloudSim.

## المصادر والأبحاث



- https://research.unsw.edu.au/projects/toniot-datasets
- https://unsw-my.sharepoint.com/:f:/g/personal/z5025758_ad_unsw_edu_au/EvBTaetotpdGnW7rJQ8fCvYBh8063CNeY9W33MpRsarJaQ?e=yZlnxW
- https://ieee-dataport.org/documents/toniot-datasets
- https://researchdata.edu.au/new-generations-internet-toniot-datasets/1957406
- https://doi.org/10.1109/ACCESS.2020.3022862
- https://www.sciencedirect.com/science/article/pii/S2210670721002808
- https://doi.org/10.1109/JIOT.2021.3085194
