import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import pygame
import time
import requests

# Load biến môi trường
load_dotenv()

class AIService:
    def __init__(self):
        # Kiểm tra API Key
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cse_id = os.getenv("GOOGLE_CSE_ID")

        if not self.api_key:
            print("LỖI: Chưa có OPENAI_API_KEY trong file .env")
        else:
            self.client = OpenAI(api_key=self.api_key)
        
        self.history = []
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

    def search_google_law(self, query):
        """Hàm này gọi Google API để tìm kiếm thông tin"""
        print(f"🔍 Đang tra cứu Google: {query}")
        
        # In ra 5 ký tự đầu/cuối của key để kiểm tra xem nó có nhận đúng không
        # (Không in hết để bảo mật)
        if self.google_api_key:
            print(f"DEBUG Key: {self.google_api_key[:5]}...{self.google_api_key[-5:]}")
        else:
            print("DEBUG Key: None")

        url = f"https://www.googleapis.com/customsearch/v1?key={self.google_api_key}&cx={self.google_cse_id}&q={query}"
        
        try:
            response = requests.get(url)
            
            # --- THÊM ĐOẠN NÀY ĐỂ DEBUG LỖI 401 ---
            if response.status_code != 200:
                print(f"❌ Lỗi Google API ({response.status_code}): {response.text}")
                return f"Lỗi kết nối Google: {response.status_code}"
            # --------------------------------------

            data = response.json()
            results = []
            if 'items' in data:
                for item in data['items'][:3]:
                    title = item.get('title')
                    snippet = item.get('snippet')
                    results.append(f"Tiêu đề: {title}\nNội dung: {snippet}")
            
            if not results:
                return "Không tìm thấy thông tin nào trên Google."
                
            return "\n---\n".join(results)
        except Exception as e:
            return f"Lỗi ngoại lệ: {str(e)}"

    def get_response(self, user_input, available_games):
        if not self.api_key:
            return {"action": "chat", "content": "Lỗi: Vui lòng cấu hình API Key"}

        # 1. Định nghĩa Tools (Công cụ) cho AI biết
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_google_law",
                    "description": "Dùng để tra cứu luật pháp, mức phạt, quy định hiện hành khi bạn không chắc chắn.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Từ khóa tìm kiếm (VD: 'mức phạt nồng độ cồn 2025')"},
                        },
                        "required": ["query"],
                    },
                }
            }
        ]

        system_prompt = f"""
        Bạn là Robot Trường Học. Danh sách game: {available_games}.
        
        QUY TẮC:
        1. Nếu người dùng muốn chơi game -> Trả về JSON: {{"action": "play", "game": "tên_game"}}.
        2. Nếu cần tra cứu luật -> Hãy GỌI HÀM (Tool Call) search_google_law.
        3. Nếu trò chuyện bình thường -> Trả về JSON: {{"action": "chat", "content": "câu trả lời"}}.
        
        LƯU Ý CUỐI CÙNG: Câu trả lời cuối cùng cho người dùng PHẢI LUÔN LÀ JSON.
        """

        # Thêm tin nhắn mới của người dùng vào lịch sử
        self.history.append({"role": "user", "content": user_input})
        
        # Giữ lại tối đa 10 tin nhắn gần nhất để không tốn tiền token
        if len(self.history) > 10:
            self.history = self.history[-10:]

        # Tạo danh sách tin nhắn gửi đi (System Prompt + Lịch sử)
        messages = [{"role": "system", "content": system_prompt}] + self.history

        try:
            # --- BƯỚC 1: Gửi yêu cầu cho AI (Cho phép dùng Tool) ---
            response = self.client.chat.completions.create(
                model="gpt-4o-mini", # Hoặc gpt-4o
                messages=messages,
                tools=tools,
                tool_choice="auto", # Để AI tự quyết định có tìm Google hay không
                # Chưa ép JSON ngay ở bước này, vì AI có thể trả về Tool Call
                temperature=0.7
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # --- BƯỚC 2: Kiểm tra xem AI có muốn tìm Google không? ---
            if tool_calls:
                # Nếu có, AI muốn tìm kiếm
                print("🤖 AI quyết định cần tra cứu Google...")
                
                # Thêm tin nhắn của AI vào lịch sử để nó nhớ
                self.history.append(response_message)
                messages.append(response_message)

                # Thực hiện các hàm mà AI yêu cầu
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    if function_name == "search_google_law":
                        # Lấy tham số 'query' AI đã tạo ra
                        function_args = json.loads(tool_call.function.arguments)
                        query_text = function_args.get("query")
                        
                        # Gọi hàm Python để tìm Google
                        function_response = self.search_google_law(query_text)
                        
                        # Gửi kết quả tìm kiếm lại cho AI
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                        })
                        self.history.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                        })
                # --- BƯỚC 3: Gọi AI lần cuối để tổng hợp câu trả lời ---
                # Lần này ép buộc trả về JSON
                second_response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    response_format={"type": "json_object"} 
                )
                final_content = second_response.choices[0].message.content
                self.history.append({"role": "assistant", "content": final_content})
                return json.loads(final_content)

            else:
                # Nếu AI không cần tìm kiếm (chỉ là chat hoặc mở game)
                # Vì bước 1 chưa ép JSON (để bắt tool), nên giờ ta phải chắc chắn nó là JSON
                # Mẹo: Thường gpt-4o-mini sẽ nghe lời system prompt và trả về JSON
                # Nhưng để an toàn, ta gọi lại hoặc parse kỹ. 
                # Ở đây ta giả định nó trả đúng vì prompt đã nhắc kỹ.
                content = response_message.content
                self.history.append({"role": "assistant", "content": content})
                try:
                    return json.loads(content)
                except:
                    # Nếu lỡ nó trả về text thường, ta đóng gói lại thủ công
                    return {"action": "chat", "content": content}

        except Exception as e:
            print(f"Lỗi AI Service: {e}")
            # Nếu lỗi history (do cắt ghép sai), reset lại history để cứu chương trình
            self.history = [] 
            return {"action": "chat", "content": "Tôi đang gặp chút trục trặc khi kết nối bộ não."}