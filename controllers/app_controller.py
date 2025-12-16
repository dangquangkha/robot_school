from functools import partial
import time
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
from kivy.core.window import Window
from kivy.properties import ListProperty

import threading
import pygame
import speech_recognition as sr

# Import Models
from models.ai_service import AIService
from models.game_manager import GameManager

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

# --- CLASS MỚI: Danh sách game (Giao diện Kids UI) ---
class GameListPopup(Popup):
    def __init__(self, game_list, callback_function, **kwargs):
        super().__init__(**kwargs)
        self.title = " KHO GAME CỦA BẠN "
        self.title_size = 28
        self.title_align = 'center'
        self.size_hint = (0.9, 0.85) # Popup to, chiếm 90% màn hình
        self.separator_color = [1, 1, 1, 0] # Ẩn đường kẻ mặc định
        
        # 1. Layout chính (Nền trắng kem)
        root_layout = BoxLayout(orientation='vertical', padding=15, spacing=15)
        # Vẽ nền màu trắng kem cho nội dung popup
        with root_layout.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(0.95, 0.95, 0.9, 1) # Màu kem nhạt
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[20,])
        # Cập nhật hình nền khi popup thay đổi kích thước
        root_layout.bind(pos=self.update_rect, size=self.update_rect)

        # 2. Vùng cuộn (ScrollView) chứa các nút game
        scroll = ScrollView(size_hint_y=0.85) # Chiếm 85% chiều cao
        
        # Lưới chứa nút (1 cột để nút to và dài)
        grid = GridLayout(cols=1, spacing=20, size_hint_y=None, padding=[10, 10])
        grid.bind(minimum_height=grid.setter('height'))

        # Danh sách màu sắc để tô luân phiên cho đẹp (Cam, Xanh Lá, Xanh Dương, Hồng)
        rainbow_colors = [
            [1, 0.6, 0.2, 1],   # Cam
            [0.2, 0.8, 0.2, 1], # Xanh lá
            [0.4, 0.6, 1, 1],   # Xanh dương
            [1, 0.4, 0.7, 1]    # Hồng
        ]

        # 3. Tạo nút cho từng game
        for index, game_name in enumerate(game_list):
            # Chọn màu dựa theo thứ tự
            color = rainbow_colors[index % len(rainbow_colors)]
            
            # Dùng KiddyButton thay vì Button thường
            btn = KiddyButton(
                text=game_name.upper(), # Chữ in hoa cho đẹp
                size_hint_y=None, 
                height=100,             # Nút cao 100px (Rất dễ bấm)
                font_size=24
            )
            btn.b_color = color # Gán màu sắc
            
            # Gán sự kiện bấm
            btn.bind(on_press=partial(self.on_game_btn_click, game_name, callback_function))
            
            grid.add_widget(btn)

        scroll.add_widget(grid)
        root_layout.add_widget(scroll)

        # 4. Nút Đóng (Màu đỏ) ở dưới cùng
        close_btn = KiddyButton(
            text="Đóng lại",
            size_hint_y=None,
            height=80
        )
        close_btn.b_color = [1, 0.3, 0.3, 1] # Màu đỏ
        close_btn.bind(on_press=self.dismiss)
        
        root_layout.add_widget(close_btn)

        self.content = root_layout

    def update_rect(self, instance, value):
        # Hàm cập nhật nền khi resize
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def on_game_btn_click(self, game_name, callback, instance):
        self.dismiss()
        callback(game_name)

