# خلاصة بحثية موحّدة: مجموعات بيانات IoT وEdge/MEC وملاءمتها لـ EdgeCloudSim

## نطاق العمل والمنهجية

أُعدّ هذا التقرير اعتمادًا **حصريًا على نتائج التحقق الواردة في التكليف**؛ لم أجرِ بحثًا أو تنزيلًا أو فحصًا إضافيًا، ولم أضف حقائق خارجها. قارنت ثماني مجموعات: EUA، وToN_IoT، وGoogle Cluster Data v3، وCICIoT2023، وUNSW-IoTraffic، وBot-IoT، وUNSW-NB15، وUCI Image Recognition Task Execution Times in Mobile Edge Computing. ميزت بين: **مقاس/مسجل** في المصدر، و**مشتق** حسابيًا أو مكانيًا، و**مولد/محاكى**، و**غير متحقق**. كما فُصلت سنة الجمع عن سنة النشر/الإيداع، ولم تُعامل خصائص حركة الشبكة أو موارد المضيف تلقائيًا على أنها مهام MEC أو كمون مهام.

«مفحوص» أدناه يعني فقط مستوى الفحص المبين لكل مجموعة؛ ففحص صفحة أو مخطط لا يعني فحص صفوف الملفات. والإشارات [1]–[20] تقود إلى الأدلة المذكورة في سجل النتائج.

## مقارنة موجزة

| المجموعة | ما تقيسه/تصفه مباشرة | measured / derived / simulated | ما ينقصها لتفريغ المهام | التنزيل والفحص المتحققان | ملاءمتها لـ EdgeCloudSim |
|---|---|---|---|---|---|
| **EUA** [1–3] | مواقع محطات قاعدة ومواقع مستخدمين/نقاط مستخدم مولدة | مواقع المحطات مستمدة من سجل ACMA؛ إسناد IP تقريبي؛ جزء من مواقع المستخدمين والتجارب مولد | لا وصول مهام، CPU/task، مهل، كمون، طاقة، نطاق ترددي أو قرارات offloading مرصودة | نُزّلت وفُحصت 3 CSV فقط؛ ملفات أكبر وخرائط HTML لم تُفحص | **ملحق مكاني** محتمل، لا workload ولا benchmark offloading |
| **ToN_IoT** [4–7] | تليمترية IoT/IIoT، PCAP/Zeek، وسجلات Linux/Windows وأمن | testbed مختبري مختلط؛ حمل/هجمات مضبوطة؛ بعض CPU/RAM على مستوى النظام | لا مهام حوسبة أو قرارات offloading؛ CPU المضيف ليس متطلب مهمة؛ ملفات التنزيل لم تُفحص | لم يُنزّل أي ملف بيانات؛ حقول كثيرة موصوفة في الأوراق فقط | مصدر سياق/خلفية IoT أو موارد مضيف بحذر، لا محول جاهز |
| **Google Cluster Data v3** [8–10] | أحداث تقديم/جدولة/إخلاء واستخدام وطلبات CPU/ذاكرة في Borg | سجلات تشغيل فعلية؛ حقول مطبّعة/مبهمة | لا مواقع، أجهزة متنقلة، مهلات، أحجام مهام أو شبكة/طاقة MEC؛ جدولة الآلة ليست offloading | نُزّلت وفُحصت 5 ملفات schema؛ لا صفوف بيانات؛ HEAD فقط لملف shard | قوي لتحليل حمل وجدولة مراكز البيانات، **ليس MEC**؛ مفيد فقط كحمل/موارد مرجعية منفصلة |
| **CICIoT2023** [11–12] | حركة حزم/تدفقات أمن IoT من 105 أجهزة موصوفة | التقاط مختبري فعلي؛ benign مختبري وهجمات منشأة عمدًا | لا مهام أو موارد أو قرارات offloading ولا كمون/طاقة | لم تُنزّل PCAP/CSV؛ نموذج طلب بيانات ظهر، وخصائص CSV من وصف رسمي لا من ملف | أمن/حركة شبكية؛ لا يصلح مباشرة لـ workload offloading |
| **UNSW-IoTraffic** [13–15] | PCAP وتدفقات وبروتوكولات لـ27 جهاز IoT | حركة أجهزة فعلية في testbed؛ إحصاءات/ميزات مشتقة من الحزم | لا مهام أو موارد أو مواقع جغرافية أو قرارات offloading | فُحصت معاينتا CSV ملخصتين فقط؛ لم تُنزّل الأرشيفات (403) | **خلفية شبكة** محتملة بعد التنزيل؛ لا مهام MEC مباشرة |
| **Bot-IoT** [16–18] | PCAP وArgus/CSV لحركة IoT وهجمات | التقاط فعلي داخل testbed، لكن خدمات IoT والحركة والهجمات مُحاكاة/مولدة | لا وصول مهام، CPU، deadline، طاقة، مواقع، ولا قرارات offloading | ظهر فهرس SharePoint؛ لم يُنزّل أو يُفحص أي ملف بيانات | أمن/حركة شبكية؛ لا benchmark offloading |
| **UNSW-NB15** [19–20] | PCAP وتدفقات كشف تسلل، 49 خاصية موصوفة | حركة طبيعية مع هجمات اصطناعية مولدة | لا مهام أو موارد MEC أو كمون/طاقة/قرارات؛ ليست موثقة كـIoT | فُحصت الصفحة والفهرس فقط؛ لم تُفحص CSV/PCAP؛ الترخيص متعارض | سياق أمني/شبكي فقط، بعد فحص فعلي للأعمدة |
| **UCI Image Recognition MEC** [21–23] | 4,000 سجل زمن تنفيذ/دوران لتعّرف صور على أربعة أنواع من الخوادم | قياسات تنفيذ فعلية في إعداد تجربة مضبوط؛ العميل المتنقل مُحاكى | لا حجم صورة أو CPU لكل مهمة أو مهلة/طاقة/قرار offloading؛ زمن الدوران لا يفصل الشبكة عن المعالجة | الأرشيف الرسمي نُزّل؛ فُحص PDF و4 CSV (1,000 صف لكل منها) | **الأقرب مباشرة لزمن تنفيذ مهمة MEC**؛ يصلح للمعايرة/المقارنة المحدودة، لا كأثر offloading كامل |

