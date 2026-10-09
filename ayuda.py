"""
ayuda.py - Ventana de instrucciones (pestaña de reglas + pestaña con el video tutorial de YouTube).
"""
import webbrowser

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPushButton, QTabWidget,
                               QTextBrowser, QVBoxLayout, QWidget)

try:  # El navegador integrado viene con PySide6 (paquete PySide6-Addons)
    from PySide6.QtWebEngineWidgets import QWebEngineView
    HAY_WEB = True
except ImportError:
    HAY_WEB = False

VIDEO_ID = "r-7R2sCW3Ro"
URL_VIDEO = f"https://youtu.be/{VIDEO_ID}"
URL_WATCH = f"https://www.youtube.com/watch?v={VIDEO_ID}"

HTML_VIDEO = f"""<!DOCTYPE html><html><body style="margin:0;background:#000;">
<iframe style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
 src="https://www.youtube.com/embed/{VIDEO_ID}?rel=0" title="Tutorial de damas"
 allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
 referrerpolicy="strict-origin-when-cross-origin"></iframe></body></html>"""

REGLAS_HTML = """
<style>
  body { font-size: 14px; color:#212529; }
  h2 { color:#2b2d42; margin-bottom:2px; }
  h3 { color:#d62828; margin-bottom:2px; }
  li { margin-bottom:4px; }
</style>
<h2>Cómo jugar a las Damas</h2>
<p>Si nunca has jugado, no te preocupes: en pocos minutos aprendes lo básico.</p>

<h3>1. El objetivo</h3>
<p>Ganas si <b>eliminas todas las fichas rojas</b> de la IA o la dejas <b>sin movimientos posibles</b>.
Si te pasa a ti, pierdes.</p>

<h3>2. Tus fichas y el tablero</h3>
<ul>
<li>Tú juegas con las fichas <b>BLANCAS</b> (abajo). La IA juega con las <b>ROJAS</b> (arriba).</li>
<li>Tú siempre empiezas. Después se turnan: una jugada cada uno.</li>
<li>El tablero es de 8×8 y <b>solo se juega sobre las casillas oscuras</b>.</li>
</ul>

<h3>3. Cómo mover una ficha (paso a paso)</h3>
<ol>
<li>Haz clic en una de tus fichas blancas: se marca con un <b style="color:#1e90ff">borde azul</b>.</li>
<li>Aparecen <b style="color:#2a9d8f">puntos verdes</b> en las casillas a las que puede ir.</li>
<li>Haz clic en un punto verde y la ficha se mueve.</li>
<li>¿Te arrepientes? Haz clic en otra ficha tuya para cambiar de selección.</li>
</ol>
<p>Si haces un movimiento no permitido, el juego te mostrará un mensaje y podrás intentarlo otra vez.</p>

<h3>4. Movimiento normal</h3>
<p>Una ficha normal avanza <b>una casilla en diagonal hacia adelante</b> (hacia arriba), siempre a una
casilla <b>vacía</b>. No puede ir hacia atrás ni en línea recta.</p>

<h3>5. Capturar fichas rivales</h3>
<ul>
<li>Si una ficha roja está en <b>diagonal, pegada a la tuya</b>, y justo detrás de ella hay una casilla
vacía, puedes <b>saltar sobre ella</b>: caes en esa casilla vacía y la ficha roja <b>desaparece</b>.</li>
<li><b>Capturar es opcional</b> en esta versión: puedes mover cualquier ficha aunque tengas una captura disponible.</li>
<li><b>Multisalto:</b> si después de saltar puedes saltar otra ficha, la captura continúa en cadena.
El punto verde te muestra dónde terminará el recorrido completo.</li>
<li>¡Cuidado! La IA también te puede capturar a ti.</li>
</ul>

<h3>6. Coronar una dama</h3>
<p>Si una de tus fichas llega a la <b>última fila de arriba</b>, se convierte en <b>dama</b> y se marca con un
<b style="color:#d4a017">anillo dorado</b>. La dama es más poderosa: se mueve y captura en
<b>las 4 diagonales</b> (hacia adelante y hacia atrás), de una casilla en una casilla.
Si te coronas durante una captura, tu turno termina ahí.</p>

<h3>7. Colores que verás en pantalla</h3>
<ul>
<li><b style="color:#1e90ff">Borde azul</b>: la ficha que seleccionaste.</li>
<li><b style="color:#2a9d8f">Punto verde</b>: casillas a las que puedes mover.</li>
<li><b style="color:#d4a017">Cuadro amarillo</b>: origen y destino de la última jugada de la IA.</li>
<li><b style="color:#d4a017">Anillo dorado</b>: esa ficha es una dama.</li>
<li>Arriba aparece de quién es el turno y cuántas fichas quedan (por ejemplo, 12 vs 12).</li>
</ul>

<h3>8. Cuándo termina la partida</h3>
<ul>
<li>Ganas si la IA se queda sin fichas o sin movimientos. Pierdes si te ocurre a ti.</li>
<li>Si pasan 80 jugadas seguidas sin capturas ni avance de fichas normales, se decide por quién tiene
más material (las damas valen doble). Si es igual, hay empate.</li>
<li>Al terminar puedes jugar de nuevo o volver al menú para cambiar la dificultad.</li>
</ul>

<h3>9. Consejos para principiantes</h3>
<ul>
<li>Empieza en nivel <b>Fácil</b> y sube poco a poco.</li>
<li>Avanza tus fichas en grupo: una ficha sola es fácil de capturar.</li>
<li>Intenta conservar algunas fichas en tu fila de abajo para que la IA no pueda coronar tan fácil.</li>
<li>Antes de mover, mira si la ficha rival podrá saltar sobre la tuya.</li>
<li>Mira el video tutorial en la otra pestaña. ¡Mucha suerte!</li>
</ul>
"""


