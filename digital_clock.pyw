import tkinter as tk
from datetime import datetime, timedelta
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
        # 개별 종목 정보 저장
        self.individual_stocks = {}
        self.stock_codes = ['395270', '144600', '473640', '161510', '000660', '005930', '229200']

        # 투명도 설정
        self.alpha = self.load_alpha()

        # 창 설정
        self.root.overrideredirect(True)  # 제목표시줄 제거
        self.root.attributes('-topmost', True)  # 항상 위에
        self.root.attributes('-alpha', self.alpha)  # 반투명
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
            fg='#000000',
            bg='#ffffff',
            insertbackground='#000000',
            height=3,
            width=30,
            relief='flat',
            wrap='word'
        )
        self.memo_text.pack(pady=(5, 0))
        self.memo_text.bind('<KeyRelease>', self.save_memo)

        # 메모 불러오기
        self.load_memo()

        # 개별 종목 구분선
        self.stock_separator = tk.Frame(self.frame, bg='#00d9ff', height=1)
        self.stock_separator.pack(fill='x', pady=(10, 5))

        # 개별 종목 헤더 프레임 (제목 + 새로고침 버튼)
        self.stock_header_frame = tk.Frame(self.frame, bg='#1a1a2e')
        self.stock_header_frame.pack()

        # 개별 종목 라벨
        self.stock_title_label = tk.Label(
            self.stock_header_frame,
            text='MY STOCKS',
            font=('맑은 고딕', 9),
            fg='#00d9ff',
            bg='#1a1a2e'
        )
        self.stock_title_label.pack(side='left')

        # 새로고침 버튼
        self.refresh_btn = tk.Label(
            self.stock_header_frame,
            text=' [F5]',
            font=('맑은 고딕', 8),
            fg='#888888',
            bg='#1a1a2e',
            cursor='hand2'
        )
        self.refresh_btn.pack(side='left')
        self.refresh_btn.bind('<Button-1>', self.refresh_all_stocks)
        self.refresh_btn.bind('<Enter>', lambda e: self.refresh_btn.config(fg='#00d9ff'))
        self.refresh_btn.bind('<Leave>', lambda e: self.refresh_btn.config(fg='#888888'))

        # 개별 종목 라벨들 생성 (종목명 + 가격정보 분리)
        self.stock_labels = {}
        self.stock_frames = {}
        for code in self.stock_codes:
            # 각 종목을 담을 프레임
            row_frame = tk.Frame(self.frame, bg='#1a1a2e')
            row_frame.pack(fill='x', pady=1)

            # 종목명 라벨 (오른쪽 정렬, 고정 너비)
            name_label = tk.Label(
                row_frame,
                font=('맑은 고딕', 10),
                fg='#ffffff',
                bg='#1a1a2e',
                text=f'{code}',
                width=12,
                anchor='e'  # 오른쪽 정렬
            )
            name_label.pack(side='left')

            # 가격 정보 라벨 (왼쪽 정렬)
            price_label = tk.Label(
                row_frame,
                font=('맑은 고딕', 10),
                fg='#888888',
                bg='#1a1a2e',
                text=' 로딩중...',
                anchor='w'  # 왼쪽 정렬
            )
            price_label.pack(side='left')

            self.stock_frames[code] = row_frame
            self.stock_labels[code] = {'name': name_label, 'price': price_label}

        # 드래그 이벤트 바인딩
        drag_widgets = [self.frame, self.time_label, self.date_label,
                       self.day_label, self.kospi_label, self.kosdaq_label,
                       self.separator, self.memo_separator, self.memo_label,
                       self.stock_separator, self.stock_header_frame, self.stock_title_label]
        # 주식 프레임과 라벨들 추가
        for code in self.stock_codes:
            drag_widgets.append(self.stock_frames[code])
            drag_widgets.append(self.stock_labels[code]['name'])
            drag_widgets.append(self.stock_labels[code]['price'])
        for widget in drag_widgets:
            widget.bind('<Button-1>', self.start_move)
            widget.bind('<B1-Motion>', self.on_move)

        # 우클릭으로 닫기
        self.root.bind('<Button-3>', lambda e: self.root.destroy())

        # F5로 새로고침
        self.root.bind('<F5>', self.refresh_all_stocks)

        # 마우스 휠로 투명도 조절
        self.root.bind('<MouseWheel>', self.adjust_alpha)

        # 날씨 업데이트 시작
        self.update_weather()

        # 주식 지수 업데이트 시작
        self.update_stock()

        # 개별 종목 업데이트 시작
        self.update_individual_stocks()

        # 시계 업데이트 시작
        self.update_clock()

        # 화면 좌측 상단에 배치
        self.root.update_idletasks()
        x = 50
        y = 50
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

    def get_alpha_path(self):
        """투명도 설정 파일 경로 반환"""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'alpha.txt')

    def load_alpha(self):
        """저장된 투명도 불러오기"""
        try:
            alpha_path = self.get_alpha_path()
            if os.path.exists(alpha_path):
                with open(alpha_path, 'r') as f:
                    return float(f.read().strip())
        except:
            pass
        return 0.7  # 기본값

    def save_alpha(self):
        """투명도 설정 저장"""
        try:
            with open(self.get_alpha_path(), 'w') as f:
                f.write(str(self.alpha))
        except:
            pass

    def adjust_alpha(self, event):
        """마우스 휠로 투명도 조절"""
        # 휠 위로: 불투명하게, 휠 아래로: 투명하게
        if event.delta > 0:
            self.alpha = min(1.0, self.alpha + 0.05)
        else:
            self.alpha = max(0.2, self.alpha - 0.05)

        self.root.attributes('-alpha', self.alpha)
        self.save_alpha()

        # 현재 투명도를 시간 라벨에 일시적으로 표시
        self.time_label.config(text=f'{int(self.alpha * 100)}%')
        # 1초 후 시간으로 복원
        if hasattr(self, '_alpha_timer'):
            self.root.after_cancel(self._alpha_timer)
        self._alpha_timer = self.root.after(1000, self.update_clock)

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
        """기상청 API로 날씨 정보를 가져오는 함수"""
        try:
            # 기상청 API 키
            service_key = "60eeaa7e0daa6de920e664e2ae499b1424412363224ec49c63832ff5051a23cd"

            # 서울 격자 좌표
            nx, ny = 60, 127

            # 현재 시간 기준으로 base_date, base_time 계산
            now = datetime.now()
            # 정각 40분 이후에 데이터가 생성되므로 안전하게 1시간 전 사용
            if now.minute < 40:
                now = now - timedelta(hours=1)

            base_date = now.strftime('%Y%m%d')
            base_time = now.strftime('%H00')

            # 초단기실황 조회
            url = f"http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst?serviceKey={service_key}&numOfRows=10&pageNo=1&dataType=JSON&base_date={base_date}&base_time={base_time}&nx={nx}&ny={ny}"

            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

                items = data['response']['body']['items']['item']

                temp = None
                pty = '0'  # 강수형태

                for item in items:
                    if item['category'] == 'T1H':  # 기온
                        temp = item['obsrValue']
                    elif item['category'] == 'PTY':  # 강수형태
                        pty = item['obsrValue']

                if temp is not None:
                    weather_desc = self.get_weather_korean(pty)
                    self.weather_text = f"서울 {temp}°C {weather_desc}"

                    # 날씨 로드 후 즉시 화면 업데이트
                    self.root.after(0, self.update_display)
        except Exception as e:
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

    def get_weather_korean(self, pty_code):
        """기상청 강수형태(PTY) 코드를 한글로 변환"""
        weather_map = {
            '0': '맑음 ☀',      # 없음
            '1': '비 🌧',        # 비
            '2': '비/눈 🌨',     # 비/눈
            '3': '눈 ❄',        # 눈
            '5': '빗방울 🌧',    # 빗방울
            '6': '눈날림 🌨',    # 빗방울눈날림
            '7': '눈날림 ❄',    # 눈날림
        }
        return weather_map.get(str(pty_code), '☀')

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

    def fetch_individual_stocks(self):
        """개별 종목 정보를 가져오는 함수"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            for code in self.stock_codes:
                # 이미 성공한 종목은 다시 시도
                # 실패한 종목도 재시도
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        url = f"https://m.stock.naver.com/api/stock/{code}/basic"
                        req = urllib.request.Request(url, headers=headers)
                        with urllib.request.urlopen(req, timeout=10) as response:
                            data = json.loads(response.read().decode('utf-8'))

                        name = data.get('stockName', code)
                        price = data.get('closePrice', '0')
                        change = data.get('compareToPreviousClosePrice', '0')
                        rate = data.get('fluctuationsRatio', '0')

                        arrow = "▲" if float(change) > 0 else "▼" if float(change) < 0 else ""
                        color = "up" if float(change) > 0 else "down" if float(change) < 0 else "flat"

                        self.individual_stocks[code] = {
                            'name': name,
                            'price': price,
                            'change': abs(float(change)),
                            'rate': rate,
                            'arrow': arrow,
                            'color': color
                        }
                        break  # 성공하면 재시도 루프 종료
                    except Exception:
                        if attempt == max_retries - 1:
                            # 마지막 시도도 실패하면 에러 상태 저장
                            self.individual_stocks[code] = {
                                'name': f'[{code}]',
                                'price': '-',
                                'change': 0,
                                'rate': '-',
                                'arrow': '',
                                'color': 'error'
                            }
                        else:
                            # 재시도 전 잠시 대기
                            import time
                            time.sleep(0.5)

            # 화면 업데이트
            self.root.after(0, self.update_individual_stocks_display)
        except:
            pass

    def update_individual_stocks_display(self):
        """개별 종목 화면 업데이트"""
        for code, labels in self.stock_labels.items():
            name_label = labels['name']
            price_label = labels['price']

            if code in self.individual_stocks:
                stock = self.individual_stocks[code]
                if stock['color'] == 'error':
                    # 에러 상태 표시
                    name_label.config(text=stock['name'], fg='#888888')
                    price_label.config(text=' 로딩 실패', fg='#888888')
                else:
                    # 종목명
                    name_label.config(text=stock['name'], fg='#ffffff')
                    # 가격 정보
                    price_text = f"  {stock['price']}  {stock['arrow']}{stock['change']:.0f} ({stock['rate']}%)"
                    price_label.config(text=price_text)

                    if stock['color'] == 'up':
                        price_label.config(fg='#ff6b6b')  # 빨간색 (상승)
                    elif stock['color'] == 'down':
                        price_label.config(fg='#4dabf7')  # 파란색 (하락)
                    else:
                        price_label.config(fg='#ffffff')  # 흰색 (보합)

    def update_individual_stocks(self):
        """백그라운드에서 개별 종목 업데이트"""
        thread = threading.Thread(target=self.fetch_individual_stocks, daemon=True)
        thread.start()
        # 1분마다 업데이트
        self.root.after(60000, self.update_individual_stocks)

    def refresh_all_stocks(self, event=None):
        """모든 주식 정보 새로고침"""
        # 새로고침 중 표시
        self.refresh_btn.config(text=' 로딩...', fg='#ffcc00')

        # 종목 라벨들 로딩 상태로 변경
        for code, labels in self.stock_labels.items():
            labels['name'].config(text=code, fg='#888888')
            labels['price'].config(text=' 로딩중...', fg='#888888')

        # KOSPI/KOSDAQ도 로딩 상태로
        self.kospi_label.config(text='KOSPI 로딩중...', fg='#888888')
        self.kosdaq_label.config(text='KOSDAQ 로딩중...', fg='#888888')

        # 기존 데이터 초기화
        self.individual_stocks = {}
        self.stock_info = None

        # 백그라운드에서 데이터 가져오기
        def fetch_all():
            self.fetch_stock()
            self.fetch_individual_stocks()
            # 완료 후 버튼 복원
            self.root.after(0, lambda: self.refresh_btn.config(text=' [F5]', fg='#888888'))

        thread = threading.Thread(target=fetch_all, daemon=True)
        thread.start()

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
