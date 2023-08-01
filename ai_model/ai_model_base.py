from easyocr import Reader
from pytube import YouTube
# from krwordrank.word import KRWordRank
# from krwordrank.word import summarize_with_keywords
from hanspell import spell_checker
from skimage.metrics import structural_similarity as ssim 

import time
import pandas as pd
import cv2
import whisper
import torch
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
        self.easyocr_results = pd.DataFrame(columns=["bbox", "text", "conf", "time"]) # bbox = (tl, tr, br, bl)
        self.whisper_results = pd.DataFrame(columns=["start", "end", "text"])

        self.height = None
        self.width = None

        cap = cv2.VideoCapture(self.video_url)
        self.fps = round(cap.get(cv2.CAP_PROP_FPS))
        self.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) # 프레임 개수
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
        prev_frame = None
        for i in tqdm(range(int(self.frame_count))):
            frame_pos = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) # 현재 프레임
            success, frame = cap.read()

            if not success:
                print('not success frame :', frame_pos)
                print('not success time :', frame_pos / self.fps)
                print('not success ... break')
                break

            if frame_pos % (self.fps) != 0: # 1초에 한 장씩
                continue

            if i != 0:
                # bins = 255
                grayPrev = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
                grayNow = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                score = ssim(grayPrev, grayNow, full=False) # SSIM
                # histPrev = cv2.calcHist(images=[grayPrev], channels=[0], mask=None, histSize=[bins], ranges=[0, 256])
                # histNow = cv2.calcHist(images=[grayNow], channels=[0], mask=None, histSize=[bins], ranges=[0, 256])
                # score = cv2.compareHist(histPrev, histNow, cv2.HISTCMP_CORREL)
                # print("score :", score)
                if score > 0.9:
                    continue

            frames.append(frame)
            prev_frame = frame
            times.append(frame_pos / self.fps) # 시간 정보

        cap.release()
        print("len(frames) : ", len(frames))

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

        # 중복 제거
        # self.easyocr_results = drop_duplicated(self.easyocr_results)

        # text 추출
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
        # whisper_model = joblib.load("ai_model/models/whisper_base_model.pkl")
        # gpu 사용
        devices = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        print("devices:", devices)
        whisper_model = whisper.load_model("tiny", device=devices)
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

    def texts2keyword(self,texts):
        from kiwipiepy import Kiwi
        from gensim.models.ldamodel import LdaModel
        from gensim import corpora

        f = open('data/stopwords.txt', encoding='utf8') 
        stopwords = f.readlines()
        f.close()
        user_stopwords = ['거','초','앞','수','번','뒤','손','지금']
        stopwords = user_stopwords + stopwords
        stopwords = [re.sub('[^ 가-힣]', '', text) for text in stopwords]

        #전처리
        kiwi = Kiwi()

        nouns_list = []
        for sentences in texts:

            #영어, 한글, 숫자 외 모든 문자 제거
            sentences = re.sub('[^가-힣a-z1-9]', '', sentences)
            for sentence in kiwi.analyze(sentences):
                nouns = [token.form for token in sentence[0] if token.form not in stopwords and token.tag.startswith('NN')]
                if nouns:
                    nouns_list.append(nouns)
        dictionary = corpora.Dictionary(nouns_list)

        #2번 이상 출현 , 전체 50% 이상 차지 단어
        dictionary.filter_extremes(no_below=2, no_above=0.5)
        corpus = [dictionary.doc2bow(doc) for doc in nouns_list]

        num_topics = 1
        chunksize = 2000
        passes = 20
        iterations = 400
        eval_every = None

        temp = dictionary[0]
        id2word = dictionary.id2token

        model = LdaModel(
            corpus=corpus,
            id2word=id2word,
            chunksize=chunksize,
            alpha='auto',
            eta='auto',
            iterations=iterations,
            num_topics=num_topics,
            passes=passes,
            eval_every=eval_every
        )

        top_topics = model.top_topics(corpus) #, num_words=20)
        keywords = [item[1] for item in top_topics[0][0]]
        return keywords

# def drop_duplicated(scripts_df):
#     TIME_INDEX = 3
#     TEXT_INDEX = 1
#     scripts = scripts_df.values.tolist()

#     is_return = [True] * scripts_df.shape[0]
#     scripts_length = len(scripts)

#     for (i, target_script) in enumerate(scripts):
#         if not is_return[i]:
#             continue

#         target_sec = int(float(target_script[TIME_INDEX]))
#         target_text = target_script[TEXT_INDEX]

#         j = i + 1
#         last_dropped_sec = target_sec
#         while j < scripts_length:
#             script = scripts[j]
#             sec = int(float(script[TIME_INDEX]))
#             text = script[TEXT_INDEX]

#             if last_dropped_sec + 1 < sec:
#                 break

#             # 레벤슈타인 거리 / 문자열 길이 <= 0.25
#             # 다른 글자가 4개 중 1개 이하 수준이면 중복 텍스트로 간주함
#             if target_text == text or levenshtein_distance(target_text, text) / len(target_text) <= 0.25:
#                 is_return[j] = False
#                 last_dropped_sec = sec

#             j += 1
    
#     return scripts_df[is_return]


# def levenshtein_distance(s1, s2):
#     m, n = len(s1), len(s2)
#     dp = [[0] * (n + 1) for _ in range(m + 1)]

#     for i in range(m + 1):
#         dp[i][0] = i
#     for j in range(n + 1):
#         dp[0][j] = j

#     for i in range(1, m + 1):
#         for j in range(1, n + 1):
#             cost = 0 if s1[i - 1] == s2[j - 1] else 1
#             dp[i][j] = min(dp[i - 1][j] + 1,  # 삭제
#                            dp[i][j - 1] + 1,  # 삽입
#                            dp[i - 1][j - 1] + cost)  # 치환

#     return dp[m][n]


if __name__ == "__main__":
    url = 'https://www.youtube.com/watch?v=Vws4jvdUO1E%26ab_channel=1%EB%B6%84%EB%AF%B8%EB%A7%8C/' # 수박
    models = AiModel(url=url)
    # caption = models.get_captions()
    # caption.to_csv("caption.csv")
    #easyocr_result = models.get_easyocr_result()
    # easyocr_result.to_csv("easyocr_result.csv")
    whisper_result = models.get_whisper_result()
    #whisper_result.to_csv("whisper_result.csv")
