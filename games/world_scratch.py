import webbrowser
import time
import sys

# --- CẤU HÌNH LINK SCRATCH ---
# Link game Scratch của bạn
SCRATCH_URL = "https://scratch.mit.edu/projects/1248388698/fullscreen/" 

def main():
    print(f"Đang khởi động trình duyệt để vào game...")
    print(f"Link: {SCRATCH_URL}")
    
    # Lệnh mở trình duyệt web mặc định của máy tính (Chrome/Edge/Cốc Cốc...)
    try:
        webbrowser.open(SCRATCH_URL)
    except Exception as e:
        print(f"Lỗi không mở được trình duyệt: {e}")
    
    # Chờ 2 giây rồi tắt script này để giải phóng RAM cho App chính
    # (Trình duyệt web vẫn sẽ giữ nguyên, không bị tắt theo)
    time.sleep(2)

if __name__ == "__main__":
    main()