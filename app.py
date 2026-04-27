import os
from dotenv import load_dotenv
from openai import OpenAI

import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib.parse

# .env 파일에 기록된 환경변수를 불러옵니다.
load_dotenv()

# os.getenv를 통해 키 값을 가져옵니다.
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# 화면 넓게 설정
st.set_page_config(layout="wide")

def get_fortune_by_direct_url(zodiac_name):
    
    query = f"{zodiac_name} 운세" # ex) 쥐띠%20운세 -> %20은 공백(space)을 뜻함.
    encoded_query = urllib.parse.quote(query)
    
    url = f"https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&qvt=0&query={encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        fortune_text = soup.select_one('p.text._cs_fortune_text')
            
        if fortune_text:
            return fortune_text.get_text().strip()
        else:
            return "운세 텍스트를 찾지 못했습니다. 네이버가 데이터를 자바스크립트로 숨겼을 가능성이 큽니다."
            
    except Exception as e:
        return f"연결 오류: {e}"


def generate_amulet(fortune_text):
    # 운세 내용을 바탕으로 프롬프트 생성
    response = client.images.generate(
        model="dall-e-3",
        prompt=f"""
        A super cute and chubby oriental zodiac animal character based on: {fortune_text}.
        The character should be placed strictly in the CENTER with plenty of empty space around the edges to fit a circular profile picture frame.
        Style: Kawaii, 3D clay art style, soft pastel colors, warm lighting, high quality.
        Background: Simple, clean solid pastel background.
        Ensure no important parts are near the corners or edges.
        """,
        size="1024x1024",
        n=1
    )
    return response.data[0].url

# --- Streamlit UI ---
# --- 세션 상태 초기화 (반드시 UI 코드 시작점에 위치해야 함) ---
if 'fortune_result' not in st.session_state:
    st.session_state.fortune_result = None
if 'current_zodiac' not in st.session_state:
    st.session_state.current_zodiac = None

st.title("🧧 오늘의 운세&부적 생성기")

zodiac_list = ['쥐띠', '소띠', '호랑이띠', '토끼띠', '용띠', '뱀띠', '말띠', '양띠', '원숭이띠', '닭띠', '개띠', '돼지띠']
zodiac_name = st.selectbox("당신의 띠를 선택하세요. 해당 운세는 96, 84, 72, 60년생만 해당합니다.", zodiac_list)

if st.button("운세 바로 가져오기"):
    with st.spinner(f'{zodiac_name} 운세를 찾는 중...'):
        result = get_fortune_by_direct_url(zodiac_name)
        st.session_state.fortune_result = result # 결과를 세션에 저장하여 기억함
        
if st.session_state.fortune_result:
    st.success(f"[{zodiac_name}] 오늘의 운세")
    st.write(st.session_state.fortune_result)

    st.write("---")
    st.write("이 운세를 바탕으로 세상에 하나뿐인 행운 부적을 그려보시겠어요?")
    
    # [버튼 2] 부적 생성 (사용자가 원할 때만 API 호출)
    if st.button("✨ 나만의 행운 부적 그리기 (OpenAI API 사용)"):
        with st.spinner('AI가 운세의 기운을 담아 부적을 그리는 중...'):
            try:
                img_url = generate_amulet(st.session_state.fortune_result)
                st.image(img_url, caption=f"{zodiac_name}를 위한 행운 부적", width="stretch")
                # 1. DALL-E가 준 URL에서 실제 이미지 데이터를 다운로드 (메모리에 일시 저장)
                img_data = requests.get(img_url).content
                # 2. 다운로드 버튼 생성
                st.download_button(
                    label="🖼️ 부적 이미지 저장하기", # 버튼에 표시될 문구
                    data=img_data,                 # 위에서 받은 이미지 데이터
                    file_name=f"{zodiac_name}_행운부적.png", # 저장될 파일 이름
                    mime="image/png"               # 파일 형식 지정
                )
                st.balloons() # 축하 효과
            except Exception as e:
                        st.error(f"부적 생성 중 오류가 발생했습니다: {e}")
