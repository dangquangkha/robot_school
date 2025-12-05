import webbrowser
import os
import sys

def main():
    # Lấy đường dẫn tuyệt đối đến file html
    # Cách này đảm bảo chạy được trên mọi máy tính
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "gamedeptrai.html")
    
    print(f"Đang mở game Offline: {file_path}")
    
    # Mở file HTML bằng trình duyệt mặc định
    webbrowser.open(f"file:///{file_path}")

if __name__ == "__main__":
    main()