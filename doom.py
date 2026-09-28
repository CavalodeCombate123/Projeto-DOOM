import math
import pygame

pygame.init()

LARGURA, ALTURA = 800, 600
CENTRO_X, HORIZONTE = LARGURA // 2, ALTURA // 2
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Jogo")
relogio = pygame.time.Clock()
fonte = pygame.font.Font(None, 32)
fonte_titulo = pygame.font.Font(None, 64)

mapa = [
    "####################",
    "#........#.........#",
    "#........#.........#",
    "#........#.........#",
    "#..#.....##........#",
    "####..#...#........#",
    "#............#.....#",
    "#........#.........#",
    "####################",
]

T = 8
FOV = math.pi / 3
COLUNAS = 160
L = LARGURA // COLUNAS
ESCALA_PAREDE = 500
INIMIGOS_INICIAIS = [[9.5, 4.5], [11.5, 1.5], [8.5, 7.5]]
CAPACIDADE_PENTE = 6


def reiniciar():
    global x, y, ang, inimigos, municao, tiro, estado
    x, y, ang = 1.5, 4.5, 0.0
    inimigos = [pos.copy() for pos in INIMIGOS_INICIAIS]
    municao = CAPACIDADE_PENTE
    tiro = 0
    estado = "jogando"


def parede(px, py):
    ix, iy = int(px), int(py)
    return not (0 <= iy < len(mapa) and 0 <= ix < len(mapa[iy])) or mapa[iy][ix] == "#"


def raio(a):
    c, s = math.cos(a), math.sin(a)
    d = 0.0
    while not parede(x + c * d, y + s * d):
        d += 0.02
    return d


reiniciar()
botao_reiniciar = pygame.Rect(0, 0, 260, 58)
botao_reiniciar.center = (CENTRO_X, HORIZONTE + 60)
rodando = True