## تحليل كل مجموعة

### 1. EUA — Edge Users Allocation

المجموعة مكانية بالأساس: تشمل محطات قاعدة من سجل تراخيص ACMA، ومواضع مستخدمين تقريبية مشتقة من إسناد عناوين IP، إضافة إلى نقاط مستخدم مولدة اصطناعيًا. ملفاتها تغطي أستراليا، مع أجزاء خاصة بملبورن. فُحصت فعليًا ملفات `site-optus-melbCBD.csv` (125 محطة وفق README)، و`users-melbcbd-generated.csv` (816 موقعًا مولدًا)، و`users-aus.csv` (4,748 سجلًا)؛ أما `site.csv` الكبير وملف المستخدمين المترو وخرائط HTML فلم تُفحص. لا توجد سلسلة زمنية ولا قياسات موارد/شبكة/مهام، وافتراضات التغطية والسعات الواردة في تجربة الورقة مولدة وليست حقول قياس. ترخيص MIT للمستودع لا يحسم تلقائيًا شروط بيانات ACMA وAPNIC وIP-API؛ وREADME يخص ACMA بملكية البيانات. [1–3]

**الحكم:** مصدر مساعد مفيد لإحداثيات أساس؛ لا يصلح وحده لتدريب/اختبار task offloading أو لإسناد latency/energy. لا يوجد محول EUA→EdgeCloudSim رسمي موثق.

### 2. ToN_IoT

تجمع موصوفة من telemetry وأثر شبكة وبيانات Linux/Windows في testbed أمني مختبري ذي طبقات Edge/Fog/Cloud. توثق الصفحات والأوراق ملفات PCAP وZeek وCSV وسجلات `atop`، كما تصف بعض telemetry بطوابع زمنية وGPS وقياسات أجهزة؛ غير أن أسماء الحقول التفصيلية لم تُتحقق بفحص الملفات. سجلات CPU/الذاكرة هي على مستوى النظام/المضيف، ولا تعني متطلبات CPU لمهمة. وسوم `label`/`type` تخص الهجمات لا وجهة تنفيذ. صفحة UNSW تعرض أكثر من 10 حساسات بينما الأدبيات الموصوفة تسرد سبع فئات؛ سبب اختلاف الوصف غير متحقق. لم يُنزّل أي ملف، وواجهة SharePoint لم تُظهر فهرس الملفات في الفحص غير التفاعلي. [4–7]

