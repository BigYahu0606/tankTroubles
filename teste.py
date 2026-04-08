import pygame
import sys
import math

pygame.init()

tela = pygame.display.set_mode((800, 600))
fps = pygame.time.Clock()
rodando = True

x, y = 300, 400
angulo = 0
velocidade = 3
velocidade_rot = 3

x2, y2 = 400, 300
angulo2 = 0

while rodando == True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
    fps.tick(60)
    tela.fill("white")
   
    #jogadores e movimento
            
            #player 1
    tecla = pygame.key.get_pressed()

    if tecla[pygame.K_LEFT]:
        angulo +=  velocidade_rot
    if tecla[pygame.K_RIGHT]:
        angulo -= velocidade_rot

    dx = math.cos(math.radians(angulo))
    dy = -math.sin(math.radians(angulo))

    if tecla[pygame.K_UP]:
        x += velocidade * dx
        y += velocidade * dy 

    if tecla[pygame.K_DOWN]:
        x -= velocidade * dx 
        y -= velocidade * dy

    tank1 = pygame.Surface((50, 30), pygame.SRCALPHA)
    tank1.fill ((255,0,0 ))

    tank1_virado = pygame.transform.rotate(tank1, angulo)
    rect = tank1_virado.get_rect(center=(x,y))

    tela.blit(tank1_virado, rect.topleft)
            
            #player 2
    
    if tecla[pygame.K_a]:
        angulo2 +=  velocidade_rot
    if tecla[pygame.K_d]:
        angulo2 -= velocidade_rot

    dx2 = math.cos(math.radians(angulo2))
    dy2 = -math.sin(math.radians(angulo2))

    if tecla[pygame.K_w]:
        x2 += velocidade * dx2
        y2 += velocidade * dy2 

    if tecla[pygame.K_s]:
        x2 -= velocidade * dx2 
        y2 -= velocidade * dy2

    tank2 = pygame.Surface((50, 30), pygame.SRCALPHA)
    tank2.fill ((0,0,0 ))

    tank2_virado = pygame.transform.rotate(tank2, angulo2)
    rect2 = tank2_virado.get_rect(center=(x2,y2))

    tela.blit(tank2_virado, rect2.topleft)
    




    pygame.display.flip()