class MainScreen(Screen):
    chat_font_size = NumericProperty(60)  # Giá trị mặc định

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ai_service = AIService()
        self.game_manager = GameManager()
        self.recognizer = sr.Recognizer()
        self.has_greeted = False
        self.is_listening = False
    
    # --- HÀM MỚI: Bật/Tắt chế độ nghe liên tục ---
    def toggle_voice_loop(self):
        if self.is_listening:
            # Nếu đang nghe -> Bấm để Dừng
            self.is_listening = False
            self.ids.btn_voice.text = "Đang dừng..."
            self.ids.btn_voice.b_color = [1, 0.4, 0.4, 1] # Màu đỏ nhạt
        else:
            # Nếu đang dừng -> Bấm để Nghe
            self.is_listening = True
            self.ids.btn_voice.text = "DỪNG LẠI"
            self.ids.btn_voice.b_color = [1, 0, 0, 1] # Màu đỏ đậm
            
            # Chạy vòng lặp trong luồng riêng
            threading.Thread(target=self.run_listening_loop).start()

    def run_listening_loop(self):
        while self.is_listening:
            
            # --- 1. CHẶN LUỒNG: Nếu Bot đang nói, tuyệt đối không nghe ---
            if self.ai_service.is_speaking:
                print("Bot đang nói, tạm dừng nghe...")
                
                # Kỹ thuật "Khóa": Ép giao diện về trạng thái tĩnh (idle)
                # để đảm bảo mặt không bị kẹt ở biểu cảm "đang nghe"
                # (Lưu ý: set_face đã được viết lại ở bước trước để an toàn với luồng)
                try:
                    # Kiểm tra nhanh: Nếu đang hiện mặt "nghe" thì mới cần reset
                    # (Dùng try-except để tránh lỗi nếu chưa kịp load ID)
                    if self.ids.face_listen.opacity == 1:
                        self.set_face('idle')
                except:
                    # Nếu lỡ có lỗi truy cập ID từ luồng phụ thì cứ set thẳng luôn cho an toàn
                    self.set_face('idle')
                
                time.sleep(0.5) # Đợi 0.5s rồi kiểm tra lại
                continue # Bỏ qua lượt này, quay lại đầu vòng lặp
            
            # --- 2. NẾU BOT IM LẶNG THÌ MỚI BẮT ĐẦU NGHE ---
            self.process_voice()
            
            # Nghỉ 1 giây giữa các lần nghe để giảm tải cho CPU và tránh nóng máy
            time.sleep(1.0)
        
        # Khi vòng lặp kết thúc (do bấm nút Dừng), reset lại giao diện nút
        Clock.schedule_once(self.reset_voice_button)

    def reset_voice_button(self, dt):
        self.ids.btn_voice.text = "Nói (Voice)"
        self.ids.btn_voice.b_color = [1, 0.4, 0.4, 1] # Trả về màu cũ
        
    # --- CẬP NHẬT HÀM NÀY ---
    def update_chat_log(self, message):
        # 1. Tạo một Label mới cho tin nhắn này
        from kivy.uix.label import Label # Import Label
        
        # Tính toán màu sắc: Nếu là "Bot:" hoặc "Hệ thống:" thì màu khác, "Bạn:" thì màu khác
        msg_color = [1, 1, 1, 1] # Mặc định trắng
        if message.startswith("Bạn:"):
            msg_color = [1, 0.9, 0.4, 1] # Màu vàng nhạt cho người dùng
        elif message.startswith("Lỗi"):
            msg_color = [1, 0.4, 0.4, 1] # Màu đỏ cho lỗi

        lbl = Label(
            text=message,
            size_hint_y=None,
            color=msg_color,
            markup=True,
            font_size=self.chat_font_size
        )
        
        # Mẹo: Để Label tự giãn chiều cao theo nội dung text
        lbl.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        lbl.text_size = (self.ids.chat_list.width, None) # Ép chiều ngang bằng khung chat
        
        # 2. Thêm Label vào GridLayout (id: chat_list)
        self.ids.chat_list.add_widget(lbl)
        
        # 3. Giới hạn lịch sử để tiết kiệm RAM (Chỉ giữ 50 tin nhắn cuối)
        if len(self.ids.chat_list.children) > 50:
            # Xóa tin nhắn cũ nhất (Kivy lưu children theo thứ tự đảo ngược, index 0 là mới nhất)
            # Nên ta xóa phần tử cuối danh sách children
            self.ids.chat_list.remove_widget(self.ids.chat_list.children[-1])

        # 4. Cuộn xuống dưới cùng
        Clock.schedule_once(self.scroll_to_bottom, 0.1)

    def scroll_to_bottom(self, dt):
        try:
            if 'chat_scroller' in self.ids:
                # scroll_y = 0 nghĩa là đáy, 1 là đỉnh
                self.ids.chat_scroller.scroll_y = 0
        except Exception as e:
            print(f"Lỗi cuộn trang: {e}")

    def on_voice_button_press(self):
        # Chạy ghi âm ở luồng riêng
        threading.Thread(target=self.process_voice).start()

    def on_enter(self):
        """Hàm này tự động chạy khi màn hình Chat hiện lên"""
        if not self.has_greeted:
            # Câu chào bạn muốn Robot nói
            greeting_text = "Xin chào các bạn! Các bạn muốn chơi gì nào?"
            
            # --- SỬA THÀNH: Gọi hàm update_chat_log ---
            self.update_chat_log(f"Bot: {greeting_text}")
            
            # Gọi hàm nói (chạy trong luồng riêng để không đơ ứng dụng)
            threading.Thread(target=self.ai_service.speak, args=(greeting_text,)).start()
            
            # Đánh dấu là đã chào rồi
            self.has_greeted = True

    # --- HÀM MỞ CÀI ĐẶT ---
    def open_settings(self):
        # Truyền 'self' (màn hình chính) vào popup để popup chỉnh được biến font_size
        popup = SettingsPopup(main_screen=self)
        popup.open()
    
    
    # Hàm đổi biểu cảm mới (Sử dụng Opacity để mượt mà, không giật)
    def set_face(self, state):
        def update_ui(dt):
            # 1. Đầu tiên: Ẩn tất cả các mặt đi
            self.ids.face_idle.opacity = 0
            self.ids.face_listen.opacity = 0
            self.ids.face_talk.opacity = 0
            
            # 2. Sau đó: Chỉ hiện mặt cần thiết
            if state == 'idle':
                self.ids.face_idle.opacity = 1
                
            elif state == 'listen':
                self.ids.face_listen.opacity = 1
                # Mẹo: Reset lại delay để GIF chạy mượt ngay từ đầu
                self.ids.face_listen.anim_delay = 0.1 
                
            elif state == 'talk':
                self.ids.face_talk.opacity = 1
                # Mẹo: Reset lại delay để GIF chạy mượt ngay từ đầu
                self.ids.face_talk.anim_delay = 0.1

        # Chạy lệnh update_ui trên luồng chính của giao diện
        Clock.schedule_once(update_ui)

    def process_voice(self):

        if not self.is_listening: return
        self.set_face('listen')
        Clock.schedule_once(lambda dt: self.update_chat_log("Hệ thống: Đang nghe (nói to lên nhé)..."))
        
        try:
            MIC_ID = 0
            with sr.Microphone(device_index=MIC_ID) as source:
                # 1. Chỉnh độ nhạy mic (quan trọng)
                self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
                
                # 2. Tăng thời gian chờ lên 50s giống file testv4.py
                # timeout: thời gian chờ bắt đầu nói
                # phrase_time_limit: thời gian tối đa cho một câu nói
                audio = self.recognizer.listen(source, timeout=120, phrase_time_limit=240)
                
                Clock.schedule_once(lambda dt: self.update_chat_log("Hệ thống: ⏳ Đang xử lý..."))
                
                text = self.recognizer.recognize_google(audio, language="vi-VN")
                
                Clock.schedule_once(lambda dt: self.update_chat_log(f"Bạn: {text}"))
                self.handle_ai_response(text)
                
        except sr.WaitTimeoutError:
            Clock.schedule_once(lambda dt: self.update_chat_log("Lỗi: Hết thời gian chờ (Timeout). Hãy thử nói nhanh hơn hoặc to hơn."))
            # Phát loa thông báo lỗi để bạn biết
            #self.speak_error("Tôi không nghe thấy gì cả.")
            pass
            
        except sr.UnknownValueError:
            Clock.schedule_once(lambda dt: self.update_chat_log("Lỗi: Không nhận dạng được giọng nói."))
            #self.speak_error("Tôi không nghe rõ bạn nói gì.")
            pass
        except sr.RequestError as e:
            Clock.schedule_once(lambda dt: self.update_chat_log(f"Lỗi kết nối Google: {e}"))
            
        except Exception as e:
            # [SỬA LẠI ĐOẠN NÀY]
            # Lưu nội dung lỗi ra một biến riêng (biến này sẽ không bị xóa)
            error_msg = str(e) 
            Clock.schedule_once(lambda dt: self.update_chat_log(f"Lỗi nghiêm trọng: {error_msg}"))

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
            
            def speak_with_face():
                # 1. Định nghĩa hàm callback: Chỉ đổi mặt khi nhạc bắt đầu chạy
                def on_sound_start():
                    self.set_face('talk') # Lúc này mới chuyển sang mặt nói

                # 2. Đặt mặt về trạng thái chờ (trong lúc đang tải âm thanh từ API)
                self.set_face('idle') 
                
                # 3. Gọi hàm speak và TRUYỀN HÀM CALLBACK VÀO
                self.ai_service.speak(bot_reply, on_play_callback=on_sound_start)
                
                # 4. Sau khi nói xong -> Về mặt bình thường
                self.set_face('idle')

            # Chạy luồng
            threading.Thread(target=speak_with_face).start()

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
    
    # --- HÀM MỚI: QUAY VỀ MÀN HÌNH CHÀO ---
    def go_back_home(self):
        # 1. Quan trọng: Tắt chế độ nghe nếu đang bật để tránh lỗi ngầm
        if self.is_listening:
            self.is_listening = False
            self.ids.btn_voice.text = "Nói (Voice)"
            self.ids.btn_voice.b_color = [1, 0.4, 0.4, 1]

        # 2. Chuyển màn hình về trang chủ
        # Hiệu ứng trượt sang phải (right) tạo cảm giác "quay lại"
        self.manager.transition.direction = 'right'
        self.manager.current = 'welcome_screen'