**الحكم:** مناسب لأمن IoT/IIoT أو سياق خلفي بعد الحصول على الملفات وفحصها؛ ليس workload offloading. ترخيص GPL-3.0 مستند إلى سجل RDA، لكن يلزم تأكيده على نسخة الملفات.

### 3. Google Cluster Data — Borg v3 (2019)

أثر تشغيل فعلي لمجدول Borg في ثماني خلايا خلال مايو 2019. يصف المخطط أحداث المجموعات والمهام والآلات والاستخدام، وطلبات CPU/ذاكرة واستخدامهما. نُزّلت وفُحصت schemas الخمسة؛ **لم تُقرأ صفوف بيانات**. لم يُنفذ تنزيل الأثر؛ طلب HEAD لملف shard واحد أظهر 498,371,634 بايتًا، ووثائق Google تذكر نحو 2.4 TiB مضغوطة للمجموعة. إذن بيانات الوصول/الجدولة حقيقية في سياق مركز بيانات، لكن `machine_id` وتعيين Borg إلى آلة لا يساويان قرار نقل مهمة من جهاز طرفي إلى MEC. لا تُعرف مواقع الخلايا؛ والموارد مطبّعة/مبهمة. لا توجد bandwidth أو network delay أو طاقة أو مهل أو حمولة بيانات مهمة. [8–10]

**الحكم:** أقوى خيار بين هذه المجموعات لتحليل أحمال وجدولة وموارد سحابية حقيقية، لكن ليس لقياس MEC/IoT ولا لتقييم offloading منفردًا.

### 4. CICIoT2023

التقاط شبكي من مختبر CIC يصف 105 أجهزة IoT؛ يجمع حركة سليمة مختبرية مع 33 نوع هجوم أُنشئت عمدًا. الورقة تذكر 16 ساعة لجمع benign، لكن تاريخ الجمع التقويمي غير متحقق. صفحة التنزيل عرضت نموذجًا يطلب بيانات تعريفية؛ لم يُرسل النموذج ولم تُنزّل ملفات PCAP/CSV. أسماء السمات مأخوذة من جدول الصفحة الرسمية وليست ترويسة ملف مفحوصة، واسم حقل التسمية غير متحقق. ترخيص ملفات البيانات غير محسوم، ولا يُستنتج من ترخيص الورقة. [11–12]

**الحكم:** مجموعة أمن شبكي IoT جيدة بحسب الوصف، لا مجموعة مهام/تفريغ. أي تحويل لتدفق إلى وصول أو حجم مهمة سيكون افتراضًا اصطناعيًا معلنًا.

### 5. UNSW-IoTraffic

تصف آثارًا فعلية لـ27 جهاز IoT في testbed بسيدني بين 22-09-2016 و13-04-2017 تقريبًا، مع تفاوت مدة الرصد حسب الجهاز. تشمل PCAP وملفات تدفق/بروتوكول. عُرضت معاينتا `device_pcap_summary.csv` و`protocol_diversity_prevalence.csv`؛ لم تُفحص ملفات التدفقات أو PCAP. رؤوس حقول التدفق من وصف الإيداع فقط. ملفات ZIP لم تُنزّل؛ طلبات HTTP HEAD إلى روابط Dryad أعادت 403. CC0 1.0 بحسب Dryad. أحجام الحمولة وتوقيتات التدفقات يمكن أن تدعم تحليل حركة أو معدل مشتق بعد فحص البيانات، لكنها لا تساوي حجم مهمة أو كمون مهمة ولا توفر سعة شبكة. [13–15]

**الحكم:** أفضل المرشحين هنا لتغذية أثر حركة IoT خلفي بعد الحصول على الملفات، لكنه ليس سجل مهام حوسبة ولا تتبع offloading.

### 6. Bot-IoT

مجموعة كشف هجمات صُممت في Cyber Range مختبري: خدمات منزل ذكي موصوفة بأنها محاكاة، وحركة عادية مولدة بأداة، وهجمات من آلات Kali؛ الحزم نفسها جُمعت في PCAP ثم اشتُقت ملفات Argus/CSV. هذا التقاط فعلي لتجربة مولدة، لا قياس ميداني مستقل لأجهزة منشورة. الأعمدة المنشورة تشمل أوقات/حجوم/معدلات تدفق ووسوم هجوم، لكن لم يُفحص أي CSV أو PCAP. فهرس SharePoint كان مرئيًا؛ نجاح تنزيل البيانات نفسها غير متحقق، وDataPort يشترط دخولًا بحسب الوصف. الاستخدام الأكاديمي مسموح وفق صفحة UNSW؛ التجاري يتطلب اتفاقًا، مع تحفظ شروط إعادة التوزيع. [16–18]

