import pygame
from random import randint

pygame.init()

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

RECT_WIDTH = 50

rectx1_height = randint(100,400)
rectx2_height = randint(100,400)
rectx3_height = randint(100,400)

rect1_x = 650
rect2_x = 950
rect3_x = 1250

bird_x = 100
bird_y = 300

bird_height = 50
direct_y = 0

RECT_Y = 0
GAP = 200

GRAVITY = 0.5
VELOCITY = 3

score = 0
font = pygame.font.SysFont("sans",20)

screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
pygame.display.set_caption("My Game")
clock = pygame.time.Clock()

rect1_pass = False
rect2_pass = False
rect3_pass = False

running = True
pausing = False

while running:
    
    clock.tick(60)
    screen.fill(GREEN)

    rect1 = pygame.draw.rect(screen, BLUE, (rect1_x, RECT_Y, RECT_WIDTH, rectx1_height))
    rect2 = pygame.draw.rect(screen, BLUE, (rect2_x, RECT_Y, RECT_WIDTH, rectx2_height))
    rect3 = pygame.draw.rect(screen, BLUE, (rect3_x, RECT_Y, RECT_WIDTH, rectx3_height))
    
    rect1_re = pygame.draw.rect(screen, BLUE, (rect1_x, rectx1_height + GAP, RECT_WIDTH, SCREEN_HEIGHT - rectx1_height - GAP))
    rect2_re = pygame.draw.rect(screen, BLUE, (rect2_x, rectx2_height + GAP, RECT_WIDTH, SCREEN_HEIGHT - rectx2_height - GAP))
    rect3_re = pygame.draw.rect(screen, BLUE, (rect3_x, rectx3_height + GAP, RECT_WIDTH, SCREEN_HEIGHT - rectx3_height - GAP))
    
    rect1_x -= VELOCITY
    rect2_x -= VELOCITY
    rect3_x -= VELOCITY

    
    font_txt = font.render("Score: "+str(score),True,BLACK)
    screen.blit(font_txt,(5,5))

    if rect1_x + RECT_WIDTH <= bird_x and not rect1_pass:
        score +=1
        rect1_pass = True
    if rect2_x + RECT_WIDTH <= bird_x and not rect2_pass:
        score +=1
        rect2_pass = True
    if rect3_x + RECT_WIDTH <= bird_x and not rect3_pass:
        score +=1
        rect3_pass = True 
    
    if rect1_x < -RECT_WIDTH:
        rect1_x = 950
        rectx1_height = randint(100,400)
        rect1_pass = False
    if rect2_x < -RECT_WIDTH:
        rect2_x = 950
        rectx2_height = randint(100,400)
        rect2_pass = False
    if rect3_x < -RECT_WIDTH:
        rect3_x = 950
        rectx3_height = randint(100,400)
        rect3_pass = False
    
    bird = pygame.draw.rect(screen,RED,(bird_x,bird_y,RECT_WIDTH,bird_height))
    
    bird_y += direct_y
    direct_y += GRAVITY
    
    for rect in [rect1,rect2,rect3,rect1_re,rect2_re,rect3_re]:
        
        if bird.colliderect(rect) or bird_y >= SCREEN_HEIGHT or bird_y < 0:
            
            pausing = True
            direct_y = 0
            VELOCITY = 0
            game_over_txt = font.render("Game Over",True,BLACK)
            Score_txt = font.render("Score: " + str(score),True,BLACK)
            retry_game = font.render("Enter Space to game retry",True,BLACK)

            screen.blit(game_over_txt,(300,300))
            screen.blit(Score_txt,(300,320))
            screen.blit(retry_game,(300,340))
            
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                
                if pausing:
                    
                    bird_y = 300
                    VELOCITY = 3
                    rect1_x = 650
                    rect2_x = 950
                    rect3_x = 1250
                    score = 0
                    pausing = False
                direct_y = 0
                direct_y -= 10
        
    pygame.display.flip()

    
pygame.quit()