# Định nghĩa nút bấm trong Python để tránh lỗi NoneType
class KiddyButton(Button):
    b_color = ListProperty([1, 1, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Pre-load âm thanh click để không bị trễ khi bấm
        try:
            if not pygame.mixer.get_init(): pygame.mixer.init()
            self.click_sound = pygame.mixer.Sound("sounds/UI_button.wav")
            self.click_sound.set_volume(0.8)
        except:
            self.click_sound = None

    def on_press(self):
        # 1. Phát âm thanh
        if self.click_sound:
            self.click_sound.play()
        
        # 2. Gọi logic mặc định của nút bấm (quan trọng)
        super().on_press()

# --- SỬA LẠI CLASS WelcomeScreen ---
class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Khởi tạo GameManager riêng cho màn hình này
        self.game_manager = GameManager()

    def show_games_welcome(self):
        """Hàm này được gọi khi bấm nút Game ở màn hình chào"""
        # 1. Lấy danh sách game
        games = self.game_manager.get_game_list()
        
        if not games:
            print("Không tìm thấy game nào!") # Hoặc bạn có thể hiện thông báo
            return

        # 2. Mở Popup danh sách game
        # Truyền vào hàm callback là self.launch_game_direct
        popup = GameListPopup(games, self.launch_game_direct)
        popup.open()

    def launch_game_direct(self, game_name):
        """Hàm chạy game trực tiếp"""
        print(f"Đang mở game {game_name} từ màn hình chào...")
        self.game_manager.launch_game(game_name)

# --- SỬA HÀM BUILD CỦA APP ---
class AIChatVoiceApp(App):
    def build(self):

        Window.fullscreen = 'auto'
        # Load giao diện
        Builder.load_file('views/main_view.kv')
        # Tạo trình quản lý màn hình
        sm = ScreenManager()
        
        # Thêm các màn hình vào trình quản lý
        # Lưu ý: Màn hình nào add trước sẽ hiện lên trước
        sm.add_widget(WelcomeScreen(name="welcome_screen"))
        sm.add_widget(MainScreen(name="chat_screen"))
        
        return sm