**الحكم:** لتحليل كشف التسلل/حركة IoT، لا كـMEC workload. `Stime` و`bytes` قد يكونان proxies لحركة تدفق فقط؛ لا يُعاد تسميتهما وصول مهمة أو حجم إدخال مهمة.

### 7. UNSW-NB15

بيانات تدفق/حزم لكشف التسلل؛ توصف بأنها حركة طبيعية مع هجمات اصطناعية مولدة بـIXIA PerfectStorm، لا كبيانات IoT أو MEC. تذكر الصفحة 2,540,044 سجلًا و49 خاصية، لكن أسماء أعمدة الملفات لم تُفحص. عُرض فهرس SharePoint ولم تُنزّل ملفات CSV/PCAP أو PDF. تاريخ RDA (2015-09-30) لا يثبت وحده كامل فترة الجمع. يوجد تعارض ترخيص: صفحة UNSW تذكر استخدامًا أكاديميًا مجانيًا وموافقة للاستخدام التجاري، بينما RDA يعرض GPL-3.0؛ يجب عدم حسمه افتراضيًا. [19–20]

**الحكم:** ليس خيارًا لـIoT/MEC offloading. قد يدعم سياق IDS بعد فحص الملفات وتسوية الترخيص؛ خصائص التدفق ليست قياس bandwidth أو task size تلقائيًا.

### 8. UCI Image Recognition Task Execution Times in Mobile Edge Computing

الأقرب لمهمة حوسبة فعلية ضمن هذه المجموعة: أربعة ملفات CSV (MacBookPro1، MacBookPro2، VM، Raspberry Pi)، كل منها 1,000 سجل، وعمودا `Time` و`Execution Time`. الأرشيف الرسمي نُزّل وفُك، وفُحص ملف الوصف والملفات الأربعة. التاريخ المسجل 26-11-2020، والإرسال موصوف بأنه صورة كل ثانية؛ `Execution Time` هو زمن دوران من بدء نقل الصورة إلى رجوع نتيجة التعرف، فلا يفصل الشبكة عن التنفيذ. مواصفات CPU/RAM الأساسية للأجهزة مذكورة، لكن لا يوجد قياس استخدام CPU أو متطلبات لكل مهمة. العميل المتنقل مُحاكى كعملية. توجد فجوة توثيقية مهمة: UCI تربط البيانات بورقة 2019، لكن الورقة المفحوصة تصف مجموعات/تجارب أخرى ولا توثق ملفات التعرف على الصور المؤرخة 2020؛ لم يُعثر على ورقة مستقلة تصف هذه الملفات. [21–23]

**الحكم:** أفضل نقطة بداية لمعايرة زمن دوران مهمة محددة ومقارنة أنواع خوادم، وليس ground truth لقرارات اختيار الخادم ولا workload شاملًا.

## التمييز بين المقاس والمشتق والمحاكى

- **قياسات/سجلات فعلية في سياق المصدر:** UCI لأزمنة تنفيذ/دوران مهمة الصور على إعداد التجربة؛ Google Borg لأحداث الجدولة واستخدام الموارد؛ التقاطات حركة الشبكة المختبرية في CICIoT2023 وUNSW-IoTraffic وBot-IoT وUNSW-NB15 (لكن طبيعة الحركة تختلف، وفي بعضها حركة هجومية/عادية مولدة). «فعلي» هنا يصف التسجيل في بيئة التجربة، لا يثبت نشرًا إنتاجيًا أو قياس MEC متكاملًا.
- **مشتق أو تقريبي:** IP-to-location في EUA؛ ميزات تدفق مستخرجة من PCAP في UNSW-IoTraffic وBot-IoT وUNSW-NB15 وCICIoT2023؛ أي bandwidth أو وصول مهمة محسوب من هذه الآثار سيكون مقياسًا مشتقًا بعد التنفيذ، لا حقلًا أصليًا مثبتًا هنا.
- **مصطنع/محاكى أو مضبوط:** بعض مستخدمي EUA وتغطية الخلايا/سعاتها في التجارب؛ سيناريوهات الهجوم في ToN_IoT وCICIoT2023 وBot-IoT وUNSW-NB15؛ حركة وخدمات المختبر في Bot-IoT؛ وإرسال الصور بوتيرة مضبوطة في UCI. أما مهام EdgeCloudSim الإضافية التي سيولدها الباحث فهي بيانات تجريبية جديدة، لا تنسب للمجموعات الأصلية.
- **غير متحقق:** لا تُعمم فترة 2018 في EUA على كل ملف؛ ولا تُستنتج مدة جمع أطول من تواريخ الكتالوج في ToN_IoT أو UNSW-NB15؛ ولا تُعامل سنة النشر/الإيداع كسنة القياس. محتويات الملفات غير المنزلة تبقى غير مفحوصة.

