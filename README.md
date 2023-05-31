# CTRL-F 서비스의 Back-End 부분 입니다.

# 환경세팅
`pip install -r requirements.txt`

## ai_model app
데이터를 저장할 models.py를 구축했고, url을 받아 인공지능 모델로 동영상에서 텍스트를 추출하여 DB에 저장합니다.

## api app
Front로 부터 api 요청을 받아, 값을 리턴해줍니다. rest framework를 사용하였습니다.
