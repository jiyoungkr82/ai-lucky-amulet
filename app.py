import os
from dotenv import load_dotenv
from openai import OpenAI

import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib.parse
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

# .env 파일에 기록된 환경변수를 불러옵니다.
load_dotenv()

# os.getenv를 통해 키 값을 가져옵니다.
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# 화면 넓게 설정
st.set_page_config(layout="wide")

def get_fortune_by_direct_url(zodiac_name, target_index):
    
    query = f"{zodiac_name} 운세" # ex) 쥐띠%20운세 -> %20은 공백(space)을 뜻함.
    encoded_query = urllib.parse.quote(query)
    
    url = f"https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&qvt=0&query={encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.naver.com"
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        logging.info(soup.get_text)
        
        # 공통 운세 내용 추출
        fortune_text_el = soup.select_one('p.text._cs_fortune_text')
        # 상세 항목 리스트 추출
        fortune_detail_list = soup.select('dl.lst_infor._cs_fortune_list > div')
            
        if fortune_text_el and len(fortune_detail_list) > target_index:
            common_text = fortune_text_el.get_text(strip=True)
            # 인덱스에 해당하는 상세 운세(dd 태그) 가져오기
            detail_text = fortune_detail_list[target_index].select_one('dd').get_text(strip=True)
            
            # 두 내용을 합쳐서 반환 (가독성을 위해 줄바꿈 추가)
            return f"{common_text}\n\n[상세 운세]\n{detail_text}"
        else:
            logging.error(f"HTML 구조 변경 감지: {url}")
            return "운세 정보를 찾을 수 없습니다. (네이버 페이지 구조 변경 가능성)"
            
    except Exception as e:
        logging.error(f"에러 발생: {e}")
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

zodiac_ages = {
    "쥐띠": [1996, 1984, 1972, 1960],
    "소띠": [1997, 1985, 1973, 1961],
    "호랑이띠": [1998, 1986, 1974, 1962],
    "토끼띠": [1999, 1987, 1975, 1963],
    "용띠": [1988, 1976, 1964, 1952],
    "뱀띠": [1989, 1977, 1965, 1953],
    "말띠": [1990, 1978, 1966, 1954],
    "양띠": [1991, 1979, 1967, 1955],
    "원숭이띠": [1992, 1980, 1968, 1956],
    "닭띠": [1993, 1981, 1969, 1957],
    "개띠": [1994, 1982, 1970, 1958],
    "돼지띠": [1995, 1983, 1971, 1959]
}

zodiac_list = list(zodiac_ages.keys())
zodiac_name = st.selectbox("당신의 띠를 선택하세요.", zodiac_list)

age_list = zodiac_ages[zodiac_name]

# 선택된 띠에 해당하는 연도들만 다시 선택박스로 제공
selected_year = st.selectbox(
    f"{zodiac_name}의 출생 연도를 선택하세요", 
    age_list
)

target_index = age_list.index(selected_year)

if st.button("운세 바로 가져오기"):
    with st.spinner(f'{zodiac_name} 운세를 찾는 중...'):
        result = get_fortune_by_direct_url(zodiac_name, target_index)
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
                        # st.error(f"부적 생성 중 오류가 발생했습니다: {e}")
                        if "insufficient_quota" in str(e) or "rate_limit" in str(e):
                            st.warning("🔮 오늘 준비된 행운 부적이 모두 소진되었습니다. 내일 다시 시도해 주세요!")
                        else:
                            # 그 외 일반적인 에러 발생 시
                            st.error(f"부적 생성 중 잠시 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")
                            