## فجوات البيانات المشتركة

لا تقدم أي مجموعة من هذه الثماني **جميع** العناصر المطلوبة لتقييم واقعي وقابل لإعادة الإنتاج لتفريغ مهام MEC: أوقات وصول موثقة لمهام حوسبة، أحجام input/output، CPU cycles أو متطلبات موارد لكل مهمة، deadlines، قرارات offloading فعلية، وقياسات منفصلة للتأخير/النطاق الترددي/الطاقة مع ربطها بالمستخدم والخادم. UCI تقدم زمن دوران لمهمة واحدة على أجهزة مختلفة لكنها لا تفصل النقل والمعالجة ولا توثق قرار الاختيار. Google يقدم موارد وجدولة فعلية لكن في مركز بيانات من دون هوية MEC أو شبكة وصول. EUA يقدم بعض المواقع دون الزمن والحمل. آثار الأمن الشبكي تقدم حركة/حزم لا workload حسابيًا. لذلك لا ينبغي الادعاء بأن أيًا منها benchmark كاملًا لـEdgeCloudSim.

## التوصية الرئيسية والمساعدة

1. **الرئيسية: UCI Image Recognition Task Execution Times in Mobile Edge Computing**، عند سؤال البحث المحدود عن زمن دوران مهمة تعرف صور عبر أنواع عتاد طرفي. السبب: ملفات CSV نُزّلت وفُحصت، وتحتوي 4,000 قياس مسجلًا على أربعة خيارات تنفيذ. استخدمها لمعايرة/مقارنة زمن تنفيذ شامل فقط، مع الإفصاح عن كون العميل محاكى، وثبات الحمل، وعدم فصل الشبكة، وفجوة إحالة ورقة 2019. **لا** تستخدمها وحدها لتدريب قرارات offloading أو ادعاء تقييم MEC شامل.
2. **المساعدة: EUA** لإضافة توزيع مكاني تقريبي لمحطات/مستخدمين إلى سيناريو جغرافي في Melbourne، بعد تحويل الإحداثيات إلى إطار محلي بالمتر. اجعلها طبقة مكانية منفصلة وصرّح أن جزءًا من مواقع المستخدمين اصطناعي/تقريبي، وأن الملفات الكبيرة لم تُفحص. لا تستنتج منها latency أو تغطية فعلية إلا كافتراض نمذجة. [1–3، 21–23]

لأبحاث حمل CPU/الذاكرة وجدولة مركز البيانات، Google Cluster v3 هو الملحق الأنسب بدل EUA؛ لكن يجب عدم خلطه ببيئة MEC أو تعميمه على أجهزة طرفية. ولحركة شبكة IoT الخلفية يمكن النظر في UNSW-IoTraffic بعد إتاحة الملفات وفحصها؛ لا يمثل أي منهما بديلًا لبيانات مهام offloading.

## خطة ربط عملية بـ EdgeCloudSim

