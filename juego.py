"""
juego.py - Reglas de las DAMAS CLASICAS (damas inglesas/americanas), tablero 8x8.

Reglas implementadas:
  * Cada jugador empieza con 12 fichas en las casillas oscuras de sus 3 primeras filas.
  * Las fichas normales se mueven 1 casilla en diagonal HACIA ADELANTE.
  * Captura: saltar en diagonal sobre una ficha rival hacia una casilla vacia. Es OPCIONAL
    (se puede mover cualquier ficha aunque haya capturas disponibles). Si se decide capturar,
    la cadena de saltos (multisalto) de esa ficha se completa.
  * Al llegar a la ultima fila la ficha se corona DAMA (se mueve y captura en las 4 diagonales,
    1 casilla). Si se corona durante una captura, el turno termina.
  * Gana quien deja al rival sin fichas o sin movimientos legales.
  * (Adicional) Si pasan 80 jugadas seguidas sin capturas ni avance de fichas normales, la partida
    se decide por material (o empate si es igual), para evitar partidas infinitas.

Coordenadas: (fila, columna), fila 0 arriba. Una ficha es (jugador, es_dama).
El HUMANO (fichas BLANCAS) empieza abajo y avanza hacia la fila 0; la IA (fichas ROJAS) empieza arriba.
Un movimiento es una tupla de casillas: ((r,c),(r,c)) o, con multisalto, ((r,c),(r,c),(r,c),...).
"""

HUMANO, IA = 1, 2
N = 8
LIMITE_SIN_PROGRESO = 80
DIAGONALES = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def rival(jugador):
    return IA if jugador == HUMANO else HUMANO


def es_oscura(r, c):
    return (r + c) % 2 == 1


def dentro(r, c):
    return 0 <= r < N and 0 <= c < N


def fila_coronacion(jugador):
    return 0 if jugador == HUMANO else N - 1


def posicion_inicial():
    pos = {}
    for r in range(N):
        for c in range(N):
            if es_oscura(r, c):
                if r < 3:
                    pos[(r, c)] = (IA, False)
                elif r > 4:
                    pos[(r, c)] = (HUMANO, False)
    return pos


def _direcciones(jugador, dama):
    if dama:
        return DIAGONALES
    return ((-1, -1), (-1, 1)) if jugador == HUMANO else ((1, -1), (1, 1))


def es_captura(mov):
    return abs(mov[1][0] - mov[0][0]) == 2


def _capturas(pos, jugador, inicio, actual, dama, camino, capturadas, salida):
    """DFS de saltos encadenados. Agrega a 'salida' cada cadena completa."""
    hubo = False
    for dr, dc in _direcciones(jugador, dama):
        medio = (actual[0] + dr, actual[1] + dc)
        fin = (actual[0] + 2 * dr, actual[1] + 2 * dc)
        if (medio in pos and pos[medio][0] != jugador and medio not in capturadas
                and dentro(*fin) and (fin not in pos or fin == inicio)):
            hubo = True
            nuevo = camino + (fin,)
            if not dama and fin[0] == fila_coronacion(jugador):
                salida.append(nuevo)          # se corona: termina el turno
            else:
                _capturas(pos, jugador, inicio, fin, dama, nuevo, capturadas | {medio}, salida)
    if not hubo and len(camino) > 1:
        salida.append(camino)


def movimientos(pos, jugador):
    """Movimientos legales del jugador: capturas (opcionales) + pasos simples de CUALQUIER ficha."""
    capturas = []
    for c, (j, dama) in pos.items():
        if j == jugador:
            _capturas(pos, jugador, c, c, dama, (c,), frozenset(), capturas)
    simples = []
    for c, (j, dama) in pos.items():
        if j == jugador:
            for dr, dc in _direcciones(jugador, dama):
                d = (c[0] + dr, c[1] + dc)
                if dentro(*d) and d not in pos:
                    simples.append((c, d))
    return capturas + simples


def aplicar(pos, mov):
    """Devuelve un NUEVO diccionario con el movimiento aplicado (no modifica el original)."""
    nuevo = dict(pos)
    jugador, dama = nuevo.pop(mov[0])
    for a, b in zip(mov, mov[1:]):
        if abs(b[0] - a[0]) == 2:
            nuevo.pop(((a[0] + b[0]) // 2, (a[1] + b[1]) // 2))
    fin = mov[-1]
    if fin[0] == fila_coronacion(jugador):
        dama = True
    nuevo[fin] = (jugador, dama)
    return nuevo


def material(pos, jugador):
    return sum(2 if d else 1 for (j, d) in pos.values() if j == jugador)


def contar(pos, jugador):
    return sum(1 for (j, _) in pos.values() if j == jugador)


class Juego:
    def __init__(self):
        self.pos = posicion_inicial()
        self.turno = HUMANO
        self.ganador = None      # HUMANO, IA, 0 (empate) o None (en juego)
        self.sin_progreso = 0

    def legales(self):
        return movimientos(self.pos, self.turno)

    def mover(self, mov):
        """Ejecuta un movimiento validando las reglas. Lanza ValueError si es invalido."""
        if self.ganador is not None:
            raise ValueError("La partida ya termino.")
        if mov not in self.legales():
            raise ValueError("Movimiento invalido.")
        jugador = self.turno
        era_normal = not self.pos[mov[0]][1]
        self.sin_progreso = 0 if (es_captura(mov) or era_normal) else self.sin_progreso + 1
        self.pos = aplicar(self.pos, mov)
        self.turno = rival(jugador)
        if not movimientos(self.pos, self.turno):
            self.ganador = jugador
        elif self.sin_progreso >= LIMITE_SIN_PROGRESO:
            a, b = material(self.pos, HUMANO), material(self.pos, IA)
            self.ganador = HUMANO if a > b else IA if b > a else 0
