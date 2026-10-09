"""
main.py - DAMAS CLASICAS: Jugador (blancas) vs IA (rojas) - version de escritorio (PySide6).
Ejecutar:  python main.py
"""
import sys
import threading

from PySide6.QtCore import QObject, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QStackedWidget, QVBoxLayout, QWidget)

import agente
import juego
from ayuda import VentanaAyuda
from juego import HUMANO, IA

NOMBRE_NIVEL = {agente.FACIL: "Fácil", agente.MEDIO: "Medio", agente.DIFICIL: "Difícil"}
COLOR_NIVEL = {agente.FACIL: "#52b788", agente.MEDIO: "#f4a261", agente.DIFICIL: "#e63946"}
COLOR_FICHA = {HUMANO: "#f8f9fa", IA: "#d62828"}      # jugador = blancas, IA = rojas
COLOR_BORDE = {HUMANO: "#8d99ae", IA: "#7a0f0f"}

ESTILO = """
QMainWindow, QDialog, QWidget#fondo { background: #2b2d42; }
QLabel { color: white; }
QPushButton { background: #495057; color: white; border: none; border-radius: 8px;
              padding: 10px 16px; font-size: 15px; font-weight: bold; }
QPushButton:hover { background: #5c6770; }
QTabBar::tab { background: #3d405b; color: white; padding: 10px 18px; font-size: 14px;
               border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 3px; }
QTabBar::tab:selected { background: #5a5f8c; font-weight: bold; }
QTabWidget::pane { border: none; }
"""


def boton(texto, color=None):
    b = QPushButton(texto)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if color:
        b.setStyleSheet(f"QPushButton {{ background:{color}; padding:14px; font-size:18px; }}"
                        f"QPushButton:hover {{ background:{color}; border: 2px solid white; }}")
    return b