1. **تثبيت نطاق السيناريو:** أنشئ سيناريو EdgeCloudSim مستقلًا، ولا تفترض وجود محول EUA جاهز. وثّق إصدار EdgeCloudSim، الإعدادات، وحدات القياس، والبذور العشوائية.
2. **المواقع:** حوّل `LATITUDE/LONGITUDE` في ملفات EUA المفحوصة إلى إحداثيات محلية بالمتر حول Melbourne؛ عيّن محطات القاعدة كعقد حافة ومواقع المستخدمين كأجهزة فقط حيث تتوفر السجلات. سجّل مصدر كل نقطة (ACMA/إسناد IP/توليد اصطناعي)، ولا تخلطها بقياسات حركة أو handover.
3. **الأجهزة والحركة:** عرّف أجهزة/حركة المستخدمين في نموذج الموقع والحركة الخاص بك. EUA ثابتة مكانيًا ولا تقدم أثر تنقل؛ أي حركة أو handover تضاف هي نموذج مستقل معلن.
4. **مولّد الحمل:** استخدم UCI فقط لتوزيع/معايرة زمن دوران التعرف على الصورة على الخوادم الأربعة، مع تجنب احتساب التأخير مرتين إذا كان `Execution Time` شاملًا النقل والمعالجة والعودة. أضف أوقات وصول/أحجام صور/CPU cycles/deadlines من مصدر مستقل أو افتراضات، ووسمها **مصطنعة**؛ لا تخترعها داخل ملف البيانات.
5. **النموذج الشبكي:** عرّف WLAN/WAN، bandwidth، delay، loss بصورة مستقلة ومن مصدر موثق أو كافتراض معلن. لا تعتبر معدل تدفق شبكي مرادفًا لسعة الوصلة، ولا تستخرج latency مهمة من حجم/توقيت حزم دون تحليل وقياس مناسب.
6. **الموارد والسياسات:** عرّف مواصفات عقد الحافة والسحابة في إعداد EdgeCloudSim، ثم نفّذ EdgeOrchestrator بسياسات معلنة. إن استُخدمت سجلات Google لمعايرة طلب/استخدام CPU أو الذاكرة، احتفظ بها كمصدر خلفية منفصل واذكر أن وحداتها مبهمة/مطبّعة وأنها من Borg لا MEC.
7. **التقييم والتقرير:** افصل القياس الأصلي عن المدخلات المشتقة والافتراضات والمخرجات المحاكية. قِس محاكاةً latency/energy/success/offloading decisions، ولا تنسب نتائج المحاكاة إلى UCI أو EUA أو سجلات الشبكة. نفّذ تحليل حساسية للتحميل والشبكة والموارد، وأرفق قائمة الحقول غير المرصودة.

## سجل المراجع والأدلة

