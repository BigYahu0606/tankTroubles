import pygame
import sys
import math
import random

pygame.init()

LARGURA, ALTURA = 1000, 600
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Tank Battles")
fps = pygame.time.Clock()

# ── Paleta de cores ────────────────────────────────────────
COR_FUNDO      = (34,  40,  49)
COR_PAREDE     = (72,  84,  96)
COR_PAREDE_B   = (52,  64,  76)
COR_P1         = (41, 128, 185)
COR_P1_ESCURO  = (21,  88, 145)
COR_P2         = (192,  57,  43)
COR_P2_ESCURO  = (152,  27,  13)
COR_BALA1      = (100, 200, 255)
COR_BALA2      = (255, 120,  80)
COR_HUD        = (236, 240, 241)
COR_VITORIA    = (241, 196,  15)

# ── Configurações ──────────────────────────────────────────
velocidade            = 3
velocidade_rot        = 3
velocidade_projetil   = 7
COOLDOWN_TIRO         = 600    # ms entre tiros
TEMPO_VIDA_BALA       = 4000   # ms até a bala sumir
MAX_BALAS_POR_JOGADOR = 3
PONTOS_VITORIA        = 5
TAMANHO_TANK          = 20     # raio de colisão
DURACAO_ROUND_OVER    = 2200   # ms da tela "round encerrado"
DURACAO_IMUNIDADE     = 2000   # ms de imunidade pós-spawn
DIST_MIN_SPAWN        = 200    # distância mínima entre os dois spawns

# ── Cenários ───────────────────────────────────────────────
CENARIOS = {
    "Campo Aberto": {
        "paredes": [],
        "descricao": "Sem obstáculos — pura mira!",
    },
    "Labirinto": {
        "paredes": [
            pygame.Rect(200, 100, 20, 200),
            pygame.Rect(200, 100, 200, 20),
            pygame.Rect(400, 100, 20, 150),
            pygame.Rect(580, 100, 20, 200),
            pygame.Rect(580, 100, 200, 20),
            pygame.Rect(780, 100, 20, 150),
            pygame.Rect(200, 350, 150, 20),
            pygame.Rect(400, 350, 200, 20),
            pygame.Rect(650, 350, 150, 20),
            pygame.Rect(200, 480, 200, 20),
            pygame.Rect(580, 480, 200, 20),
            pygame.Rect(350, 250, 20, 150),
            pygame.Rect(630, 250, 20, 150),
        ],
        "descricao": "Navegue pelo labirinto!",
    },
    "Fortaleza": {
        "paredes": [
            pygame.Rect(380, 220, 240, 160),
            pygame.Rect(150, 150, 60, 60),
            pygame.Rect(790, 150, 60, 60),
            pygame.Rect(150, 390, 60, 60),
            pygame.Rect(790, 390, 60, 60),
            pygame.Rect(250, 290, 130, 20),
            pygame.Rect(620, 290, 130, 20),
        ],
        "descricao": "Proteja seu flanco!",
    },
    "Cruz": {
        "paredes": [
            pygame.Rect(100, 250, 200, 100),
            pygame.Rect(700, 250, 200, 100),
            pygame.Rect(450,  50, 100, 200),
            pygame.Rect(450, 350, 100, 200),
            pygame.Rect(380, 180, 240, 240),
        ],
        "descricao": "Caminhos cruzados!",
    },
    "Arena Caos": {
        "paredes": [
            pygame.Rect(300, 150, 20, 120),
            pygame.Rect(500, 100, 20, 100),
            pygame.Rect(680, 150, 20, 120),
            pygame.Rect(200, 330, 130, 20),
            pygame.Rect(450, 280, 100, 20),
            pygame.Rect(670, 330, 130, 20),
            pygame.Rect(350, 430, 20, 120),
            pygame.Rect(630, 430, 20, 120),
            pygame.Rect(160, 180, 80, 20),
            pygame.Rect(760, 180, 80, 20),
            pygame.Rect(160, 420, 80, 20),
            pygame.Rect(760, 420, 80, 20),
        ],
        "descricao": "Caos total!",
    },
}