while rodando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        elif evento.type == pygame.KEYDOWN:
            if estado == "jogando":
                if evento.key == pygame.K_ESCAPE:
                    estado = "pausado"
                elif evento.key == pygame.K_SPACE and municao > 0 and tiro == 0:
                    municao -= 1
                    tiro = 6
                elif evento.key == pygame.K_r and municao == 0:
                    municao = CAPACIDADE_PENTE
            elif estado == "pausado" and evento.key in (pygame.K_ESCAPE, pygame.K_SPACE):
                estado = "jogando"
            elif estado == "game_over" and evento.key == pygame.K_SPACE:
                reiniciar()
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if estado == "game_over" and botao_reiniciar.collidepoint(evento.pos):
                reiniciar()

    if estado == "jogando":
        k = pygame.key.get_pressed()
        ang += (int(k[pygame.K_RIGHT]) - int(k[pygame.K_LEFT])) * 0.05
        passo = (int(k[pygame.K_UP]) - int(k[pygame.K_DOWN])) * 0.08
        dx, dy = math.cos(ang) * passo, math.sin(ang) * passo
        if not parede(x + dx * 4, y):
            x += dx
        if not parede(x, y + dy * 4):
            y += dy

        for inimigo in inimigos:
            dx, dy = x - inimigo[0], y - inimigo[1]
            distancia = math.hypot(dx, dy)
            if distancia <= 0.45:
                estado = "game_over"
                break
            if distancia > 0.8:
                inimigo[0] += dx / distancia * 0.03
                inimigo[1] += dy / distancia * 0.03

        if estado == "jogando" and tiro == 6:
            # Acerta o inimigo visível mais próximo do centro da mira.
            alvos = []
            for inimigo in inimigos:
                dx, dy = inimigo[0] - x, inimigo[1] - y
                distancia = math.hypot(dx, dy)
                relativo = (math.atan2(dy, dx) - ang + math.pi) % (2 * math.pi) - math.pi
                coluna = int((CENTRO_X + relativo / (FOV / 2) * CENTRO_X) / L)
                if 0 <= coluna < COLUNAS and abs(relativo) < 0.025:
                    alvos.append((distancia, inimigo))
            if alvos:
                inimigos.remove(min(alvos, key=lambda alvo: alvo[0])[1])

        if tiro > 0:
            tiro -= 1
        if not inimigos:
            inimigos = [pos.copy() for pos in INIMIGOS_INICIAIS]

    # Céu, chão e paredes usam o centro vertical da tela como horizonte.
    tela.fill((22, 22, 22))
    pygame.draw.rect(tela, (120, 70, 42), (0, HORIZONTE, LARGURA, ALTURA - HORIZONTE))
    distancias = []
    for i in range(COLUNAS):
        angulo_raio = ang - FOV / 2 + FOV * (i + 0.5) / COLUNAS
        distancia = raio(angulo_raio)
        corrigida = max(0.05, distancia * math.cos(angulo_raio - ang))
        distancias.append(corrigida)
        altura_parede = min(ALTURA, ESCALA_PAREDE / corrigida)
        px = x + math.cos(angulo_raio) * distancia
        luz = max(30, int(230 - corrigida * 22))
        if abs(px - round(px)) < 0.03:
            luz = int(luz * 0.7)
        cor = (luz, int(luz * 0.9), int(luz * 0.75))
        pygame.draw.rect(tela, cor, (i * L, HORIZONTE - altura_parede / 2, L + 1, altura_parede))

    # Desenha primeiro os inimigos mais distantes para respeitar a oclusão das paredes.
    for inimigo in sorted(inimigos, key=lambda e: -math.dist(e, (x, y))):
        dx, dy = inimigo[0] - x, inimigo[1] - y
        distancia = math.hypot(dx, dy)
        relativo = (math.atan2(dy, dx) - ang + math.pi) % (2 * math.pi) - math.pi
        sx = CENTRO_X + relativo / (FOV / 2) * CENTRO_X
        coluna = int(sx / L)
        if not 0 <= coluna < COLUNAS or distancias[coluna] < distancia:
            continue
        altura = min(ALTURA, ESCALA_PAREDE / max(distancia, 0.1))
        corpo = pygame.Rect(0, 0, max(2, int(altura * 0.5)), max(2, int(altura * 0.7)))
        corpo.midbottom = (int(sx), int(HORIZONTE + altura / 2))
        pygame.draw.ellipse(tela, "darkred", corpo)
        for ox in (sx - altura * 0.1, sx + altura * 0.1):
            pygame.draw.circle(tela, "gold", (int(ox), int(corpo.y + altura * 0.2)), max(1, int(altura / 20)))

    # Mini mapa no canto superior esquerdo.
    for my, linha in enumerate(mapa):
        for mx, celula in enumerate(linha):
            if celula == "#":
                pygame.draw.rect(tela, "gray40", (mx * T, my * T, T, T))
    for ex, ey in inimigos:
        pygame.draw.circle(tela, "red", (int(ex * T), int(ey * T)), 3)
    pygame.draw.circle(tela, "white", (int(x * T), int(y * T)), 5)

    if tiro > 0 and estado == "jogando":
        pygame.draw.circle(tela, "orange", (CENTRO_X, HORIZONTE), 34)
        pygame.draw.circle(tela, "yellow", (CENTRO_X, HORIZONTE), 18)
    arma = [(CENTRO_X - 45, 520), (CENTRO_X - 20, 440),
            (CENTRO_X + 20, 440), (CENTRO_X + 45, 520)]
    pygame.draw.polygon(tela, "gray35", arma)
    pygame.draw.rect(tela, "gray20", (CENTRO_X - 12, 400, 24, 60))
    pygame.draw.circle(tela, "white", (CENTRO_X, HORIZONTE), 3)
    texto_municao = fonte.render(f"Balas: {municao}/{CAPACIDADE_PENTE}  |  R: recarregar", True, "white")
    tela.blit(texto_municao, (12, ALTURA - 38))

    if estado in ("pausado", "game_over"):
        filtro = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        filtro.fill((0, 0, 0, 175))
        tela.blit(filtro, (0, 0))
        if estado == "pausado":
            titulo = fonte_titulo.render("PAUSADO", True, "white")
            instrucao = fonte.render("Pressione Esc ou Espaço para continuar", True, "white")
            tela.blit(titulo, titulo.get_rect(center=(CENTRO_X, HORIZONTE - 20)))
            tela.blit(instrucao, instrucao.get_rect(center=(CENTRO_X, HORIZONTE + 35)))
        else:
            titulo = fonte_titulo.render("GAME - OVER", True, "white")
            pygame.draw.rect(tela, "white", botao_reiniciar, border_radius=8)
            texto_botao = fonte.render("tente novamente", True, "black")
            tela.blit(titulo, titulo.get_rect(center=(CENTRO_X, HORIZONTE - 45)))
            tela.blit(texto_botao, texto_botao.get_rect(center=botao_reiniciar.center))
    pygame.display.flip()
    relogio.tick(30)

pygame.quit()
