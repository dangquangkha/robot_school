from functools import partial
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout  # <--- Thêm cái này
from kivy.uix.scrollview import ScrollView  # <--- Thêm cái này
from kivy.uix.button import Button          # <--- Thêm cái này
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.popup import Popup # <--- Thêm dòng này
from kivy.properties import NumericProperty # <--- Thêm dòng này
from kivy.uix.screenmanager import ScreenManager, Screen

from kivy.properties import ListProperty

import threading
import speech_recognition as sr

# Import Models
from models.ai_service import AIService
from models.game_manager import GameManager

# --- CLASS MỚI: Cửa sổ cài đặt ---
# --- CLASS MỚI: Cửa sổ cài đặt (Đã sửa giao diện đẹp hơn) ---
class SettingsPopup(Popup):
    def __init__(self, main_screen, **kwargs):
        super().__init__(**kwargs)
        self.main_screen = main_screen
        self.title = "Cài đặt cho trò chuyện"
        self.title_size = 24
        self.title_align = 'center'
        self.size_hint = (0.7, 0.5) # Popup nhỏ gọn (70% rộng, 50% cao)
        self.separator_color = [0.53, 0.81, 0.98, 1] # Đường kẻ màu xanh da trời

        # Layout chính
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # 1. Dòng hướng dẫn
        lbl_instruct = (Builder.load_string('''Label:
            text: "Chỉnh cỡ chữ to/nhỏ"
            font_size: 22
            color: 1, 1, 1, 1
        '''))
        layout.add_widget(lbl_instruct)

        # 2. Khu vực điều khiển (Hàng ngang)
        controls = BoxLayout(orientation='horizontal', spacing=30, size_hint_y=None, height=100)
        
        # Nút GIẢM (Màu Đỏ Hồng)
        # Lưu ý: Ta khởi tạo KiddyButton và gán màu trực tiếp
        btn_down = KiddyButton(text="-", font_size=50)
        btn_down.b_color = [1, 0.4, 0.4, 1] 
        btn_down.bind(on_press=self.decrease_font)
        
        # Hiển thị số (To rõ ràng)
        self.lbl_info = (Builder.load_string(f'''Label:
            text: "{int(self.main_screen.chat_font_size)}"
            font_size: 60
            bold: True
            color: 1, 1, 0.5, 1
        '''))
        
        # Nút TĂNG (Màu Xanh Lá)
        btn_up = KiddyButton(text="+", font_size=50)
        btn_up.b_color = [0.2, 0.8, 0.2, 1]
        btn_up.bind(on_press=self.increase_font)

        # Thêm vào hàng ngang
        controls.add_widget(btn_down)
        controls.add_widget(self.lbl_info)
        controls.add_widget(btn_up)
        
        # Thêm hàng ngang vào layout chính
        layout.add_widget(controls)
        
        # Set nội dung cho Popup
        self.content = layout

    def increase_font(self, instance):
        # Tăng cỡ chữ
        self.main_screen.chat_font_size += 2
        self.lbl_info.text = str(int(self.main_screen.chat_font_size))

    def decrease_font(self, instance):
        # Giảm cỡ chữ (nhưng không cho nhỏ hơn 14)
        if self.main_screen.chat_font_size > 14:
            self.main_screen.chat_font_size -= 2
            self.lbl_info.text = str(int(self.main_screen.chat_font_size))

class GameListPopup(Popup):
    def __init__(self, game_list, callback_function, **kwargs):
        super().__init__(**kwargs)
        self.title = "Danh sách trò chơi"
        self.size_hint = (0.9, 0.8) # Rộng 90%, cao 80% màn hình
        
        # 1. Tạo vùng chứa có thanh cuộn (ScrollView)
        scroll = ScrollView()
        
        # 2. Tạo lưới chứa các nút (GridLayout)
        # cols=1 nghĩa là xếp theo 1 cột dọc
        # size_hint_y=None để lưới có thể dài ra tùy ý theo số lượng nút
        layout = GridLayout(cols=2, spacing=10, size_hint_y=None, padding=10)
        layout.bind(minimum_height=layout.setter('height'))

        # 3. Dùng vòng lặp để tạo nút cho từng game
        for game_name in game_list:
            btn = Button(
                text=game_name, 
                size_hint_y=None, 
                height=80, # Chiều cao mỗi nút
                background_color=(0, 1, 0.5, 1) # Màu xanh nhẹ
            )
            # Gắn sự kiện: Khi bấm nút -> Gọi hàm chọn game
            # partial giúp truyền tên game cụ thể vào hàm
            btn.bind(on_press=partial(self.on_game_btn_click, game_name, callback_function))
            
            layout.add_widget(btn)

        # Đóng gói giao diện
        scroll.add_widget(layout)
        self.content = scroll

    def on_game_btn_click(self, game_name, callback, instance):
        # Đóng popup trước
        self.dismiss()
        # Gọi hàm xử lý mở game bên MainScreen
        callback(game_name)

class MainScreen(Screen):
    chat_font_size = NumericProperty(50)  # Giá trị mặc định

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ai_service = AIService()
        self.game_manager = GameManager()
        self.recognizer = sr.Recognizer()

    def update_chat_log(self, message):
        # Cập nhật UI an toàn từ luồng khác
        self.ids.chat_log.text += f"\n\n{message}"

    def on_voice_button_press(self):
        # Chạy ghi âm ở luồng riêng
        threading.Thread(target=self.process_voice).start()

