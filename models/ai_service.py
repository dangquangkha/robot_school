import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import pygame
import time

# Load biến môi trường
load_dotenv()

class AIService:
    def __init__(self):
        # Kiểm tra API Key
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("LỖI: Chưa có OPENAI_API_KEY trong file .env")
        else:
            self.client = OpenAI(api_key=self.api_key)
        
        # Khởi tạo Pygame Mixer
        try:
            pygame.mixer.init()
            print("Pygame Mixer đã khởi tạo thành công.")
        except Exception as e:
            print(f"Lỗi khởi tạo Pygame Mixer: {e}")

    def speak(self, text):
        """Chuyển văn bản thành giọng nói và phát bằng Pygame"""
        if not text:
            return

        print(f"Bot đang nói: {text}") # In ra console để debug
        filename = "bot_speak.mp3"
        
        try:
            if not self.api_key:
                print("Không thể nói vì thiếu API Key.")
                return

            # 1. Gọi API TTS của OpenAI
            with self.client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice="alloy",
                input=text
            ) as response:
                response.stream_to_file(filename)

            # 2. Phát âm thanh bằng Pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
                
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()

            # Chờ phát xong
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            # Giải phóng file
            pygame.mixer.music.unload()

        except Exception as e:
            print(f"Lỗi phần Text-to-Speech: {str(e)}")

    def get_response(self, user_input, available_games):
        if not self.api_key:
            return {"action": "chat", "content": "Lỗi: Vui lòng cấu hình OPENAI_API_KEY trong file .env"}

        system_prompt = f"""
        Bạn là trợ lý ảo game center. Danh sách game hiện có: {available_games}.
        Nếu người dùng muốn chơi game, trả về JSON: {{"action": "play", "game": "tên_game"}}.
        Nếu trò chuyện bình thường, trả về JSON: {{"action": "chat", "content": "câu trả lời ngắn gọn"}}.
        Luôn trả về JSON.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"action": "chat", "content": f"Lỗi kết nối AI: {str(e)}"}