class VentanaAyuda(QDialog):
    def __init__(self, padre=None):
        super().__init__(padre)
        self.setWindowTitle("Instrucciones")
        self.resize(900, 680)
        self.vista = None
        self.video_cargado = False

        self.tabs = QTabWidget()
        texto = QTextBrowser()
        texto.setOpenExternalLinks(True)
        texto.setStyleSheet("background:#f8f9fa; padding:10px; border-radius:8px;")
        texto.setHtml(REGLAS_HTML)
        self.tabs.addTab(texto, "📖  Reglas e instrucciones")
        self.tabs.addTab(self._crear_pagina_video(), "▶  Video tutorial")
        self.tabs.currentChanged.connect(self._cambio_pestana)

        cerrar = QPushButton("Cerrar")
        cerrar.clicked.connect(self.accept)
        caja = QVBoxLayout(self)
        caja.addWidget(self.tabs)
        caja.addWidget(cerrar)
        self.finished.connect(lambda *_: self._detener_video())

    def _crear_pagina_video(self):
        pagina = QWidget()
        caja = QVBoxLayout(pagina)
        if HAY_WEB:
            self.vista = QWebEngineView()
            caja.addWidget(self.vista, 1)
            fila = QHBoxLayout()
            b1 = QPushButton("¿No carga? Ver la página de YouTube aquí")
            b1.clicked.connect(lambda: self.vista.load(QUrl(URL_WATCH)))
            b2 = QPushButton("Abrir en el navegador")
            b2.clicked.connect(lambda: webbrowser.open(URL_VIDEO))
            fila.addWidget(b1)
            fila.addWidget(b2)
            caja.addLayout(fila)
        else:
            aviso = QLabel("No se pudo cargar el reproductor integrado.\n"
                           "Instala PySide6 completo (pip install PySide6) o abre el video en el navegador.")
            caja.addWidget(aviso)
            b = QPushButton("Abrir video en YouTube")
            b.clicked.connect(lambda: webbrowser.open(URL_VIDEO))
            caja.addWidget(b)
        return pagina

    def _cambio_pestana(self, indice):
        if indice == 1 and self.vista is not None and not self.video_cargado:
            # El video se carga solo al abrir la pestaña (y se detiene al salir de ella)
            self.vista.setHtml(HTML_VIDEO, QUrl("https://www.youtube.com/"))
            self.video_cargado = True
        elif indice != 1:
            self._detener_video()

    def _detener_video(self):
        if self.vista is not None and self.video_cargado:
            self.vista.setHtml("")
            self.video_cargado = False