# --- HÀM MỞ CÀI ĐẶT ---
    def open_settings(self):
        # Truyền 'self' (màn hình chính) vào popup để popup chỉnh được biến font_size
        popup = SettingsPopup(main_screen=self)
        popup.open()

    def process_voice(self):
        Clock.schedule_once(lambda dt: self.update_chat_log("Hệ thống: 🎧 Đang nghe (nói to lên nhé)..."))
        
        try:
            MIC_ID = 0
            with sr.Microphone(device_index=MIC_ID) as source:
                # 1. Chỉnh độ nhạy mic (quan trọng)
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # 2. Tăng thời gian chờ lên 50s giống file testv4.py
                # timeout: thời gian chờ bắt đầu nói
                # phrase_time_limit: thời gian tối đa cho một câu nói
                audio = self.recognizer.listen(source, timeout=50, phrase_time_limit=10)
                
                Clock.schedule_once(lambda dt: self.update_chat_log("Hệ thống: ⏳ Đang xử lý..."))
                
                text = self.recognizer.recognize_google(audio, language="vi-VN")
                
                Clock.schedule_once(lambda dt: self.update_chat_log(f"Bạn: {text}"))
                self.handle_ai_response(text)
                
        except sr.WaitTimeoutError:
            Clock.schedule_once(lambda dt: self.update_chat_log("Lỗi: Hết thời gian chờ (Timeout). Hãy thử nói nhanh hơn hoặc to hơn."))
            # Phát loa thông báo lỗi để bạn biết
            self.speak_error("Tôi không nghe thấy gì cả.")
            
        except sr.UnknownValueError:
            Clock.schedule_once(lambda dt: self.update_chat_log("Lỗi: Không nhận dạng được giọng nói."))
            self.speak_error("Tôi không nghe rõ bạn nói gì.")
            
        except sr.RequestError as e:
            Clock.schedule_once(lambda dt: self.update_chat_log(f"Lỗi kết nối Google: {e}"))
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_chat_log(f"Lỗi nghiêm trọng: {e}"))

    def speak_error(self, text):
        threading.Thread(target=self.ai_service.speak, args=(text,)).start()

    def handle_ai_response(self, user_text):
        games = self.game_manager.get_game_list()
        
        # Gọi API OpenAI
        response = self.ai_service.get_response(user_text, games)

        if response.get("action") == "play":
            game_name = response.get("game")
            msg = f"Bot: Đang mở game {game_name}..."
            Clock.schedule_once(lambda dt: self.update_chat_log(msg))
            
            # Bot nói
            threading.Thread(target=self.ai_service.speak, args=(f"Đang mở game {game_name}",)).start()
            
            # Mở game
            success = self.game_manager.launch_game(game_name)
            if not success:
                 err = f"Bot: Không tìm thấy file {game_name}."
                 Clock.schedule_once(lambda dt: self.update_chat_log(err))
        else:
            bot_reply = response.get("content")
            Clock.schedule_once(lambda dt: self.update_chat_log(f"Bot: {bot_reply}"))
            
            # Bot nói câu trả lời
            threading.Thread(target=self.ai_service.speak, args=(bot_reply,)).start()

    def show_games(self):
        # 1. Lấy danh sách game từ GameManager
        games = self.game_manager.get_game_list()
        
        if not games:
            self.update_chat_log("Hệ thống: Không tìm thấy game nào trong thư mục 'games'.")
            return

        # 2. Khởi tạo và hiển thị Popup danh sách game
        # Truyền vào danh sách game VÀ hàm self.start_game_from_ui để popup biết làm gì khi bấm
        popup = GameListPopup(games, self.start_game_from_ui)
        popup.open()
        
        # Bot nói nhỏ nhẹ
        threading.Thread(target=self.ai_service.speak, args=("Mời bạn chọn game trên màn hình.",)).start()

    # --- THÊM HÀM MỚI ĐỂ XỬ LÝ KHI CHỌN GAME TỪ POPUP ---
    def start_game_from_ui(self, game_name):
        msg = f"Bot: Đang mở game {game_name}..."
        self.update_chat_log(msg)
        
        # Bot nói
        threading.Thread(target=self.ai_service.speak, args=(f"Đang mở game {game_name}",)).start()
        
        # Gọi GameManager để chạy game
        success = self.game_manager.launch_game(game_name)
        
        if not success:
             self.update_chat_log(f"Lỗi: Không thể khởi động file {game_name}.")

# Định nghĩa nút bấm trong Python để tránh lỗi NoneType
class KiddyButton(Button):
    # Khai báo biến b_color là ListProperty với màu mặc định là trắng
    b_color = ListProperty([1, 1, 1, 1])

# --- CLASS MỚI: Màn hình chào ---
class WelcomeScreen(Screen):
    pass

# --- SỬA HÀM BUILD CỦA APP ---
class AIChatVoiceApp(App):
    def build(self):
        
        # Load giao diện
        Builder.load_file('views/main_view.kv')
        # Tạo trình quản lý màn hình
        sm = ScreenManager()
        
        # Thêm các màn hình vào trình quản lý
        # Lưu ý: Màn hình nào add trước sẽ hiện lên trước
        sm.add_widget(WelcomeScreen(name="welcome_screen"))
        sm.add_widget(MainScreen(name="chat_screen"))
        
        return sm