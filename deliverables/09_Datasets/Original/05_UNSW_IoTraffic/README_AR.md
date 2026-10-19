# UNSW IoT traffic data with packets, flows, and protocols

## الحالة

هذه الصفحة مبنية على نتائج تحقق موثقة. لا تعني الإشارة إلى ملف في ورقة أو README أن الملف فُحص، ويظهر مستوى الفحص صراحةً أدناه.

## المصدر والمؤسسة

- الاسم الرسمي: UNSW IoT traffic data with packets, flows, and protocols
- المؤسسة/الجامعة: غير متحقق منه
- المنطقة: سيدني، أستراليا؛ UNSW Sydney.
- فترة الجمع: تقريبًا 2016-09-22 إلى 2017-04-13؛ نحو 203 أيام إجمالية مع اختلاف مدة الالتقاط حسب الجهاز.
- سنة النشر/الإيداع: مقال الوصف 2025-08-25؛ سجل Dryad 2025-08-29؛ الجمع 2016–2017.
- طبيعة البيانات: التقاط فعلي عبر tcpdump على بوابة TP-Link Archer C7 v2/OpenWrt في testbed LAN لـ27 جهاز IoT استهلاكيًا؛ فصل الآثار وفق MAC. حركة أجهزة فعلية في مختبر، وليست مهام حوسبة أو قرارات offloading.
- الترخيص: CC0 1.0 وفق سجل Dryad.

## الروابط

- المصدر الرسمي: https://iotanalytics.unsw.edu.au/unsw-iotraffic.html
- رابط التنزيل: غير متحقق منه

## طريقة الجمع والملفات

التقاط فعلي عبر tcpdump على بوابة TP-Link Archer C7 v2/OpenWrt في testbed LAN لـ27 جهاز IoT استهلاكيًا؛ فصل الآثار وفق MAC. حركة أجهزة فعلية في مختبر، وليست مهام حوسبة أو قرارات offloading.

- 27 ملف PCAP خاصًا بالأجهزة؛ flows.zip يحوي 27 CSV؛ protocols.zip نماذج JSON وCSV لمعلمات الطلب/الاستجابة؛ scripts.zip أدوات تحليل.
- device_pcap_summary.csv رأسه المفحوص: Device Name, Device MAC Address, First Seen, Last Seen, Number of Packets, Number of Flows.
- protocol_diversity_prevalence.csv رأسه المفحوص: Protocol, Number of Devices, Number of Flows.
- حقول التدفق المذكورة في وصف الإيداع تشمل time, srcMac, dstMac, ethType, srcIp, dstIp, ipProto, srcPort, dstPort, srcNumPackets, dstNumPackets, srcPayloadSize, dstPayloadSize, flowDuration, interarrival statistics, protocol؛ لم تفحص CSV التدفقات مباشرة.
- الأحجام المدرجة: 28.47 GB إجمالي ملفات، UNSW-IoTraffic.zip 14.24 GB وpcaps.zip 13.92 GB؛ لا تخلط النسخ/الأرشيفات.

## حالة التنزيل والفحص

فُحصت الصفحة الرسمية وDryad وDataCite ومقال الوصف ومعاينتا CSV الملخصتين فقط. لم تُفتح PCAP أو ملفات التدفقات/الأرشيفات؛ طلبات HTTP HEAD لروابط Dryad أعادت 403، لذلك لم يُنزّل أي أرشيف.

غير متحقق منه

## الاستخدام في المشروع

- يمكن استخدام أول حزمة وتوقيتات التدفقات لمحاكاة حركة خلفية، لا تسميها task arrivals دون افتراض صريح.
- يمكن استخدام بايتات payload كحجوم نقل تقريبية لا CPU cycles؛ موارد ومواقع وشبكة ومهل وطاقة وقرارات offloading تحتاج مصدرًا/نموذجًا مستقلاً.
- لا تنسب نتائج EdgeCloudSim إلى UNSW-IoTraffic.

## التوصية

ملائم كأثر حركة IoT خلفي بعد إتاحة الأرشيف وفحصه؛ ليس مدخل مهام جاهزًا لـEdgeCloudSim.

## المصادر والأبحاث



- https://iotanalytics.unsw.edu.au/unsw-iotraffic.html
- https://datadryad.org/dataset/doi:10.5061/dryad.w0vt4b94b
- https://api.datacite.org/dois/10.5061/dryad.w0vt4b94b
- https://datadryad.org/downloads/file_stream/4322592
- https://doi.org/10.1109/IEEEDATA.2025.3602010
- https://creativecommons.org/publicdomain/zero/1.0/