class Tablero(QWidget):
    """Dibuja el tablero 8x8 y emite la casilla (fila, columna) donde se hace clic."""
    clic = Signal(int, int)

    def __init__(self):
        super().__init__()
        self.pos_fichas, self.sel, self.dest, self.ultimo = {}, None, set(), ()
        self.setMinimumSize(360, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _geom(self):
        tam = min(self.width(), self.height()) / 8
        return tam, (self.width() - 8 * tam) / 2, (self.height() - 8 * tam) / 2

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        tam, ox, oy = self._geom()
        for r in range(8):
            for c in range(8):
                p.fillRect(QRectF(ox + c * tam, oy + r * tam, tam, tam),
                           QColor("#3a3a3a" if juego.es_oscura(r, c) else "#e9e9e9"))
        p.setBrush(Qt.BrushStyle.NoBrush)
        for celdas, color, grosor in ((self.ultimo, "#ffd166", 3), ((self.sel,) if self.sel else (), "#4cc9f0", 4)):
            p.setPen(QPen(QColor(color), grosor))
            for r, c in celdas:
                p.drawRect(QRectF(ox + c * tam + 2, oy + r * tam + 2, tam - 4, tam - 4))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#80ed99"))
        for r, c in self.dest:                                   # destinos posibles
            p.drawEllipse(QRectF(ox + (c + 0.3) * tam, oy + (r + 0.3) * tam, tam * 0.4, tam * 0.4))
        for (r, c), (j, dama) in self.pos_fichas.items():        # fichas
            x, y = ox + c * tam, oy + r * tam
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(COLOR_BORDE[j]))
            p.drawEllipse(QRectF(x + tam * 0.09, y + tam * 0.09, tam * 0.82, tam * 0.82))
            p.setBrush(QColor(COLOR_FICHA[j]))
            p.drawEllipse(QRectF(x + tam * 0.15, y + tam * 0.15, tam * 0.70, tam * 0.70))
            if dama:                                             # dama = anillo dorado
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor("#ffbe0b"), max(2.0, tam * 0.07)))
                p.drawEllipse(QRectF(x + tam * 0.3, y + tam * 0.3, tam * 0.4, tam * 0.4))

    def mousePressEvent(self, ev):
        tam, ox, oy = self._geom()
        c, r = int((ev.position().x() - ox) // tam), int((ev.position().y() - oy) // tam)
        if 0 <= r < 8 and 0 <= c < 8:
            self.clic.emit(r, c)


class Puente(QObject):
    """Lleva la jugada calculada por el hilo de la IA hasta el hilo de la interfaz."""
    listo = Signal(int, object)


class PaginaMenu(QWidget):
    def __init__(self, ventana):
        super().__init__()
        self.setObjectName("fondo")
        caja = QVBoxLayout(self)
        caja.setContentsMargins(60, 40, 60, 40)
        caja.setSpacing(12)
        titulo = QLabel("DAMAS")
        titulo.setFont(QFont("Arial", 42, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc = QLabel("Tú (blancas) vs IA (rojas)\nMueve en diagonal y captura las fichas rivales.\n"
                      "Gana quien deje al rival sin fichas o sin movimientos.")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color:#adb5bd; font-size:14px;")
        sel = QLabel("Selecciona la dificultad")
        sel.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        sel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for w in (titulo, desc, sel):
            caja.addWidget(w)
        for nivel in (agente.FACIL, agente.MEDIO, agente.DIFICIL):
            b = boton(NOMBRE_NIVEL[nivel], COLOR_NIVEL[nivel])
            b.clicked.connect(lambda _=False, n=nivel: ventana.iniciar(n))
            caja.addWidget(b)
        caja.addStretch()
        b_ayuda = boton("📖  Instrucciones y video tutorial", "#3d5a80")
        b_ayuda.clicked.connect(ventana.abrir_ayuda)
        b_salir = QPushButton("Salir")
        b_salir.clicked.connect(ventana.close)
        caja.addWidget(b_ayuda)
        caja.addWidget(b_salir)


class PaginaJuego(QWidget):
    def __init__(self, ventana):
        super().__init__()
        self.setObjectName("fondo")
        self.ventana = ventana
        self.token, self.nivel, self.bloqueado, self.movs_sel = 0, agente.FACIL, True, []
        self.g = juego.Juego()
        caja = QVBoxLayout(self)
        caja.setContentsMargins(12, 10, 12, 12)
        self.lbl_turno = QLabel()
        self.lbl_turno.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        self.lbl_turno.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_msg = QLabel()
        self.lbl_msg.setStyleSheet("color:#ffd166; font-size:13px;")
        self.lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_msg.setWordWrap(True)
        self.lbl_msg.setMinimumHeight(38)
        self.tablero = Tablero()
        self.tablero.clic.connect(self.tocar)
        barra = QHBoxLayout()
        for texto, accion in (("Reiniciar", lambda: self.iniciar(self.nivel)),
                              ("Menú principal", ventana.ir_menu),
                              ("📖 Instrucciones", ventana.abrir_ayuda)):
            b = QPushButton(texto)
            b.clicked.connect(lambda _=False, a=accion: a())
            barra.addWidget(b)
        for w in (self.lbl_turno, self.lbl_msg):
            caja.addWidget(w)
        caja.addWidget(self.tablero, 1)
        caja.addLayout(barra)
        self.puente = Puente()
        self.puente.listo.connect(self._jugada_ia)

    def iniciar(self, nivel):
        self.token += 1                      # invalida cualquier jugada pendiente de la IA
        self.nivel, self.g, self.bloqueado, self.movs_sel = nivel, juego.Juego(), False, []
        t = self.tablero
        t.sel, t.dest, t.ultimo = None, set(), ()
        self.msg(f"Nivel {NOMBRE_NIVEL[nivel]}. Haz clic en una de tus fichas blancas.")
        self.refrescar()

    def msg(self, texto):
        self.lbl_msg.setText(texto)

    def refrescar(self):
        g, t = self.g, self.tablero
        t.pos_fichas = dict(g.pos)
        t.update()
        b, r = juego.contar(g.pos, HUMANO), juego.contar(g.pos, IA)
        if g.ganador is not None:
            self.lbl_turno.setText("Partida terminada")
            self.lbl_turno.setStyleSheet("color:white;")
        elif g.turno == HUMANO:
            self.lbl_turno.setText(f"Turno: TÚ (blancas)    {b} vs {r}")
            self.lbl_turno.setStyleSheet("color:#f8f9fa;")
        else:
            self.lbl_turno.setText(f"Turno: IA (rojas) pensando...    {b} vs {r}")
            self.lbl_turno.setStyleSheet("color:#ff6b6b;")

    def tocar(self, r, c):
        if self.bloqueado:
            return
        celda, t = (r, c), self.tablero
        ficha = self.g.pos.get(celda)
        if ficha and ficha[0] == HUMANO:
            self.movs_sel = [m for m in self.g.legales() if m[0] == celda]
            t.sel, t.dest = celda, {m[-1] for m in self.movs_sel}
            self.msg("Elige una casilla con punto verde." if self.movs_sel
                     else "Esa ficha no tiene movimientos disponibles.")
        elif ficha:
            self.msg("Esa ficha es del rival. Haz clic en una ficha blanca.")
        elif t.sel is None:
            self.msg("Primero haz clic en una de tus fichas blancas.")
        else:
            elegido = next((m for m in self.movs_sel if m[-1] == celda), None)
            if elegido is None:
                self.msg("Movimiento inválido: solo en diagonal a una casilla vacía "
                         "(hacia adelante, salvo damas) o saltando una ficha rival.")
                return
            self.g.mover(elegido)
            t.sel, t.dest, t.ultimo, self.movs_sel = None, set(), (), []
            self.msg("")
            self.refrescar()
            if self.g.ganador is not None:
                return self.terminar()
            self.bloqueado = True
            token, pos, nivel = self.token, dict(self.g.pos), self.nivel
            # La IA piensa en otro hilo para que la ventana no se congele
            threading.Thread(target=lambda: self.puente.listo.emit(
                token, agente.elegir_movimiento(pos, nivel, IA)), daemon=True).start()
            return
        self.refrescar()

    def _jugada_ia(self, token, mov):
        if token != self.token:              # se reinicio o se salio al menu mientras pensaba
            return
        self.g.mover(mov)
        self.tablero.ultimo = (mov[0], mov[-1])
        self.refrescar()
        if self.g.ganador is not None:
            return self.terminar()
        self.bloqueado = False
        self.msg("Tu turno.")

    def terminar(self):
        self.bloqueado = True
        self.msg("Fin de la partida.")
        texto, color = {HUMANO: ("¡GANASTE!", "#80ed99"), IA: ("PERDISTE", "#ff6b6b"),
                        0: ("EMPATE", "#ffd166")}[self.g.ganador]
        dlg = QDialog(self)
        dlg.setWindowTitle("Fin de la partida")
        dlg.setMinimumWidth(320)
        caja = QVBoxLayout(dlg)
        titulo = QLabel(texto)
        titulo.setFont(QFont("Arial", 34, QFont.Weight.Bold))
        titulo.setStyleSheet(f"color:{color};")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel(f"Nivel {NOMBRE_NIVEL[self.nivel]}")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        b1, b2 = QPushButton("Jugar de nuevo"), QPushButton("Menú principal")
        b1.clicked.connect(dlg.accept)
        b2.clicked.connect(dlg.reject)
        for w in (titulo, sub, b1, b2):
            caja.addWidget(w)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.iniciar(self.nivel)
        else:
            self.ventana.ir_menu()


class Ventana(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Damas - Jugador vs IA")
        self.resize(560, 780)
        self.pila = QStackedWidget()
        self.menu, self.partida = PaginaMenu(self), PaginaJuego(self)
        self.pila.addWidget(self.menu)
        self.pila.addWidget(self.partida)
        self.setCentralWidget(self.pila)

    def iniciar(self, nivel):
        self.partida.iniciar(nivel)
        self.pila.setCurrentWidget(self.partida)

    def ir_menu(self):
        self.partida.token += 1
        self.pila.setCurrentWidget(self.menu)

    def abrir_ayuda(self):
        VentanaAyuda(self).exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(ESTILO)
    ventana = Ventana()
    ventana.show()
    sys.exit(app.exec())
