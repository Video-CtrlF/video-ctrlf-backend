from easyocr import Reader
from pytube import YouTube

import time
import pandas as pd
import cv2
import whisper
import joblib

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
        self.easyocr_results = pd.DataFrame(columns=["bbox", "text", "conf", "time"])
        self.whisper_results = pd.DataFrame(columns=["start", "end", "text"])
        self.fps = None
        self.frame_count = None


    def get_captions(self):
        """
        YouTube에서 제공하는 자막 정보 받기
        return: pd.DataFrame
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
        return self.caption_df
    def get_easyocr_result(self):
        """
        easyocr을 통해 동영상에서 Text 추출
        return: pd.DataFrame
        """
        print("EasyOCR Start!!")
        easyocr_model = joblib.load("ai_model/models/easyocr_base_model.pkl")
        cap = cv2.VideoCapture(self.video_url)
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) # 프레임 개수
        print("fps :", self.fps)
        print("frame_count :", self.frame_count)
        # images = []
        # while True:
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
            # images.append(frame)
            result = pd.DataFrame(easyocr_model.readtext(frame, detail=1), columns=['bbox', 'text', 'conf'])
            result['time'] = frame_pos / self.fps 
            self.easyocr_results = pd.concat([self.easyocr_results, result], ignore_index=True)
            # if count // self.fps >= 5: # 5초까지
            #     break
        print("EasyOCR Done!!")
        return self.easyocr_results

    def get_whisper_result(self):
        """
        Whisper를 통해 동영상 오디오에서 Text 추출
        return: pd.DataFrame
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
        print('Whisper Done!!')
        return self.whisper_results
    
if __name__ == "__main__":
    url = 'https://www.youtube.com/watch?v=bGcVkNP1tPs&t=2s&ab_channel=1%EB%B6%84%EB%AF%B8%EB%A7%8C'
    models = AiModel(url=url)
    caption = models.get_captions()
    caption.to_csv("caption.csv")
    easyocr_result = models.get_easyocr_result()
    easyocr_result.to_csv("easyocr_result.csv")
    whisper_result = models.get_whisper_result()
    whisper_result.to_csv("whisper_result.csv")
