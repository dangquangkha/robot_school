import os
# Ưu tiên dùng thư viện PIL (Pillow) để load ảnh GIF mượt mà
os.environ['KIVY_IMAGE'] = 'pil,sdl2'
from controllers.app_controller import AIChatVoiceApp

if __name__ == "__main__":
    AIChatVoiceApp().run()