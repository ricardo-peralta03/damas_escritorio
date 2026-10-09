"""
simular.py - Pruebas automaticas IA vs IA para comparar niveles (util para el informe).
Uso:  python simular.py
"""
import time
import agente
from juego import HUMANO, IA, Juego

NOMBRES = {1: "Facil", 2: "Medio", 3: "Dificil"}


def partida(nivel_blancas, nivel_rojas):
    g = Juego()
    niveles = {HUMANO: nivel_blancas, IA: nivel_rojas}
    t0, turnos = time.time(), 0
    while g.ganador is None and turnos < 300:
        j = g.turno
        g.mover(agente.elegir_movimiento(g.pos, niveles[j], j))
        turnos += 1
    return g.ganador, turnos, time.time() - t0


if __name__ == "__main__":
    for a, b in [(1, 2), (2, 3), (1, 3)]:
        g, turnos, seg = partida(a, b)
        res = {HUMANO: f"{NOMBRES[a]} (blancas)", IA: f"{NOMBRES[b]} (rojas)", 0: "empate", None: "sin resultado"}[g]
        print(f"{NOMBRES[a]:8} vs {NOMBRES[b]:8} -> gana: {res:18} jugadas: {turnos:3}  tiempo: {seg:.1f}s")
