# AI Model Files
## 모델 불러 오는 법
```
easyocr_model = joblib.load('easyocr_base_model.pkl')
whisper_model = joblib.load('whisper_base_model.pkl')
```

## EasyOCR
- `easyocr_base_model.pkl`
```
langs = ['ko', 'en']
joblib.dump(Reader(lang_list=langs, gpu=False), 'easyocr_base_model.pkl')
```

## Whisper
- `whisper_base_model.pkl`
```
joblib.dump(whisper.load_model("base"), "whisper_base_model.pkl")
```