lista_cenarios = list(CENARIOS.keys())

# ── Spawn aleatório seguro ─────────────────────────────────
def spawn_aleatorio(paredes, outro_pos=None):
    """
    Retorna (x, y) em posição livre de paredes e longe do outro jogador.
    Tenta até 200 vezes antes de desistir e retornar uma posição padrão.
    """
    margem  = TAMANHO_TANK + 10
    for _ in range(200):
        tx = random.randint(margem + 40, LARGURA  - margem - 40)
        ty = random.randint(margem + 60, ALTURA - margem - 10)

        tank_rect = pygame.Rect(tx - TAMANHO_TANK, ty - TAMANHO_TANK,
                                TAMANHO_TANK * 2,  TAMANHO_TANK * 2)

        # Não pode colidir com nenhuma parede
        colide_parede = any(tank_rect.colliderect(p) for p in paredes)
        if colide_parede:
            continue

        # Deve ficar longe do outro jogador
        if outro_pos is not None:
            dist = math.hypot(tx - outro_pos[0], ty - outro_pos[1])
            if dist < DIST_MIN_SPAWN:
                continue

        return float(tx), float(ty)

    # Fallback seguro
    return (150.0, 300.0) if outro_pos is None else (850.0, 300.0)


# ── Desenho do tanque ──────────────────────────────────────
def desenhar_tank(surface, cx, cy, angulo, cor_corpo, cor_escuro, imune=False):
    W, H  = 36, 26
    rad   = math.radians(-angulo)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    def rot(px, py):
        return (cx + px * cos_a - py * sin_a,
                cy + px * sin_a + py * cos_a)

    pontos_corpo = [(-W//2,-H//2),(W//2,-H//2),(W//2,H//2),(-W//2,H//2)]
    corpo_r = [rot(px, py) for px, py in pontos_corpo]

    # Piscada durante imunidade
    if imune and (pygame.time.get_ticks() // 120) % 2 == 0:
        alpha_surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        pygame.draw.polygon(alpha_surf, (*cor_corpo, 80), corpo_r)
        surface.blit(alpha_surf, (0, 0))
        return

    pygame.draw.polygon(surface, cor_corpo,  corpo_r)
    pygame.draw.polygon(surface, cor_escuro, corpo_r, 2)

    for sinal in (-1, 1):
        esteira = [(-W//2, sinal*(H//2-1)), (W//2, sinal*(H//2-1)),
                   (W//2, sinal*(H//2+6)), (-W//2, sinal*(H//2+6))]
        pygame.draw.polygon(surface, cor_escuro, [rot(px,py) for px,py in esteira])

    canon = [(0,-4),(22,-4),(22,4),(0,4)]
    pygame.draw.polygon(surface, cor_escuro, [rot(px,py) for px,py in canon])

    pygame.draw.circle(surface, cor_corpo,  (int(cx), int(cy)), 10)
    pygame.draw.circle(surface, cor_escuro, (int(cx), int(cy)), 10, 2)

    # Anel de imunidade
    if imune:
        restante = 1.0  # só para ter o anel sempre visível durante imunidade
        pygame.draw.circle(surface, COR_VITORIA, (int(cx), int(cy)), TAMANHO_TANK + 4, 2)


# ── Classe Projétil ────────────────────────────────────────
class Projetil:
    def __init__(self, x, y, angulo, dono):
        self.x      = x
        self.y      = y
        self.angulo = angulo
        self.dono   = dono
        self.dx     = math.cos(math.radians(angulo)) * velocidade_projetil
        self.dy     = -math.sin(math.radians(angulo)) * velocidade_projetil
        self.raio   = 5
        self.ativo  = True
        self.nasceu = pygame.time.get_ticks()
        self.ricochetes     = 0
        self.MAX_RICOCHETES = 5

    def mover(self, paredes):
        if pygame.time.get_ticks() - self.nasceu > TEMPO_VIDA_BALA:
            self.ativo = False
            return

        nx = self.x + self.dx
        ny = self.y + self.dy

        if nx - self.raio <= 0 or nx + self.raio >= LARGURA:
            self.dx *= -1
            nx = self.x + self.dx
            self.ricochetes += 1

        if ny - self.raio <= 0 or ny + self.raio >= ALTURA:
            self.dy *= -1
            ny = self.y + self.dy
            self.ricochetes += 1

        bola_rect = pygame.Rect(nx - self.raio, ny - self.raio,
                                self.raio * 2,  self.raio * 2)
        for parede in paredes:
            if bola_rect.colliderect(parede):
                bola_x = pygame.Rect(nx - self.raio, self.y - self.raio,
                                     self.raio * 2,  self.raio * 2)
                if bola_x.colliderect(parede):
                    self.dx *= -1

                bola_y = pygame.Rect(self.x - self.raio, ny - self.raio,
                                     self.raio * 2, self.raio * 2)
                if bola_y.colliderect(parede):
                    self.dy *= -1

                nx = self.x + self.dx
                ny = self.y + self.dy
                self.ricochetes += 1
                break

        if self.ricochetes > self.MAX_RICOCHETES:
            self.ativo = False
            return

        self.x = nx
        self.y = ny
        self.angulo = math.degrees(math.atan2(-self.dy, self.dx))

    def desenhar(self, surface):
        cor = COR_BALA1 if self.dono == 1 else COR_BALA2
        for i in range(1, 4):
            tc = tuple(max(0, c - i * 40) for c in cor)
            tx = int(self.x - self.dx * i * 1.5)
            ty = int(self.y - self.dy * i * 1.5)
            pygame.draw.circle(surface, tc, (tx, ty), max(1, self.raio - i))
        pygame.draw.circle(surface, cor,          (int(self.x), int(self.y)), self.raio)
        pygame.draw.circle(surface, (255,255,255), (int(self.x), int(self.y)), 2)

    def colidiu_com_tank(self, tx, ty):
        return math.hypot(self.x - tx, self.y - ty) < self.raio + TAMANHO_TANK


# ── Colisão tank ↔ paredes ─────────────────────────────────
def resolver_colisao_tank(tx, ty, paredes):
    r = TAMANHO_TANK
    for parede in paredes:
        tank_rect = pygame.Rect(tx - r, ty - r, r * 2, r * 2)
        if tank_rect.colliderect(parede):
            ox = min(tank_rect.right - parede.left, parede.right - tank_rect.left)
            oy = min(tank_rect.bottom - parede.top, parede.bottom - tank_rect.top)
            if ox < oy:
                tx += ox if tx > parede.centerx else -ox
            else:
                ty += oy if ty > parede.centery else -oy
    return tx, ty


# ── Tela de seleção de cenário ─────────────────────────────
def tela_selecao():
    fonte_titulo = pygame.font.SysFont("Consolas", 52, bold=True)
    fonte_nome   = pygame.font.SysFont("Consolas", 28, bold=True)
    fonte_desc   = pygame.font.SysFont("Consolas", 18)
    fonte_inst   = pygame.font.SysFont("Consolas", 20)
    selecionado  = 0
    nomes        = lista_cenarios

    while True:
        tela.fill(COR_FUNDO)

        t = fonte_titulo.render("⚙ TANK BATTLES ⚙", True, COR_VITORIA)
        tela.blit(t, (LARGURA // 2 - t.get_width() // 2, 40))

        sub = fonte_inst.render(
            "Selecione o cenário  ·  ↑↓ para navegar  ·  ENTER para jogar",
            True, (150, 160, 170))
        tela.blit(sub, (LARGURA // 2 - sub.get_width() // 2, 105))

        card_h, card_w = 72, 560
        inicio_y = 145
        for i, nome in enumerate(nomes):
            cy_card = inicio_y + i * (card_h + 10)
            cx_card = LARGURA // 2 - card_w // 2
            cf = (60, 70, 82) if i == selecionado else (45, 52, 62)
            cb = COR_VITORIA  if i == selecionado else (60, 70, 82)
            pygame.draw.rect(tela, cf, (cx_card, cy_card, card_w, card_h), border_radius=10)
            pygame.draw.rect(tela, cb, (cx_card, cy_card, card_w, card_h), 2, border_radius=10)
            t_nome = fonte_nome.render(nome, True, COR_VITORIA if i == selecionado else COR_HUD)
            t_desc = fonte_desc.render(CENARIOS[nome]["descricao"], True, (160, 175, 185))
            tela.blit(t_nome, (cx_card + 20, cy_card + 10))
            tela.blit(t_desc, (cx_card + 22, cy_card + 44))

        for j, linha in enumerate([
            "P1: ↑↓←→ mover  |  ENTER atirar",
            "P2: WASD mover   |  ESPAÇO atirar",
        ]):
            ct = fonte_inst.render(linha, True, (120, 140, 160))
            tela.blit(ct, (LARGURA // 2 - ct.get_width() // 2, ALTURA - 65 + j * 28))

        pygame.display.flip()
        fps.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP,):
                    selecionado = (selecionado - 1) % len(nomes)
                if event.key in (pygame.K_DOWN,):
                    selecionado = (selecionado + 1) % len(nomes)
                if event.key == pygame.K_RETURN:
                    return lista_cenarios[selecionado]


# ── Tela de vitória ────────────────────────────────────────
def tela_vitoria(vencedor, p1, p2, nome_cenario):
    fonte_g = pygame.font.SysFont("Consolas", 64, bold=True)
    fonte_p = pygame.font.SysFont("Consolas", 36)
    fonte_i = pygame.font.SysFont("Consolas", 24)
    cor_v   = COR_P1 if vencedor == 1 else COR_P2
    fade    = 0

    while True:
        tela.fill(COR_FUNDO)
        fade = min(fade + 8, 255)
        ov = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        ov.fill((*cor_v, fade // 8))
        tela.blit(ov, (0, 0))

        tv = fonte_g.render(f"PLAYER {vencedor} VENCEU!", True, COR_VITORIA)
        tela.blit(tv, (LARGURA//2 - tv.get_width()//2, 180))
        tp = fonte_p.render(f"Placar  P1: {p1}   P2: {p2}", True, COR_HUD)
        tela.blit(tp, (LARGURA//2 - tp.get_width()//2, 290))
        tm = fonte_p.render(f"Mapa: {nome_cenario}", True, (150, 170, 190))
        tela.blit(tm, (LARGURA//2 - tm.get_width()//2, 345))
        ti = fonte_i.render("ENTER → Novo mapa     ESC → Sair", True, (120, 140, 160))
        tela.blit(ti, (LARGURA//2 - ti.get_width()//2, 430))

        pygame.display.flip()
        fps.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return "selecao"
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()


# ── Tela "Round encerrado" (overlay) ──────────────────────
def exibir_round_over(vencedor_round, paredes, tx1, ty1, tx2, ty2):
    """
    Exibe por DURACAO_ROUND_OVER ms uma sobreposição anunciando
    quem ganhou o round, enquanto ainda mostra o mapa ao fundo.
    """
    fonte_g = pygame.font.SysFont("Consolas", 54, bold=True)
    fonte_p = pygame.font.SysFont("Consolas", 26)
    cor_v   = COR_P1 if vencedor_round == 1 else (COR_P2 if vencedor_round == 2 else (220, 200, 60))
    inicio  = pygame.time.get_ticks()

    while pygame.time.get_ticks() - inicio < DURACAO_ROUND_OVER:
        # Fundo do mapa congelado
        tela.fill(COR_FUNDO)
        for gx in range(0, LARGURA, 40):
            pygame.draw.line(tela, (40, 46, 55), (gx, 0), (gx, ALTURA))
        for gy in range(0, ALTURA, 40):
            pygame.draw.line(tela, (40, 46, 55), (0, gy), (LARGURA, gy))
        for parede in paredes:
            pygame.draw.rect(tela, COR_PAREDE,   parede)
            pygame.draw.rect(tela, COR_PAREDE_B, parede, 3)
            pygame.draw.line(tela, (100,115,130),
                             (parede.left+2, parede.top+2),
                             (parede.right-2, parede.top+2), 2)

        # Overlay escurecido
        ov = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 140))
        tela.blit(ov, (0, 0))

        # Painel central
        painel_w, painel_h = 500, 160
        px = LARGURA // 2 - painel_w // 2
        py = ALTURA  // 2 - painel_h // 2
        pygame.draw.rect(tela, (28, 33, 40), (px, py, painel_w, painel_h), border_radius=16)
        pygame.draw.rect(tela, cor_v,        (px, py, painel_w, painel_h), 3, border_radius=16)

        if vencedor_round == 0:
            msg = fonte_g.render("EMPATE DE ROUND!", True, (220, 200, 60))
        else:
            msg = fonte_g.render(f"PLAYER {vencedor_round} marcou ponto!", True, cor_v)
        sub = fonte_p.render("Preparando novo round...", True, (160, 175, 190))
        tela.blit(msg, (LARGURA//2 - msg.get_width()//2, py + 30))
        tela.blit(sub, (LARGURA//2 - sub.get_width()//2, py + 108))

        # Barra de progresso do tempo
        progresso = (pygame.time.get_ticks() - inicio) / DURACAO_ROUND_OVER
        barra_w   = int((painel_w - 40) * (1 - progresso))
        pygame.draw.rect(tela, (50, 58, 70),  (px + 20, py + painel_h - 22, painel_w - 40, 10), border_radius=5)
        pygame.draw.rect(tela, cor_v,         (px + 20, py + painel_h - 22, barra_w, 10), border_radius=5)

        pygame.display.flip()
        fps.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            # ENTER/ESPAÇO acelera a transição
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return


# ── Loop principal do jogo ─────────────────────────────────
def jogar(nome_cenario):
    cenario = CENARIOS[nome_cenario]
    paredes = cenario["paredes"]

    # Spawn inicial em lados opostos
    x,  y  = spawn_aleatorio(paredes, outro_pos=None)
    x2, y2 = spawn_aleatorio(paredes, outro_pos=(x, y))
    angulo  = random.randint(0, 359)
    angulo2 = random.randint(0, 359)

    projeteis      = []
    ultimo_tiro1   = ultimo_tiro2 = 0
    pontos1        = pontos2 = 0
    spawn_time1    = spawn_time2 = pygame.time.get_ticks()  # para imunidade

    fonte_hud  = pygame.font.SysFont("Consolas", 28, bold=True)
    fonte_mapa = pygame.font.SysFont("Consolas", 18)

    while True:
        agora = pygame.time.get_ticks()
        imune1 = (agora - spawn_time1) < DURACAO_IMUNIDADE
        imune2 = (agora - spawn_time2) < DURACAO_IMUNIDADE

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "selecao"

                # Player 1 atira — ENTER
                if event.key == pygame.K_RETURN:
                    balas_p1 = sum(1 for p in projeteis if p.dono == 1)
                    if agora - ultimo_tiro1 > COOLDOWN_TIRO and balas_p1 < MAX_BALAS_POR_JOGADOR:
                        cx = x + math.cos(math.radians(angulo)) * 24
                        cy = y - math.sin(math.radians(angulo)) * 24
                        projeteis.append(Projetil(cx, cy, angulo, 1))
                        ultimo_tiro1 = agora

                # Player 2 atira — ESPAÇO
                if event.key == pygame.K_SPACE:
                    balas_p2 = sum(1 for p in projeteis if p.dono == 2)
                    if agora - ultimo_tiro2 > COOLDOWN_TIRO and balas_p2 < MAX_BALAS_POR_JOGADOR:
                        cx2 = x2 + math.cos(math.radians(angulo2)) * 24
                        cy2 = y2 - math.sin(math.radians(angulo2)) * 24
                        projeteis.append(Projetil(cx2, cy2, angulo2, 2))
                        ultimo_tiro2 = agora

        fps.tick(60)

        # ── Movimento Player 1 ─────────────────────────────
        tecla = pygame.key.get_pressed()

        if tecla[pygame.K_LEFT]:  angulo += velocidade_rot
        if tecla[pygame.K_RIGHT]: angulo -= velocidade_rot
        dx_ = math.cos(math.radians(angulo))
        dy_ = -math.sin(math.radians(angulo))
        if tecla[pygame.K_UP]:
            x += velocidade * dx_; y += velocidade * dy_
        if tecla[pygame.K_DOWN]:
            x -= velocidade * dx_; y -= velocidade * dy_
        x = max(TAMANHO_TANK, min(LARGURA  - TAMANHO_TANK, x))
        y = max(TAMANHO_TANK, min(ALTURA - TAMANHO_TANK, y))
        x, y = resolver_colisao_tank(x, y, paredes)

        # ── Movimento Player 2 ─────────────────────────────
        if tecla[pygame.K_a]: angulo2 += velocidade_rot
        if tecla[pygame.K_d]: angulo2 -= velocidade_rot
        dx2_ = math.cos(math.radians(angulo2))
        dy2_ = -math.sin(math.radians(angulo2))
        if tecla[pygame.K_w]:
            x2 += velocidade * dx2_; y2 += velocidade * dy2_
        if tecla[pygame.K_s]:
            x2 -= velocidade * dx2_; y2 -= velocidade * dy2_
        x2 = max(TAMANHO_TANK, min(LARGURA  - TAMANHO_TANK, x2))
        y2 = max(TAMANHO_TANK, min(ALTURA - TAMANHO_TANK, y2))
        x2, y2 = resolver_colisao_tank(x2, y2, paredes)

        # ── Render ─────────────────────────────────────────
        tela.fill(COR_FUNDO)
        for gx in range(0, LARGURA, 40):
            pygame.draw.line(tela, (40, 46, 55), (gx, 0), (gx, ALTURA))
        for gy in range(0, ALTURA, 40):
            pygame.draw.line(tela, (40, 46, 55), (0, gy), (LARGURA, gy))

        for parede in paredes:
            pygame.draw.rect(tela, COR_PAREDE,   parede)
            pygame.draw.rect(tela, COR_PAREDE_B, parede, 3)
            pygame.draw.line(tela, (100,115,130),
                             (parede.left+2, parede.top+2),
                             (parede.right-2, parede.top+2), 2)

        desenhar_tank(tela, x,  y,  angulo,  COR_P1, COR_P1_ESCURO, imune1)
        desenhar_tank(tela, x2, y2, angulo2, COR_P2, COR_P2_ESCURO, imune2)

        # ── Projéteis ──────────────────────────────────────
        acertou = None  # (vencedor_round, perdedor)

        for p in projeteis[:]:
            p.mover(paredes)
            if not p.ativo:
                projeteis.remove(p)
                continue
            p.desenhar(tela)

            # Qualquer bala pode acertar qualquer tanque (inclusive o próprio dono).
            # Se for dano próprio, o ponto vai para o adversário.
            acertou_p1 = not imune1 and p.colidiu_com_tank(x,  y)
            acertou_p2 = not imune2 and p.colidiu_com_tank(x2, y2)

            if acertou_p1 or acertou_p2:
                if acertou_p1 and acertou_p2:
                    # Bala acertou os dois ao mesmo tempo → nenhum ponto (empate de round)
                    acertou = 0   # sinaliza round encerrado sem vencedor
                elif acertou_p1:
                    # P1 foi acertado → ponto para P2
                    pontos2 += 1
                    acertou = 2
                else:
                    # P2 foi acertado → ponto para P1
                    pontos1 += 1
                    acertou = 1
                projeteis.clear()
                break

        # ── HUD ────────────────────────────────────────────
        pygame.draw.rect(tela, (30, 35, 42), (0, 0, LARGURA, 46))
        txt1 = fonte_hud.render(f"◀ P1  {pontos1}", True, COR_P1)
        txt2 = fonte_hud.render(f"{pontos2}  P2 ▶", True, COR_P2)
        tela.blit(txt1, (20, 9))
        tela.blit(txt2, (LARGURA - txt2.get_width() - 20, 9))

        for i in range(PONTOS_VITORIA):
            cf1 = COR_P1 if i < pontos1 else (55, 65, 78)
            cf2 = COR_P2 if i < pontos2 else (55, 65, 78)
            pygame.draw.rect(tela, cf1, (200 + i*28, 13, 22, 20), border_radius=4)
            pygame.draw.rect(tela, cf2, (LARGURA - 200 - (i+1)*28, 13, 22, 20), border_radius=4)

        nm = fonte_mapa.render(nome_cenario, True, (100, 115, 130))
        tela.blit(nm, (LARGURA//2 - nm.get_width()//2, 14))

        # Barra de imunidade
        for jogador, imune, spawn_t, cx, cy, cor in [
            (1, imune1, spawn_time1, x,  y,  COR_P1),
            (2, imune2, spawn_time2, x2, y2, COR_P2),
        ]:
            if imune:
                prog = 1.0 - (agora - spawn_t) / DURACAO_IMUNIDADE
                bar_w = int(60 * prog)
                pygame.draw.rect(tela, (50,58,70), (int(cx)-30, int(cy)+28, 60, 6), border_radius=3)
                pygame.draw.rect(tela, cor,        (int(cx)-30, int(cy)+28, bar_w, 6), border_radius=3)

        pygame.display.flip()

        # ── Verifica vitória geral ──────────────────────────
        if pontos1 >= PONTOS_VITORIA:
            return tela_vitoria(1, pontos1, pontos2, nome_cenario)
        if pontos2 >= PONTOS_VITORIA:
            return tela_vitoria(2, pontos1, pontos2, nome_cenario)

        # ── Respawn após ponto marcado ──────────────────────
        if acertou is not None:
            exibir_round_over(acertou, paredes, x, y, x2, y2)

            # Novos spawns aleatórios para ambos
            x,  y  = spawn_aleatorio(paredes, outro_pos=None)
            x2, y2 = spawn_aleatorio(paredes, outro_pos=(x, y))
            angulo  = random.randint(0, 359)
            angulo2 = random.randint(0, 359)

            agora       = pygame.time.get_ticks()
            spawn_time1 = agora
            spawn_time2 = agora
            ultimo_tiro1 = ultimo_tiro2 = agora

    return "selecao"


# ── Entrada principal ──────────────────────────────────────
estado = "selecao"
while True:
    if estado == "selecao":
        nome_cenario = tela_selecao()
        estado = "jogando"
    elif estado == "jogando":
        estado = jogar(nome_cenario)





#a maior parte desse jogo foi feita por IA, a gente começou fazendo normalmente mas não tivemos aulas suficientes
#então precisamos usar a IA pra terminar ele, infelizmente a turma do 2 ano matutino de jogos digitais está muito atrasada
#tivemos somente aulas de python basico e ja fomos colocados para fazer um jogo, esse é o nosso projeto final 50% gerado por IA
#algumas partes foram ajudadas por IA mas foram feitas por pessoas reais