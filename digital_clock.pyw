import tkinter as tk
from datetime import datetime, timedelta
import urllib.request
import json
import threading
import os
import html
import re

class DigitalClock:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("디지털 시계")

        # 날씨 정보 저장
        self.weather_text = ""
        # 24시간 온도 데이터 저장
        self.hourly_temps = []
        # 주식 지수 저장
        self.stock_info = None
        # 개별 종목 정보 저장
        self.individual_stocks = {}
        self.default_stock_codes = ['395270', '144600', '473640', '161510', '000660', '005930', '229200']
        self.stock_codes = self.load_stock_codes()
        # 반도체 뉴스 저장
        self.semiconductor_news = []

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

        # 24시간 온도 그래프 캔버스
        self.temp_canvas = tk.Canvas(
            self.frame,
            width=280,
            height=60,
            bg='#1a1a2e',
            highlightthickness=0
        )
        self.temp_canvas.pack(pady=(5, 0))

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
            height=4,
            width=40,
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

        # 설정 버튼
        self.settings_btn = tk.Label(
            self.stock_header_frame,
            text=' [설정]',
            font=('맑은 고딕', 8),
            fg='#888888',
            bg='#1a1a2e',
            cursor='hand2'
        )
        self.settings_btn.pack(side='left')
        self.settings_btn.bind('<Button-1>', self.open_stock_settings)
        self.settings_btn.bind('<Enter>', lambda e: self.settings_btn.config(fg='#00d9ff'))
        self.settings_btn.bind('<Leave>', lambda e: self.settings_btn.config(fg='#888888'))

        # 개별 종목 라벨들 생성 (종목명 + 가격정보 분리)
        self.stock_labels = {}
        self.stock_frames = {}
        for code in self.stock_codes:
            # 각 종목을 담을 프레임
            row_frame = tk.Frame(self.frame, bg='#1a1a2e')
            row_frame.pack(fill='x', pady=1, padx=(15, 0))

            # 종목명 라벨 (오른쪽 정렬, 고정 너비)
            name_label = tk.Label(
                row_frame,
                font=('맑은 고딕', 10),
                fg='#ffffff',
                bg='#1a1a2e',
                text=f'{code}',
                width=14,
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

        # 뉴스 구분선
        self.news_separator = tk.Frame(self.frame, bg='#00d9ff', height=1)
        self.news_separator.pack(fill='x', pady=(10, 5))

        # 뉴스 헤더 프레임
        self.news_header_frame = tk.Frame(self.frame, bg='#1a1a2e')
        self.news_header_frame.pack()

        # 뉴스 제목 라벨
        self.news_title_label = tk.Label(
            self.news_header_frame,
            text='SEMICONDUCTOR NEWS',
            font=('맑은 고딕', 9),
            fg='#00d9ff',
            bg='#1a1a2e'
        )
        self.news_title_label.pack(side='left')

        # 뉴스 새로고침 버튼
        self.news_refresh_btn = tk.Label(
            self.news_header_frame,
            text=' [새로고침]',
            font=('맑은 고딕', 8),
            fg='#888888',
            bg='#1a1a2e',
            cursor='hand2'
        )
        self.news_refresh_btn.pack(side='left')
        self.news_refresh_btn.bind('<Button-1>', self.refresh_news)
        self.news_refresh_btn.bind('<Enter>', lambda e: self.news_refresh_btn.config(fg='#00d9ff'))
        self.news_refresh_btn.bind('<Leave>', lambda e: self.news_refresh_btn.config(fg='#888888'))

        # 뉴스 라벨들 (5개)
        self.news_labels = []
        for i in range(5):
            news_label = tk.Label(
                self.frame,
                font=('맑은 고딕', 9),
                fg='#cccccc',
                bg='#1a1a2e',
                text='뉴스 로딩중...' if i == 0 else '',
                anchor='w',
                cursor='hand2'
            )
            news_label.pack(fill='x', pady=1, padx=5)
            news_label.bind('<Enter>', lambda e, lbl=news_label: lbl.config(fg='#00d9ff'))
            news_label.bind('<Leave>', lambda e, lbl=news_label: lbl.config(fg='#cccccc'))
            self.news_labels.append(news_label)

        # 드래그 이벤트 바인딩
        drag_widgets = [self.frame, self.time_label, self.date_label,
                       self.day_label, self.temp_canvas, self.kospi_label, self.kosdaq_label,
                       self.separator, self.memo_separator, self.memo_label,
                       self.stock_separator, self.stock_header_frame, self.stock_title_label,
                       self.news_separator, self.news_header_frame, self.news_title_label]
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

        # 24시간 온도 예보 업데이트 시작
        self.update_hourly_temps()

        # 주식 지수 업데이트 시작
        self.update_stock()

        # 개별 종목 업데이트 시작
        self.update_individual_stocks()

        # 반도체 뉴스 업데이트 시작
        self.update_news()

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

    def get_stock_codes_path(self):
        """종목 코드 파일 경로 반환"""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stocks.txt')

    def get_stock_cache_path(self):
        """주식 캐시 파일 경로 반환"""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stock_cache.json')

    def load_stock_cache(self):
        """저장된 주식 캐시 불러오기"""
        try:
            cache_path = self.get_stock_cache_path()
            if os.path.exists(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}

    def save_stock_cache(self):
        """주식 캐시 저장"""
        try:
            with open(self.get_stock_cache_path(), 'w', encoding='utf-8') as f:
                json.dump(self.individual_stocks, f, ensure_ascii=False, indent=2)
        except:
            pass

    def load_stock_codes(self):
        """저장된 종목 코드 불러오기"""
        try:
            path = self.get_stock_codes_path()
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    codes = [line.strip() for line in f.readlines() if line.strip()]
                    if codes:
                        return codes
        except:
            pass
        return self.default_stock_codes.copy()

    def save_stock_codes(self):
        """종목 코드 저장"""
        try:
            with open(self.get_stock_codes_path(), 'w', encoding='utf-8') as f:
                for code in self.stock_codes:
                    f.write(code + '\n')
        except:
            pass

    def open_stock_settings(self, event=None):
        """종목 코드 설정 창 열기"""
        # 설정 창 생성
        settings_win = tk.Toplevel(self.root)
        settings_win.title("종목 설정")
        settings_win.geometry("300x450")
        settings_win.configure(bg='#1a1a2e')
        settings_win.attributes('-topmost', True)

        # 안내 라벨
        tk.Label(
            settings_win,
            text="종목 코드 (한 줄에 하나씩)",
            font=('맑은 고딕', 10),
            fg='#00d9ff',
            bg='#1a1a2e'
        ).pack(pady=(15, 5))

        # 버튼 프레임 (하단에 먼저 배치)
        btn_frame = tk.Frame(settings_win, bg='#1a1a2e')
        btn_frame.pack(side='bottom', pady=15)

        # 텍스트 입력 영역
        text_frame = tk.Frame(settings_win, bg='#1a1a2e')
        text_frame.pack(fill='both', expand=True, padx=15, pady=5)

        text_input = tk.Text(
            text_frame,
            font=('Consolas', 11),
            fg='#ffffff',
            bg='#2a2a4e',
            insertbackground='#ffffff',
            relief='flat',
            wrap='word'
        )
        text_input.pack(fill='both', expand=True)

        # 현재 종목 코드 표시
        text_input.insert('1.0', '\n'.join(self.stock_codes))

        def save_and_close():
            # 새 종목 코드 가져오기
            content = text_input.get('1.0', 'end-1c')
            new_codes = [line.strip() for line in content.split('\n') if line.strip()]

            if new_codes:
                self.stock_codes = new_codes
                self.save_stock_codes()
                self.rebuild_stock_labels()
                self.refresh_all_stocks()

            settings_win.destroy()

        def reset_to_default():
            text_input.delete('1.0', 'end')
            text_input.insert('1.0', '\n'.join(self.default_stock_codes))

        # 저장 버튼
        save_btn = tk.Button(
            btn_frame,
            text="저장",
            font=('맑은 고딕', 10),
            fg='#ffffff',
            bg='#00d9ff',
            activebackground='#00b8d4',
            relief='flat',
            width=8,
            command=save_and_close
        )
        save_btn.pack(side='left', padx=5)

        # 초기화 버튼
        reset_btn = tk.Button(
            btn_frame,
            text="기본값",
            font=('맑은 고딕', 10),
            fg='#ffffff',
            bg='#666666',
            activebackground='#888888',
            relief='flat',
            width=8,
            command=reset_to_default
        )
        reset_btn.pack(side='left', padx=5)

        # 취소 버튼
        cancel_btn = tk.Button(
            btn_frame,
            text="취소",
            font=('맑은 고딕', 10),
            fg='#ffffff',
            bg='#666666',
            activebackground='#888888',
            relief='flat',
            width=8,
            command=settings_win.destroy
        )
        cancel_btn.pack(side='left', padx=5)

    def rebuild_stock_labels(self):
        """종목 라벨 재생성"""
        # 기존 라벨들 제거
        for code in list(self.stock_frames.keys()):
            self.stock_frames[code].destroy()

        self.stock_labels = {}
        self.stock_frames = {}
        self.individual_stocks = {}

        # 새 라벨들 생성 (뉴스 섹션 앞에 배치)
        for code in self.stock_codes:
            row_frame = tk.Frame(self.frame, bg='#1a1a2e')
            row_frame.pack(fill='x', pady=1, padx=(15, 0), before=self.news_separator)

            name_label = tk.Label(
                row_frame,
                font=('맑은 고딕', 10),
                fg='#ffffff',
                bg='#1a1a2e',
                text=f'{code}',
                width=14,
                anchor='e'
            )
            name_label.pack(side='left')

            price_label = tk.Label(
                row_frame,
                font=('맑은 고딕', 10),
                fg='#888888',
                bg='#1a1a2e',
                text=' 로딩중...',
                anchor='w'
            )
            price_label.pack(side='left')

            self.stock_frames[code] = row_frame
            self.stock_labels[code] = {'name': name_label, 'price': price_label}

            # 드래그 이벤트 바인딩
            for widget in [row_frame, name_label, price_label]:
                widget.bind('<Button-1>', self.start_move)
                widget.bind('<B1-Motion>', self.on_move)

    def get_memo_path(self):
        """메모 파일 경로 반환"""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'memo.txt')

    def starts_with_date(self, text):
        """텍스트가 날짜 형식(YYYY.MM.DD)으로 시작하는지 확인"""
        import re
        return bool(re.match(r'^\d{4}\.\d{2}\.\d{2}', text.strip()))

    def save_memo(self, event=None):
        """메모 내용을 파일에 저장"""
        try:
            content = self.memo_text.get('1.0', 'end-1c')
            with open(self.get_memo_path(), 'w', encoding='utf-8') as f:
                f.write(content)
        except:
            pass

    def load_memo(self):
        """파일에서 메모 내용 불러오기, 앱 시작 시 오늘 날짜 표시"""
        try:
            memo_path = self.get_memo_path()
            content = ""
            if os.path.exists(memo_path):
                with open(memo_path, 'r', encoding='utf-8') as f:
                    content = f.read()

            # 오늘 날짜
            today_date = datetime.now().strftime('%Y.%m.%d ')

            # 날짜로 시작하지 않으면 오늘 날짜를 앞에 추가
            if not self.starts_with_date(content):
                content = today_date + content.lstrip()

            self.memo_text.insert('1.0', content)
            # 커서를 맨 뒤로 이동
            self.memo_text.mark_set('insert', 'end-1c')
        except:
            # 에러 시에도 오늘 날짜는 표시
            today_date = datetime.now().strftime('%Y.%m.%d ')
            self.memo_text.insert('1.0', today_date)

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
        """네이버에서 KOSPI/KOSDAQ 지수를 가져오는 함수"""
        import time

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://m.stock.naver.com/',
                'Origin': 'https://m.stock.naver.com',
            }

            # KOSPI
            kospi_url = "https://m.stock.naver.com/api/index/KOSPI/basic"
            req = urllib.request.Request(kospi_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                kospi_data = json.loads(response.read().decode('utf-8'))

            time.sleep(0.3)

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

    def fetch_hourly_temps(self):
        """기상청 단기예보 API로 24시간 온도 데이터를 가져오는 함수"""
        try:
            service_key = "60eeaa7e0daa6de920e664e2ae499b1424412363224ec49c63832ff5051a23cd"
            nx, ny = 60, 127

            # base_time 계산 (02, 05, 08, 11, 14, 17, 20, 23시)
            now = datetime.now()
            base_times = [2, 5, 8, 11, 14, 17, 20, 23]

            # 현재 시간에서 가장 가까운 이전 base_time 찾기
            current_hour = now.hour
            base_hour = 23  # 기본값
            base_date = now

            for bt in reversed(base_times):
                if current_hour >= bt + 1:  # 발표 후 1시간 여유
                    base_hour = bt
                    break
            else:
                # 현재 시간이 03시 이전이면 전날 23시 사용
                base_hour = 23
                base_date = now - timedelta(days=1)

            base_date_str = base_date.strftime('%Y%m%d')
            base_time_str = f'{base_hour:02d}00'

            url = f"http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst?serviceKey={service_key}&numOfRows=300&pageNo=1&dataType=JSON&base_date={base_date_str}&base_time={base_time_str}&nx={nx}&ny={ny}"

            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))

                items = data['response']['body']['items']['item']

                # TMP(기온) 데이터만 추출하고 시간순 정렬
                temps = []
                for item in items:
                    if item['category'] == 'TMP':
                        fcst_date = item['fcstDate']
                        fcst_time = item['fcstTime']
                        temp_value = int(item['fcstValue'])
                        temps.append({
                            'datetime': f"{fcst_date}{fcst_time}",
                            'hour': fcst_time[:2],
                            'temp': temp_value
                        })

                # 시간순 정렬
                temps.sort(key=lambda x: x['datetime'])

                # 현재 시간 기준으로 필터링 (현재 시간 이후 데이터만)
                current_datetime = now.strftime('%Y%m%d%H00')
                temps = [t for t in temps if t['datetime'] >= current_datetime]

                # 24개만 사용
                self.hourly_temps = temps[:24]

                # 그래프 업데이트
                self.root.after(0, self.draw_temp_graph)
        except Exception as e:
            self.hourly_temps = []

    def update_hourly_temps(self):
        """백그라운드에서 24시간 온도 예보 업데이트"""
        thread = threading.Thread(target=self.fetch_hourly_temps, daemon=True)
        thread.start()
        # 1시간마다 업데이트
        self.root.after(3600000, self.update_hourly_temps)

    def draw_temp_graph(self):
        """24시간 온도 그래프 그리기"""
        self.temp_canvas.delete('all')

        if not self.hourly_temps or len(self.hourly_temps) < 2:
            self.temp_canvas.create_text(
                140, 30, text='온도 데이터 로딩중...',
                fill='#888888', font=('맑은 고딕', 9)
            )
            return

        temps = [t['temp'] for t in self.hourly_temps]
        hours = [t['hour'] for t in self.hourly_temps]

        # 그래프 영역 설정
        width = 280
        height = 60
        padding_x = 15
        padding_y = 15
        graph_width = width - 2 * padding_x
        graph_height = height - 2 * padding_y

        min_temp = min(temps)
        max_temp = max(temps)
        temp_range = max_temp - min_temp if max_temp != min_temp else 1

        # 포인트 계산
        points = []
        for i, temp in enumerate(temps):
            x = padding_x + (i / (len(temps) - 1)) * graph_width
            y = padding_y + (1 - (temp - min_temp) / temp_range) * graph_height
            points.append((x, y))

        # 그라데이션 효과를 위한 영역 채우기
        fill_points = points.copy()
        fill_points.append((points[-1][0], height - 5))
        fill_points.append((points[0][0], height - 5))
        flat_fill = [coord for point in fill_points for coord in point]
        self.temp_canvas.create_polygon(flat_fill, fill='#1e3a5f', outline='')

        # 선 그리기
        for i in range(len(points) - 1):
            self.temp_canvas.create_line(
                points[i][0], points[i][1],
                points[i+1][0], points[i+1][1],
                fill='#00d9ff', width=2
            )

        # 최고/최저 온도 표시
        max_idx = temps.index(max_temp)
        min_idx = temps.index(min_temp)

        self.temp_canvas.create_text(
            points[max_idx][0], points[max_idx][1] - 10,
            text=f'{max_temp}°', fill='#ff6b6b', font=('맑은 고딕', 8, 'bold')
        )
        self.temp_canvas.create_text(
            points[min_idx][0], points[min_idx][1] - 10,
            text=f'{min_temp}°', fill='#4dabf7', font=('맑은 고딕', 8, 'bold')
        )

        # 시작/끝 시간 표시
        self.temp_canvas.create_text(
            padding_x, height - 3,
            text=f'{hours[0]}시', fill='#aaaaaa', font=('맑은 고딕', 7), anchor='w'
        )
        self.temp_canvas.create_text(
            width - padding_x, height - 3,
            text=f'{hours[-1]}시', fill='#aaaaaa', font=('맑은 고딕', 7), anchor='e'
        )

        # 시작 시간 온도 표시 (그래프 시작 포인트 위)
        self.temp_canvas.create_text(
            points[0][0], points[0][1] - 10,
            text=f'{temps[0]}°', fill='#aaaaaa', font=('맑은 고딕', 8, 'bold')
        )

        # 끝 시간 온도 표시 (그래프 끝 포인트 위)
        self.temp_canvas.create_text(
            points[-1][0], points[-1][1] - 10,
            text=f'{temps[-1]}°', fill='#aaaaaa', font=('맑은 고딕', 8, 'bold')
        )

    def update_stock(self):
        """백그라운드에서 주식 지수 업데이트"""
        thread = threading.Thread(target=self.fetch_stock, daemon=True)
        thread.start()
        # 1분마다 주식 업데이트
        self.root.after(60000, self.update_stock)

    def fetch_single_stock(self, code, headers, stock_cache):
        """네이버에서 단일 종목 정보를 가져오는 함수"""
        import time

        max_retries = 5
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

                # 쉼표 제거 후 숫자 변환
                change_val = float(change.replace(',', '')) if isinstance(change, str) else float(change)

                arrow = "▲" if change_val > 0 else "▼" if change_val < 0 else ""
                color = "up" if change_val > 0 else "down" if change_val < 0 else "flat"

                self.individual_stocks[code] = {
                    'name': name,
                    'price': price,
                    'change': abs(change_val),
                    'rate': rate,
                    'arrow': arrow,
                    'color': color
                }
                # 성공 시 캐시 저장 및 화면 업데이트
                self.root.after(0, lambda c=code: self.update_single_stock_display(c))
                self.root.after(0, self.save_stock_cache)
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1.5)  # 재시도 간격 증가

        # 모든 시도 실패 - 캐시에서 불러오기 시도
        if code in stock_cache and stock_cache[code].get('color') != 'error':
            cached = stock_cache[code].copy()
            # 캐시 데이터임을 표시 (이름 앞에 ⏸ 추가, 중복 방지)
            if not cached.get('name', '').startswith('⏸'):
                cached['name'] = f"⏸ {cached.get('name', code)}"
            self.individual_stocks[code] = cached
            self.root.after(0, lambda c=code: self.update_single_stock_display(c))
        else:
            self.individual_stocks[code] = {
                'name': f'[{code}]',
                'price': '-',
                'change': 0,
                'rate': '-',
                'arrow': '',
                'color': 'error'
            }
            self.root.after(0, lambda c=code: self.update_single_stock_display(c))

    def fetch_individual_stocks(self):
        """네이버에서 개별 종목 정보를 병렬로 가져오는 함수"""
        from concurrent.futures import ThreadPoolExecutor, wait

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://m.stock.naver.com/',
            'Origin': 'https://m.stock.naver.com',
        }

        # 캐시 불러오기 (실패 시 fallback용)
        stock_cache = self.load_stock_cache()

        # 최대 2개씩 병렬 처리 (rate limiting 방지)
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(self.fetch_single_stock, code, headers, stock_cache) for code in self.stock_codes]
            wait(futures)  # 모든 작업 완료 대기

    def update_single_stock_display(self, code):
        """단일 종목 화면 업데이트"""
        if code not in self.stock_labels:
            return

        labels = self.stock_labels[code]
        name_label = labels['name']
        price_label = labels['price']

        if code in self.individual_stocks:
            stock = self.individual_stocks[code]
            if stock['color'] == 'error':
                name_label.config(text=stock['name'], fg='#888888')
                price_label.config(text=' 로딩 실패', fg='#888888')
            else:
                name_label.config(text=stock['name'], fg='#ffffff')
                price_text = f"  {stock['price']}  {stock['arrow']}{stock['change']:.0f} ({stock['rate']}%)"
                price_label.config(text=price_text)

                if stock['color'] == 'up':
                    price_label.config(fg='#ff6b6b')
                elif stock['color'] == 'down':
                    price_label.config(fg='#4dabf7')
                else:
                    price_label.config(fg='#ffffff')

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

    def get_solar_term(self, date):
        """주어진 날짜가 24절기에 해당하는지 확인하고, 해당하면 (한글명, 한자명) 반환"""
        year = date.year
        month = date.month
        day = date.day

        # 24절기 데이터: (월, 한글명, 한자명, C상수)
        # 각 월에 2개의 절기가 있음 (월 초와 월 중순)
        solar_terms = [
            (1, '소한', '小寒', 5.4055),
            (1, '대한', '大寒', 20.12),
            (2, '입춘', '立春', 3.87),
            (2, '우수', '雨水', 18.73),
            (3, '경칩', '驚蟄', 5.63),
            (3, '춘분', '春分', 20.646),
            (4, '청명', '淸明', 4.81),
            (4, '곡우', '穀雨', 20.1),
            (5, '입하', '立夏', 5.52),
            (5, '소만', '小滿', 21.04),
            (6, '망종', '芒種', 5.678),
            (6, '하지', '夏至', 21.37),
            (7, '소서', '小暑', 7.108),
            (7, '대서', '大暑', 22.83),
            (8, '입추', '立秋', 7.5),
            (8, '처서', '處暑', 23.13),
            (9, '백로', '白露', 7.646),
            (9, '추분', '秋分', 23.042),
            (10, '한로', '寒露', 8.318),
            (10, '상강', '霜降', 23.438),
            (11, '입동', '立冬', 7.438),
            (11, '소설', '小雪', 22.36),
            (12, '대설', '大雪', 7.18),
            (12, '동지', '冬至', 21.94),
        ]

        # 연도의 마지막 두 자리
        year_suffix = year % 100

        # 해당 월의 절기만 확인
        for term_month, korean_name, chinese_name, c_constant in solar_terms:
            if term_month != month:
                continue

            # 절기 날짜 계산 공식: D = int(Y × 0.2422 + C) - int((Y-1) / 4)
            # 21세기 기준 (2000년 이후)
            calculated_day = int(year_suffix * 0.2422 + c_constant) - int((year_suffix - 1) // 4)

            if calculated_day == day:
                return (korean_name, chinese_name)

        return None

    def fetch_news(self):
        """구글 뉴스 RSS로 반도체 뉴스를 가져오는 함수"""
        try:
            # 구글 뉴스 RSS
            query = urllib.request.quote('반도체')
            url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_content = response.read().decode('utf-8')

            # RSS에서 뉴스 아이템 추출
            news_items = []

            # item 태그 내의 title과 link 추출
            items = re.findall(r'<item>(.*?)</item>', xml_content, re.DOTALL)

            for item in items[:5]:
                title_match = re.search(r'<title>(.*?)</title>', item)
                link_match = re.search(r'<link>(.*?)</link>', item)

                if title_match and link_match:
                    title = title_match.group(1)
                    link = link_match.group(1)

                    # HTML 엔티티 디코딩
                    title = html.unescape(title)
                    # CDATA 제거
                    title = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', title)
                    # 불필요한 태그 제거
                    title = re.sub(r'<[^>]+>', '', title)
                    # 출처 제거 (예: " - 한국경제")
                    title = re.sub(r'\s*-\s*[^-]+$', '', title)
                    # 제목이 너무 길면 자르기 (한 줄에 맞게)
                    if len(title) > 32:
                        title = title[:30] + '..'

                    news_items.append({'title': title, 'link': link})

            if news_items:
                self.semiconductor_news = news_items
                self.root.after(0, self.update_news_display)

        except Exception as e:
            # 에러 시 기존 뉴스 유지
            pass

    def update_news_display(self):
        """뉴스 화면 업데이트"""
        for i, label in enumerate(self.news_labels):
            if i < len(self.semiconductor_news):
                news = self.semiconductor_news[i]
                label.config(text=f"• {news['title']}")
                # 클릭 이벤트 바인딩 (링크 열기)
                label.bind('<Button-1>', lambda e, url=news['link']: self.open_news_link(url))
            else:
                label.config(text='')
                label.unbind('<Button-1>')

    def open_news_link(self, url):
        """뉴스 링크 열기"""
        import webbrowser
        webbrowser.open(url)

    def refresh_news(self, event=None):
        """뉴스 새로고침"""
        self.news_refresh_btn.config(text=' 로딩...', fg='#ffcc00')
        for label in self.news_labels:
            label.config(text='')
        self.news_labels[0].config(text='뉴스 로딩중...')

        def fetch_and_restore():
            self.fetch_news()
            self.root.after(0, lambda: self.news_refresh_btn.config(text=' [새로고침]', fg='#888888'))

        thread = threading.Thread(target=fetch_and_restore, daemon=True)
        thread.start()

    def update_news(self):
        """백그라운드에서 뉴스 업데이트"""
        thread = threading.Thread(target=self.fetch_news, daemon=True)
        thread.start()
        # 10분마다 뉴스 업데이트
        self.root.after(600000, self.update_news)

    def refresh_all_stocks(self, event=None):
        """모든 주식 정보 새로고침"""
        # 새로고침 중 표시
        self.refresh_btn.config(text=' 로딩...', fg='#ffcc00')

        # stocks.txt에서 최신 종목 코드 다시 로드
        new_codes = self.load_stock_codes()

        # 종목 코드가 변경되었으면 라벨 재생성
        if new_codes != self.stock_codes:
            self.stock_codes = new_codes
            self.rebuild_stock_labels()

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

        # 24절기 확인
        solar_term_info = self.get_solar_term(now)
        if solar_term_info:
            korean_name, chinese_name = solar_term_info
            date_str = f"{date_str} ({korean_name}, {chinese_name})"

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
