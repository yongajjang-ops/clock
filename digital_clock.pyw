import tkinter as tk
from datetime import datetime
import urllib.request
import json
import threading
import os

class DigitalClock:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("디지털 시계")

        # 날씨 정보 저장
        self.weather_text = ""
        # 주식 지수 저장
        self.stock_info = None

        # 창 설정
        self.root.overrideredirect(True)  # 제목표시줄 제거
        self.root.attributes('-topmost', True)  # 항상 위에
        self.root.attributes('-alpha', 0.7)  # 반투명
        self.root.configure(bg='#1a1a2e')

        # 드래그 이동을 위한 변수
        self.x = None
        self.y = None

        # 메인 프레임
        self.frame = tk.Frame(self.root, bg='#1a1a2e', padx=20, pady=15)
        self.frame.pack()

        # 시간 라벨
        self.time_label = tk.Label(
            self.frame,
            font=('Consolas', 60, 'bold'),
            fg='#00d9ff',
            bg='#1a1a2e'
        )
        self.time_label.pack()

        # 날짜 라벨
        self.date_label = tk.Label(
            self.frame,
            font=('맑은 고딕', 14),
            fg='#ffffff',
            bg='#1a1a2e'
        )
        self.date_label.pack(pady=(5, 0))

        # 요일 + 날씨 라벨
        self.day_label = tk.Label(
            self.frame,
            font=('맑은 고딕', 11),
            fg='#00d9ff',
            bg='#1a1a2e'
        )
        self.day_label.pack()

        # 구분선
        self.separator = tk.Frame(self.frame, bg='#00d9ff', height=1)
        self.separator.pack(fill='x', pady=(10, 5))

        # KOSPI 라벨
        self.kospi_label = tk.Label(
            self.frame,
            font=('맑은 고딕', 11),
            fg='#ffffff',
            bg='#1a1a2e'
        )
        self.kospi_label.pack()

        # KOSDAQ 라벨
        self.kosdaq_label = tk.Label(
            self.frame,
            font=('맑은 고딕', 11),
            fg='#ffffff',
            bg='#1a1a2e'
        )
        self.kosdaq_label.pack()

        # 메모 구분선
        self.memo_separator = tk.Frame(self.frame, bg='#00d9ff', height=1)
        self.memo_separator.pack(fill='x', pady=(10, 5))

        # 메모 라벨
        self.memo_label = tk.Label(
            self.frame,
            text='MEMO',
            font=('맑은 고딕', 9),
            fg='#00d9ff',
            bg='#1a1a2e'
        )
        self.memo_label.pack()

        # 메모 입력 필드
        self.memo_text = tk.Text(
            self.frame,
            font=('맑은 고딕', 10),
            fg='#ffffff',
            bg='#252540',
            insertbackground='#00d9ff',
            height=3,
            width=30,
            relief='flat',
            wrap='word'
        )
        self.memo_text.pack(pady=(5, 0))
        self.memo_text.bind('<KeyRelease>', self.save_memo)

        # 메모 불러오기
        self.load_memo()

        # 드래그 이벤트 바인딩
        for widget in [self.frame, self.time_label, self.date_label,
                       self.day_label, self.kospi_label, self.kosdaq_label,
                       self.separator, self.memo_separator, self.memo_label]:
            widget.bind('<Button-1>', self.start_move)
            widget.bind('<B1-Motion>', self.on_move)

        # 우클릭으로 닫기
        self.root.bind('<Button-3>', lambda e: self.root.destroy())

        # 날씨 업데이트 시작
        self.update_weather()

        # 주식 지수 업데이트 시작
        self.update_stock()

        # 시계 업데이트 시작
        self.update_clock()

        # 화면 우측 하단에 배치
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        x = screen_width - window_width - 50
        y = screen_height - window_height - 100
        self.root.geometry(f'+{x}+{y}')

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        new_x = self.root.winfo_x() + deltax
        new_y = self.root.winfo_y() + deltay
        self.root.geometry(f'+{new_x}+{new_y}')

    def get_memo_path(self):
        """메모 파일 경로 반환"""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'memo.txt')

    def save_memo(self, event=None):
        """메모 내용을 파일에 저장"""
        try:
            content = self.memo_text.get('1.0', 'end-1c')
            with open(self.get_memo_path(), 'w', encoding='utf-8') as f:
                f.write(content)
        except:
            pass

    def load_memo(self):
        """파일에서 메모 내용 불러오기"""
        try:
            memo_path = self.get_memo_path()
            if os.path.exists(memo_path):
                with open(memo_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.memo_text.insert('1.0', content)
        except:
            pass

    def fetch_weather(self):
        """날씨 정보를 가져오는 함수"""
        try:
            # wttr.in API 사용 (IP 기반 자동 위치)
            url = "https://wttr.in/?format=j1"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

                current = data['current_condition'][0]
                temp = current['temp_C']

                # 지역명 가져오기
                area = data['nearest_area'][0]
                area_name = area.get('areaName', [{}])[0].get('value', '')

                # 날씨 상태를 한글로 변환
                weather_code = current['weatherCode']
                weather_desc = self.get_weather_korean(weather_code)

                self.weather_text = f"{area_name} {temp}°C {weather_desc}"

                # 날씨 로드 후 즉시 화면 업데이트
                self.root.after(0, self.update_display)
        except:
            self.weather_text = ""

    def fetch_stock(self):
        """KOSPI/KOSDAQ 지수를 가져오는 함수"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}

            # KOSPI
            kospi_url = "https://m.stock.naver.com/api/index/KOSPI/basic"
            req = urllib.request.Request(kospi_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                kospi_data = json.loads(response.read().decode('utf-8'))

            # KOSDAQ
            kosdaq_url = "https://m.stock.naver.com/api/index/KOSDAQ/basic"
            req = urllib.request.Request(kosdaq_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                kosdaq_data = json.loads(response.read().decode('utf-8'))

            # KOSPI 정보
            kospi_price = kospi_data.get('closePrice', '')
            kospi_change = kospi_data.get('compareToPreviousClosePrice', '')
            kospi_rate = kospi_data.get('fluctuationsRatio', '')

            # KOSDAQ 정보
            kosdaq_price = kosdaq_data.get('closePrice', '')
            kosdaq_change = kosdaq_data.get('compareToPreviousClosePrice', '')
            kosdaq_rate = kosdaq_data.get('fluctuationsRatio', '')

            # 등락 표시
            kospi_arrow = "▲" if float(kospi_change) > 0 else "▼" if float(kospi_change) < 0 else ""
            kosdaq_arrow = "▲" if float(kosdaq_change) > 0 else "▼" if float(kosdaq_change) < 0 else ""

            kospi_color = "up" if float(kospi_change) > 0 else "down" if float(kospi_change) < 0 else "flat"
            kosdaq_color = "up" if float(kosdaq_change) > 0 else "down" if float(kosdaq_change) < 0 else "flat"

            self.stock_info = {
                'kospi': {'price': kospi_price, 'change': abs(float(kospi_change)), 'rate': kospi_rate, 'arrow': kospi_arrow, 'color': kospi_color},
                'kosdaq': {'price': kosdaq_price, 'change': abs(float(kosdaq_change)), 'rate': kosdaq_rate, 'arrow': kosdaq_arrow, 'color': kosdaq_color}
            }

            # 주식 로드 후 즉시 화면 업데이트
            self.root.after(0, self.update_stock_display)
        except Exception as e:
            self.stock_info = None

    def update_stock_display(self):
        """주식 지수 화면 업데이트"""
        if hasattr(self, 'stock_info') and self.stock_info:
            # KOSPI
            kospi = self.stock_info['kospi']
            kospi_text = f"KOSPI  {kospi['price']}  {kospi['arrow']}{kospi['change']:.2f} ({kospi['rate']}%)"
            self.kospi_label.config(text=kospi_text)
            if kospi['color'] == 'up':
                self.kospi_label.config(fg='#ff6b6b')  # 빨간색 (상승)
            elif kospi['color'] == 'down':
                self.kospi_label.config(fg='#4dabf7')  # 파란색 (하락)
            else:
                self.kospi_label.config(fg='#ffffff')  # 흰색 (보합)

            # KOSDAQ
            kosdaq = self.stock_info['kosdaq']
            kosdaq_text = f"KOSDAQ  {kosdaq['price']}  {kosdaq['arrow']}{kosdaq['change']:.2f} ({kosdaq['rate']}%)"
            self.kosdaq_label.config(text=kosdaq_text)
            if kosdaq['color'] == 'up':
                self.kosdaq_label.config(fg='#ff6b6b')  # 빨간색 (상승)
            elif kosdaq['color'] == 'down':
                self.kosdaq_label.config(fg='#4dabf7')  # 파란색 (하락)
            else:
                self.kosdaq_label.config(fg='#ffffff')  # 흰색 (보합)

    def update_display(self):
        """화면 즉시 업데이트"""
        days = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
        now = datetime.now()
        day_str = days[now.weekday()]
        if self.weather_text:
            self.day_label.config(text=f"{day_str}  |  {self.weather_text}")

    def get_weather_korean(self, code):
        """날씨 코드를 한글로 변환"""
        weather_map = {
            '113': '맑음 ☀',
            '116': '구름조금 ⛅',
            '119': '흐림 ☁',
            '122': '흐림 ☁',
            '143': '안개 🌫',
            '176': '비 🌧',
            '179': '눈 🌨',
            '182': '진눈깨비 🌨',
            '185': '진눈깨비 🌨',
            '200': '천둥번개 ⛈',
            '227': '눈 🌨',
            '230': '폭설 ❄',
            '248': '안개 🌫',
            '260': '안개 🌫',
            '263': '이슬비 🌧',
            '266': '이슬비 🌧',
            '281': '비 🌧',
            '284': '비 🌧',
            '293': '비 🌧',
            '296': '비 🌧',
            '299': '비 🌧',
            '302': '비 🌧',
            '305': '폭우 🌧',
            '308': '폭우 🌧',
            '311': '비 🌧',
            '314': '비 🌧',
            '317': '진눈깨비 🌨',
            '320': '눈 🌨',
            '323': '눈 🌨',
            '326': '눈 🌨',
            '329': '눈 🌨',
            '332': '눈 🌨',
            '335': '폭설 ❄',
            '338': '폭설 ❄',
            '350': '우박 🌨',
            '353': '비 🌧',
            '356': '폭우 🌧',
            '359': '폭우 🌧',
            '362': '진눈깨비 🌨',
            '365': '진눈깨비 🌨',
            '368': '눈 🌨',
            '371': '눈 🌨',
            '374': '우박 🌨',
            '377': '우박 🌨',
            '386': '천둥번개 ⛈',
            '389': '천둥번개 ⛈',
            '392': '천둥눈 ⛈',
            '395': '폭설 ❄',
        }
        return weather_map.get(code, '🌡')

    def update_weather(self):
        """백그라운드에서 날씨 정보 업데이트"""
        thread = threading.Thread(target=self.fetch_weather, daemon=True)
        thread.start()
        # 10분마다 날씨 업데이트
        self.root.after(600000, self.update_weather)

    def update_stock(self):
        """백그라운드에서 주식 지수 업데이트"""
        thread = threading.Thread(target=self.fetch_stock, daemon=True)
        thread.start()
        # 1분마다 주식 업데이트
        self.root.after(60000, self.update_stock)

    def update_clock(self):
        days = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
        now = datetime.now()

        time_str = now.strftime('%H:%M')
        date_str = now.strftime('%Y년 %m월 %d일')
        day_str = days[now.weekday()]

        # 요일 + 날씨 표시
        if self.weather_text:
            day_weather_str = f"{day_str}  |  {self.weather_text}"
        else:
            day_weather_str = day_str

        self.time_label.config(text=time_str)
        self.date_label.config(text=date_str)
        self.day_label.config(text=day_weather_str)

        # 1초마다 업데이트
        self.root.after(1000, self.update_clock)

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    clock = DigitalClock()
    clock.run()