1. EUA GitHub: https://github.com/PhuLai/eua-dataset ؛ README للمواقع: https://raw.githubusercontent.com/PhuLai/eua-dataset/master/edge-servers/README.md ؛ README للمستخدمين: https://raw.githubusercontent.com/PhuLai/eua-dataset/master/users/README.md
2. EUA الترخيص: https://raw.githubusercontent.com/PhuLai/eua-dataset/master/LICENSE ؛ ACMA: https://www.acma.gov.au/industry/spectrum/radiocomms-licensing/register-radiocommunications-licences/radiocomms-licence-data
3. EUA ورقة ICSOC 2018: https://doi.org/10.1007/978-3-030-03596-9_15 ؛ ICSOC 2019: https://doi.org/10.1007/978-3-030-33702-5_8 ؛ سجل IEEE DataPort: https://ieee-dataport.org/documents/eua-dataset
4. ToN_IoT صفحة UNSW: https://research.unsw.edu.au/projects/toniot-datasets ؛ رابط SharePoint المذكور في نتائج التحقق: https://unsw-my.sharepoint.com/:f:/g/personal/z5025758_ad_unsw_edu_au/EvBTaetotpdGnW7rJQ8fCvYBh8063CNeY9W33MpRsarJaQ?e=yZlnxW
5. ToN_IoT سجل RDA: https://researchdata.edu.au/new-generations-internet-toniot-datasets/1957406 ؛ IEEE DataPort: https://ieee-dataport.org/documents/toniot-datasets
6. ToN_IoT ورقة telemetry: https://doi.org/10.1109/ACCESS.2020.3022862 ؛ ورقة شبكة ToN_IoT: https://www.sciencedirect.com/science/article/pii/S2210670721002808 ؛ ورقة التغاير: https://doi.org/10.1109/JIOT.2021.3085194
7. ToN_IoT بيانات مشتقة للحافة (ليست offloading): https://gala.gre.ac.uk/id/eprint/34598/7/34598_ESSOP_Generating_IoT_edge_network_datasets.pdf ؛ تراخيص مذكورة في السجلات: https://creativecommons.org/licenses/by/4.0/ وhttps://www.gnu.org/licenses/gpl-3.0.html
8. Google Cluster Data: https://github.com/google/cluster-data ؛ إرشادات v3: https://github.com/google/cluster-data/blob/master/ClusterData2019.md ؛ مخطط proto: https://raw.githubusercontent.com/google/cluster-data/master/clusterdata_trace_format_v3.proto
9. Google v3 schemas: https://storage.googleapis.com/clusterdata_2019_schema/collection_events.schema.json ؛ https://storage.googleapis.com/clusterdata_2019_schema/instance_events.schema.json ؛ https://storage.googleapis.com/clusterdata_2019_schema/machine_events.schema.json ؛ https://storage.googleapis.com/clusterdata_2019_schema/machine_attributes.schema.json ؛ https://storage.googleapis.com/clusterdata_2019_schema/instance_usage.schema.json
10. Google Borg: The Next Generation: https://doi.org/10.1145/3342195.3387517 ؛ منشور Google: https://research.google/blog/yet-more-google-compute-cluster-trace-data/ ؛ CC BY 4.0: https://creativecommons.org/licenses/by/4.0/
11. CICIoT2023 صفحة UNB: https://www.unb.ca/cic/datasets/iotdataset-2023.html ؛ صفحة التنزيل: https://cicresearch.ca/IOTDataset/CIC_IOT_Dataset2023/
12. ورقة CICIoT2023: https://doi.org/10.3390/s23135941 ؛ EdgeCloudSim: https://github.com/CagataySonmez/EdgeCloudSim
13. UNSW-IoTraffic الصفحة الرسمية: https://iotanalytics.unsw.edu.au/unsw-iotraffic.html ؛ Dryad: https://datadryad.org/dataset/doi:10.5061/dryad.w0vt4b94b
14. UNSW-IoTraffic بيانات تعريف DataCite: https://api.datacite.org/dois/10.5061/dryad.w0vt4b94b ؛ مثال رابط تنزيل تعذر الوصول إليه (403): https://datadryad.org/downloads/file_stream/4322592
15. UNSW-IoTraffic ورقة الوصف: https://doi.org/10.1109/IEEEDATA.2025.3602010 ؛ CC0: https://creativecommons.org/publicdomain/zero/1.0/
16. Bot-IoT صفحة UNSW: https://research.unsw.edu.au/projects/bot-iot-dataset ؛ SharePoint: https://unsw-my.sharepoint.com/:f:/g/personal/z5131399_ad_unsw_edu_au/EjlBDf2KODxPgXmqbO3MxxsBBVARCKZxGUG47OiFHb_AnQ
17. Bot-IoT IEEE DataPort: https://ieee-dataport.org/documents/bot-iot-dataset ؛ الورقة: https://doi.org/10.1016/j.future.2019.05.041 ؛ نص arXiv: https://arxiv.org/abs/1811.00701
18. UCI المقارنة المرجعية في EdgeCloudSim: https://github.com/CagataySonmez/EdgeCloudSim ؛ ورقة EdgeCloudSim: https://doi.org/10.1002/ett.3493
19. UNSW-NB15 صفحة UNSW: https://research.unsw.edu.au/projects/unsw-nb15-dataset ؛ SharePoint: https://unsw-my.sharepoint.com/:f:/g/personal/z5025758_ad_unsw_edu_au/EnuQZZn3XuNBjgfcUu4DIVMBLCHyoLHqOswirpOQifr1ag?e=gKWkLS ؛ RDA: https://researchdata.edu.au/the-unsw-nb15-dataset/1957529
20. UNSW-NB15 الورقة الأصلية: https://ieeexplore.ieee.org/document/7348942 ؛ DOI البيانات: https://doi.org/10.26190/5d7ac5b1e8485 ؛ سجل GPL المذكور: https://www.gnu.org/licenses/gpl-3.0.html
21. UCI Image Recognition MEC صفحة المجموعة: https://archive.ics.uci.edu/dataset/859/image+recognition+task+execution+times+in+mobile+edge+comput ؛ الملف الرسمي: https://archive.ics.uci.edu/static/public/859/image+recognition+task+execution+times+in+mobile+edge+computing.zip
22. UCI DOI: https://doi.org/10.24432/C5N617 ؛ CC BY 4.0: https://creativecommons.org/licenses/by/4.0/legalcode
23. الورقة المرتبطة في UCI: https://doi.org/10.1109/WD.2019.8734210 ؛ نسخة جامعة غلاسكو: https://eprints.gla.ac.uk/179591/ ؛ ملف PDF: https://eprints.gla.ac.uk/179591/7/179591.pdf
