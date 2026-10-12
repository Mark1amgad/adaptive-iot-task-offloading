# دليل إعادة الإنتاج

1. ثبّت Python 3.11 و`pandas`, `openpyxl`.
2. شغّل الملفات في `analysis/` باستخدام مسارات نسبية من مجلد `Dataset`.
3. لا تعدّل `raw/`. اكتب المخرجات في `processed/` أو `analysis/`.
4. لتنزيل مصدر لم يُنزّل، استخدم رابط المصدر الرسمي في `README_AR.md` والتزم بترخيصه.
5. افصل في النتائج بين `Measured` و`Derived` و`Simulated`، وسجّل الإصدار والتاريخ والبذرة العشوائية.
6. في EdgeCloudSim، عرّف المهام والموارد والمهل والشبكة التي لا توفرها البيانات كمدخلات مستقلة موثقة.

## تشغيل التحليل

```bash
cd Dataset
python3 analysis/inspect_dataset.py --input 08_UCI_Image_Recognition_MEC/raw/uci_extracted/final/TATDescriptionDataset/DatasetExpeirmentalDescription.pdf
python3 analysis/dataset_quality_report.py --input 01_EUA/raw/users-aus.csv
python3 analysis/compare_datasets.py --root .
```
