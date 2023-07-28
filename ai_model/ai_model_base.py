from easyocr import Reader
from pytube import YouTube
# from krwordrank.word import KRWordRank
# from krwordrank.word import summarize_with_keywords
from hanspell import spell_checker


import time
import pandas as pd
import cv2
import whisper
import joblib
# from konlpy.tag import Okt
import re, os

from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')


class AiModel:
    def __init__(self, url):
        """
        args:
            url : Youtube Url
        """
        self.url = url
        self.yt = YouTube(self.url)
        self.video_url = self.yt.streams.get_highest_resolution().url
        self.audio_url = self.yt.streams.filter(only_audio=True).first().url
        self.caption_df = pd.DataFrame(columns=["start", "end", "text"])
        self.easyocr_results = pd.DataFrame(columns=["bbox", "text", "conf", "time", "size"]) # bbox = (tl, tr, br, bl)
        self.whisper_results = pd.DataFrame(columns=["start", "end", "text"])

        self.height = None
        self.width = None

        cap = cv2.VideoCapture(self.video_url)
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) # 프레임 개수
        print("fps :", self.fps)
        print("frame_count :", self.frame_count)

        success, frame = cap.read()
        if not success:
            print("cannot get video")
            self.height = None
            self.width = None
        cap.release()
        self.height, self.width = frame.shape[:2]

    def get_captions(self):
        """
        YouTube에서 제공하는 자막 정보 받기
        return: pd.DataFrame, list(keywords)
        """
        # 첫 번째 자막 선택
        caption = self.yt.captions.all()[0]
        # 한국어 가져오기 'ko'와 'a.ko' 존재. 'a.ko'는 자동 생성된 한국어 자막
        # 영어도 마찬가지로 'en'과 'a.en' 존재.
        # self.caption = self.yt.captions.get('a.ko')

        # YouTube에서 제공하는 자막 DataFrame으로 저장
        for data in caption.json_captions['events']:
            if 'aAppend' in data:
                continue
            if 'segs' in data:
                start = data['tStartMs'] / 1000.0
                end = start + (data['dDurationMs'] / 1000.0)
                text = []
                for seg in data['segs']:
                    text.append(seg['utf8'])
                text = ' '.join(text)
                temp = pd.DataFrame([[start, end, text]], columns=["start", "end", "text"])
                self.caption_df = pd.concat([self.caption_df, temp], ignore_index=True)
        
        #text 추출
        text = self.caption_df['text']
        text_list = list(map(str, text))
        keywords = self.texts2keyword(text_list)
        print(keywords)

        return self.caption_df, keywords
    
    def get_easyocr_result(self):
        """
        easyocr을 통해 동영상에서 Text 추출
        Cap.read()와 EasyOCR을 같이 쓰면 프레임을 끝까지 못읽어와서
        프레임을 다 뽑아오고 EasyOCR 진행
        return: pd.DataFrame, list(keywords)
        """
        print("EasyOCR Start!!")
        # easyocr_model = joblib.load("ai_model/models/easyocr_base_model.pkl")
        langs = ['ko', 'en']
        easyocr_model = Reader(lang_list=langs, gpu=True)
        cap = cv2.VideoCapture(self.video_url)
        frames = []
        times = []
        for _ in tqdm(range(int(self.frame_count))):
            frame_pos = cap.get(cv2.CAP_PROP_POS_FRAMES) # 현재 프레임
            success, frame = cap.read()
            
            if not success:
                print('not success frame :', frame_pos)
                print('not success time :', frame_pos / self.fps)
                print('not success ... break')
                break

            if frame_pos % (self.fps) != 0: # 1초에 한 장씩
                continue

            frames.append(frame)
            times.append(frame_pos / self.fps) # 시간 정보

        cap.release()

        for frame, time in zip(tqdm(frames), times):
            temp = easyocr_model.readtext(frame, detail=1)
            # 상대 좌표로 변경
            for i in temp:
                for j in i[0]:
                    j[0] /= self.width
                    j[1] /= self.height
            # result = pd.DataFrame(easyocr_model.readtext(frame, detail=1), columns=['bbox', 'text', 'conf'])
            result = pd.DataFrame(temp, columns=['bbox', 'text', 'conf'])
            result['time'] = time
            self.easyocr_results = pd.concat([self.easyocr_results, result], ignore_index=True)

        #text 추출
        text = self.easyocr_results['text']
        text_list = list(map(str, text))
        keywords = self.texts2keyword(text_list)
        print(keywords)    
        print("EasyOCR Done!!")
        return self.easyocr_results, keywords

    def get_whisper_result(self):
        """
        Whisper를 통해 동영상 오디오에서 Text 추출
        return: pd.DataFrame, list(keywords)
        """
        print('Whisper Start!!')
        whisper_model = joblib.load("ai_model/models/whisper_base_model.pkl")
        audio_all = whisper.load_audio(self.audio_url) # load audio
        result = whisper_model.transcribe(audio_all)
        for seg in result['segments']:
            start, end, text = seg['start'], seg['end'], seg['text']
            # print(f"[ {start:>6.2f} ~ {end:>6.2f} ] {text}")
            temp = pd.DataFrame([[start, end, text]], columns=["start", "end", "text"])
            self.whisper_results = pd.concat([self.whisper_results, temp], ignore_index=True)

        #text 추출
        text = self.whisper_results['text']
        text_list = list(map(str, text))
        keywords = self.texts2keyword(text_list)
        print(keywords)
        print('Whisper Done!!')
        return self.whisper_results, keywords

    def texts2keyword(self, texts):
        from keybert import KeyBERT
        from kiwipiepy import Kiwi
        from transformers import BertModel

        model = BertModel.from_pretrained('skt/kobert-base-v1')
        kw_model = KeyBERT(model)

        kiwi = Kiwi()
        nouns_list = []
        for sentences in texts:
            # 맞춤법 검사
            spell_sentence = spell_checker.check(sentences)
            checked_sentence = spell_sentence.checked
            
            #영어, 한글, 숫자 외 모든 문자 제거
            sentences = re.sub('[^가-힣a-z1-9]', ' ', checked_sentence)

            for sentence in kiwi.analyze(sentences):
                nouns = [token.form for token in sentence[0] if token.tag.startswith('NN')]
                if nouns:
                    nouns_list.extend(nouns)
            result_text = ' '.join(nouns_list)

        #불용어 처리
        # stop_words = ['말씀','지금','오늘','번째']
        # keywords = kw_model.extract_keywords(result_text, keyphrase_ngram_range=(1, 1), stop_words=stop_words, top_n=20)
        keywords = kw_model.extract_keywords(result_text, keyphrase_ngram_range=(1, 1), stop_words=None, top_n=20)
        keywords = [item[0] for item in keywords]
        return keywords
    
    # def texts2keyword2(self, texts):
    #     os.environ['JAVA_HOME'] = r'C:\Program Files\Java\jdk-17' 
    #     text_str = list(map(str, texts))
        
    #     okt = Okt()
    #     result = []
    #     for sentence in text_str:
    #         #맞춤법 확인
    #         print(sentence)
    #         spell_sentence = spell_checker.check(sentence)
    #         checked_sentence = spell_sentence.checked
            
    #         #영어, 한글,숫자 외 모든 문자 제거
    #         sentence = re.sub('[^가-힣a-z1-9]', ' ', checked_sentence)

    #         print(sentence)
    #         if len(sentence) == 0:
    #             continue
    #         sentence_pos = okt.pos(sentence, norm= True, stem=True)
    #         nouns = [word for word, pos in sentence_pos if pos == 'Noun']
    #         if len(nouns) == 1:
    #             continue
    #         result.append(' '.join(nouns))
    #     #print(result)
    #     min_count = 2   # 단어의 최소 출현 빈도수 (그래프 생성 시)
    #     max_length = 10 # 단어의 최대 길이
    #     #wordrank_extractor = KRWordRank(min_count=min_count, max_length=max_length)
    #     beta = 0.85    # PageRank의 decaying factor beta
    #     max_iter=15
        
    #     keywords_result = []
    #     keywords = summarize_with_keywords(result, min_count=min_count, max_length=max_length, beta=beta, max_iter=max_iter, verbose=True)
    #     for word, r in sorted(keywords.items(), key=lambda x:x[1], reverse=True):
    #             keywords_result.append(word)
    #     return keywords_result


if __name__ == "__main__":
    url = 'https://www.youtube.com/watch?v=bGcVkNP1tPs&t=2s&ab_channel=1%EB%B6%84%EB%AF%B8%EB%A7%8C'
    models = AiModel(url=url)
    # caption = models.get_captions()
    # caption.to_csv("caption.csv")
    #easyocr_result = models.get_easyocr_result()
    # easyocr_result.to_csv("easyocr_result.csv")
    whisper_result = models.get_whisper_result()
    #whisper_result.to_csv("whisper_result.csv")
