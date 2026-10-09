"""
agente.py - Agente inteligente de Damas con tres niveles de dificultad.

El agente solo usa 'pos' (las fichas visibles en el tablero): la misma informacion que ve
un jugador humano. No hace trampa.

  Facil   -> movimiento aleatorio entre los movimientos legales.
  Medio   -> Minimax de profundidad 2 con heuristica basica (solo material).
  Dificil -> Minimax con poda alfa-beta de profundidad 6 + busqueda de quietud en capturas,
             con heuristica avanzada (material, avance, centro y defensa de la fila trasera).
"""
import random
from juego import IA, aplicar, es_captura, movimientos, rival

FACIL, MEDIO, DIFICIL = 1, 2, 3
PROFUNDIDAD = {MEDIO: 2, DIFICIL: 6}
GANAR = 100000
INF = 10 ** 9


def evaluar(pos, jugador, avanzada=True):
    """Valor del tablero para 'jugador' (mayor = mejor).
    Basica: solo material.  Avanzada: + avance, control del centro y fila trasera."""
    total = 0
    for (r, c), (j, dama) in pos.items():
        if dama:
            v = 180
        else:
            v = 100
            if avanzada:
                avance = (7 - r) if j != IA else r      # filas recorridas (0..7)
                # el humano avanza hacia la fila 0; la IA hacia la 7
                v += 5 * avance
                if avance == 0:
                    v += 8                               # defensa de la fila trasera
        if avanzada:
            v += 2 * (3.5 - max(abs(r - 3.5), abs(c - 3.5)))   # centro del tablero
        total += v if j == jugador else -v
    return total


def _minimax(pos, prof, alfa, beta, turno, yo, avanzada):
    movs = movimientos(pos, turno)
    if not movs:                                   # quien no puede mover pierde
        return (-GANAR - prof) if turno == yo else (GANAR + prof)
    movs.sort(key=es_captura, reverse=True)        # capturas primero: mejor poda
    quieta = prof <= 0
    if quieta:
        # Busqueda de quietud: al llegar al limite solo se siguen explorando las capturas
        # (evita "efecto horizonte"); si nadie quiere capturar, se evalua el tablero.
        estatico = evaluar(pos, yo, avanzada)
        movs = [m for m in movs if es_captura(m)]
        if not movs or prof < -6:
            return estatico
    if turno == yo:
        mejor = estatico if quieta else -INF
        for m in movs:
            mejor = max(mejor, _minimax(aplicar(pos, m), prof - 1, alfa, beta, rival(turno), yo, avanzada))
            alfa = max(alfa, mejor)
            if alfa >= beta:
                break                              # poda beta
        return mejor
    mejor = estatico if quieta else INF
    for m in movs:
        mejor = min(mejor, _minimax(aplicar(pos, m), prof - 1, alfa, beta, rival(turno), yo, avanzada))
        beta = min(beta, mejor)
        if alfa >= beta:
            break                                  # poda alfa
    return mejor


def _mejor_movimiento(pos, jugador, prof, avanzada):
    mejores, mejor_val, alfa = [], -INF, -INF
    for m in movimientos(pos, jugador):
        v = _minimax(aplicar(pos, m), prof - 1, alfa, INF, rival(jugador), jugador, avanzada)
        if v > mejor_val:
            mejor_val, mejores = v, [m]
        elif v == mejor_val:
            mejores.append(m)
        alfa = mejor_val - 1                       # ventana que conserva los empates exactos
    return random.choice(mejores)                  # entre iguales, variedad


def elegir_movimiento(pos, nivel, jugador=IA):
    """Punto de entrada: devuelve el movimiento (tupla de casillas) segun el nivel."""
    if nivel == FACIL:
        return random.choice(movimientos(pos, jugador))
    if nivel == MEDIO:
        return _mejor_movimiento(pos, jugador, PROFUNDIDAD[MEDIO], avanzada=False)
    return _mejor_movimiento(pos, jugador, PROFUNDIDAD[DIFICIL], avanzada=True)
