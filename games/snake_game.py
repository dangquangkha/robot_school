import pygame
from random import randint
import time

pygame.init()

screen = pygame.display.set_mode((600,600))
pygame.display.set_caption("Snake Hunter - Space to Restart")

# Font chữ
font_small = pygame.font.SysFont("sans", 22)
font_big = pygame.font.SysFont("sans", 50) # Font to cho đếm ngược và Game Over

# Hằng số
WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)
GREEN = (0,255,0)
YELLOW = (255, 255, 0)
WIDTH = 50
HEIGHT = 50
VELOCITY = 50

clock = pygame.time.Clock()

# --- CÁC BIẾN TOÀN CỤC CẦN KHỞI TẠO LẠI ---
snake_body = []
velocity_x = 0
velocity_y = 0
score = 0
apple = None
game_state = "" # Các trạng thái: "countdown", "playing", "game_over"
countdown_timer = 0
last_count_time = 0

def reset_game():
    """Hàm này dùng để đặt lại toàn bộ thông số về ban đầu"""
    global snake_body, velocity_x, velocity_y, score, apple, game_state, countdown_timer, last_count_time
    
    # Đặt lại rắn
    snake_body = [
        pygame.Rect(150, 300, WIDTH, HEIGHT),
        pygame.Rect(100, 300, WIDTH, HEIGHT),
        pygame.Rect(50, 300, WIDTH, HEIGHT)
    ]
    
    # Đặt lại vận tốc mặc định
    velocity_x = VELOCITY
    velocity_y = 0
    
    # Đặt lại táo
    apple_x = randint(0, (600 - WIDTH) // WIDTH) * WIDTH
    apple_y = randint(0, (600 - HEIGHT) // HEIGHT) * HEIGHT
    apple = pygame.Rect(apple_x, apple_y, WIDTH, HEIGHT)
    
    score = 0
    
    # Chuyển sang chế độ đếm ngược
    game_state = "countdown"
    countdown_timer = 3  # Đếm từ 3 giây
    last_count_time = pygame.time.get_ticks()

# Gọi reset lần đầu để bắt đầu game
reset_game()

running = True

while running:
    clock.tick(10) # 10 FPS
    screen.fill(BLACK)
    
    # --- XỬ LÝ SỰ KIỆN ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.KEYDOWN:
            # 1. Logic điều khiển khi đang CHƠI
            if game_state == "playing":
                if event.key == pygame.K_RIGHT and velocity_x == 0:
                    velocity_x = VELOCITY
                    velocity_y = 0
                elif event.key == pygame.K_LEFT and velocity_x == 0:
                    velocity_x = -VELOCITY
                    velocity_y = 0
                elif event.key == pygame.K_UP and velocity_y == 0:
                    velocity_x = 0
                    velocity_y = -VELOCITY
                elif event.key == pygame.K_DOWN and velocity_y == 0:
                    velocity_x = 0
                    velocity_y = VELOCITY
            
            # 2. Logic khi GAME OVER (Bấm Space để chơi lại)
            if game_state == "game_over":
                if event.key == pygame.K_SPACE:
                    reset_game()

    # --- VẼ RẮN VÀ TÁO (Luôn vẽ dù đang chơi hay game over) ---
    for block in snake_body:
        pygame.draw.rect(screen, GREEN, block)
    pygame.draw.rect(screen, RED, apple)
    
    # Vẽ điểm
    score_txt = font_small.render("Score: " + str(score), True, WHITE)
    screen.blit(score_txt, (20,20))

    # --- LOGIC TỪNG TRẠNG THÁI ---
    
    # === TRẠNG THÁI 1: ĐẾM NGƯỢC ===
    if game_state == "countdown":
        # Lấy thời gian hiện tại
        current_time = pygame.time.get_ticks()
        
        # Vẽ số đếm ngược ra giữa màn hình
        count_text = font_big.render(str(countdown_timer), True, YELLOW)
        text_rect = count_text.get_rect(center=(300, 300))
        screen.blit(count_text, text_rect)
        
        # Logic trừ thời gian (mỗi 1000ms = 1s)
        if current_time - last_count_time > 1000:
            countdown_timer -= 1
            last_count_time = current_time
        
        if countdown_timer == 0:
            game_state = "playing"

    # === TRẠNG THÁI 2: ĐANG CHƠI ===
    elif game_state == "playing":
        # 1. Tạo đầu mới
        current_head = snake_body[0]
        new_head = pygame.Rect(
            current_head.x + velocity_x,
            current_head.y + velocity_y,
            WIDTH, HEIGHT
        )
        
        # 2. Va chạm tường -> Chết
        if new_head.left < 0 or new_head.right > 600 or new_head.top < 0 or new_head.bottom > 600:
            game_state = "game_over"
        
        # 3. Va chạm bản thân -> Chết
        for block in snake_body[1:]:
            if new_head.colliderect(block):
                game_state = "game_over"
        
        # 4. Di chuyển
        if game_state == "playing": # Kiểm tra lại để chắc chắn chưa chết
            snake_body.insert(0, new_head)
            
            if new_head.colliderect(apple):
                score += 1
                # Random táo sao cho khớp lưới ô vuông
                apple.x = randint(0, (600 - WIDTH) // WIDTH) * WIDTH
                apple.y = randint(0, (600 - HEIGHT) // HEIGHT) * HEIGHT
            else:
                snake_body.pop()

    # === TRẠNG THÁI 3: GAME OVER ===
    elif game_state == "game_over":
        # Vẽ chữ Game Over
        game_over_txt = font_big.render("GAME OVER", True, WHITE)
        restart_txt = font_small.render("Press SPACE to Restart", True, WHITE)
        
        # Căn giữa chữ
        screen.blit(game_over_txt, (300 - game_over_txt.get_width()//2, 200))
        screen.blit(restart_txt, (300 - restart_txt.get_width()//2, 300))

    pygame.display.flip()

pygame.quit()