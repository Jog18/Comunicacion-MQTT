#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard ESP32 MQTT — Interfaz Tkinter
Equivalente visual del dashboard HTML (dark theme).
Al ejecutar este script se abre la ventana y se conecta al broker MQTT
usando la clase MQTTClient definida en mqtt_client.py.
"""

import tkinter as tk
from datetime import datetime

from mqtt_client import MQTTClient

# ── Paleta de colores (misma que el HTML) ─────────────────────────────────────
BG      = "#0d1117"   # fondo general
CARD_BG = "#161b22"   # fondo de tarjetas
BORDER  = "#30363d"   # bordes
TEXT    = "#e6edf3"   # texto principal
DIM     = "#8b949e"   # texto secundario
DIMMER  = "#484f58"   # timestamp
BLUE    = "#58a6ff"   # pot 1
PURPLE  = "#bc8cff"   # pot 2
ORANGE  = "#f0883e"   # pot 3
RED_C   = "#f85149"   # LM35 / desconectado
GREEN   = "#3fb950"   # conectado / botón ON
LED_ON  = "#ffd60a"   # LED encendido
LED_OFF = "#21262d"   # LED apagado
BAR_BG  = "#21262d"   # fondo de barras de progreso


# ── Widget: tarjeta de sensor ─────────────────────────────────────────────────

class SensorCard(tk.Frame):
    """Tarjeta oscura con etiqueta, valor grande, unidad y barra de progreso."""

    def __init__(self, parent, label: str, unit: str, color: str,
                 min_val: float, max_val: float, decimals: int, **kw):
        super().__init__(
            parent, bg=CARD_BG,
            highlightbackground=BORDER, highlightthickness=1,
            padx=20, pady=16, **kw,
        )
        self._min = min_val
        self._max = max_val
        self._dec = decimals
        self._color = color
        self._pct = 0.0

        # Etiqueta en mayúsculas (ej. "POTENCIÓMETRO 1")
        tk.Label(
            self, text=label.upper(), bg=CARD_BG, fg=DIM,
            font=("Segoe UI", 7, "bold"), anchor="w",
        ).pack(fill="x")

        # Valor numérico grande
        self._val_lbl = tk.Label(
            self, text="—", bg=CARD_BG, fg=color,
            font=("Segoe UI", 26, "bold"), anchor="w",
        )
        self._val_lbl.pack(fill="x")

        # Unidad
        tk.Label(
            self, text=unit, bg=CARD_BG, fg=DIM,
            font=("Segoe UI", 8), anchor="w",
        ).pack(fill="x", pady=(0, 10))

        # Barra de progreso (Canvas para control total del color)
        self._bar = tk.Canvas(self, bg=CARD_BG, height=8, highlightthickness=0)
        self._bar.pack(fill="x")
        self._bar.bind("<Configure>", self._redraw)

    def _redraw(self, _=None):
        w = self._bar.winfo_width() or 1
        self._bar.delete("all")
        # Fondo de la barra
        self._bar.create_rectangle(0, 0, w, 8, fill=BAR_BG, outline="")
        # Relleno coloreado
        fill_w = int(w * self._pct / 100)
        if fill_w > 0:
            self._bar.create_rectangle(0, 0, fill_w, 8, fill=self._color, outline="")

    def set_value(self, value: float):
        """Actualiza el valor mostrado y la barra de progreso."""
        self._val_lbl.config(text=f"{value:.{self._dec}f}")
        span = self._max - self._min
        self._pct = max(0.0, min(100.0, (value - self._min) / span * 100)) if span else 0.0
        self._redraw()


# ── Ventana principal ─────────────────────────────────────────────────────────

class Dashboard:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ESP32 MQTT Dashboard")
        self.root.configure(bg=BG)
        self.root.geometry("980x520")
        self.root.minsize(760, 460)

        self._build_header()
        self._build_cards()
        self._build_led_section()
        self._build_footer()

        # Conectar MQTT (hilo daemon, no bloquea la ventana)
        self.mqtt = MQTTClient(
            on_message_cb=self._on_message,
            on_connect_cb=self._on_connect,
            on_disconnect_cb=lambda: self.root.after(0, self._set_broker, False),
        )
        self.mqtt.start()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Construcción de la UI ─────────────────────────────────────────────────

    def _build_header(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=24, pady=(20, 0))

        # Título: "ESP32 MQTT Dashboard"
        tk.Label(
            header, text="ESP32 ", bg=BG, fg=BLUE,
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left")
        tk.Label(
            header, text="MQTT Dashboard", bg=BG, fg=TEXT,
            font=("Segoe UI", 18),
        ).pack(side="left")

        # Badge de estado del broker (derecha)
        badge = tk.Frame(
            header, bg=CARD_BG,
            highlightbackground=BORDER, highlightthickness=1,
        )
        badge.pack(side="right")
        inner = tk.Frame(badge, bg=CARD_BG, padx=14, pady=6)
        inner.pack()

        self._dot = tk.Canvas(inner, width=10, height=10, bg=CARD_BG, highlightthickness=0)
        self._dot.pack(side="left", padx=(0, 8))
        self._dot.create_oval(1, 1, 9, 9, fill=RED_C, outline="", tags="d")

        self._broker_lbl = tk.Label(
            inner, text="Desconectado", bg=CARD_BG, fg=TEXT,
            font=("Segoe UI", 9),
        )
        self._broker_lbl.pack(side="left")

        # Línea separadora
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(14, 14))

    def _build_cards(self):
        grid = tk.Frame(self.root, bg=BG)
        grid.pack(fill="x", padx=24, pady=(0, 16))

        specs = [
            ("Potenciómetro 1",  "Voltios (V)",          BLUE,   0.0, 3.3,   2, "pot1"),
            ("Potenciómetro 2",  "Voltios (V)",          PURPLE, 0.0, 3.3,   2, "pot2"),
            ("Potenciómetro 3",  "Voltios (V)",          ORANGE, 0.0, 3.3,   2, "pot3"),
            ("Temperatura LM35", "Grados Celsius (°C)",  RED_C,  0.0, 100.0, 1, "lm35"),
        ]

        self._cards: dict[str, SensorCard] = {}
        for col_idx, (lbl, unit, color, mn, mx, dec, key) in enumerate(specs):
            grid.columnconfigure(col_idx, weight=1)
            card = SensorCard(grid, lbl, unit, color, mn, mx, dec)
            card.grid(
                row=0, column=col_idx, sticky="nsew",
                padx=(0 if col_idx == 0 else 10, 0),
            )
            self._cards[key] = card

    def _build_led_section(self):
        sec = tk.Frame(
            self.root, bg=CARD_BG,
            highlightbackground=BORDER, highlightthickness=1,
        )
        sec.pack(fill="x", padx=24, pady=(0, 16))

        inner = tk.Frame(sec, bg=CARD_BG, padx=28, pady=20)
        inner.pack(fill="x")

        # Círculo LED
        self._led_cv = tk.Canvas(inner, width=60, height=60, bg=CARD_BG, highlightthickness=0)
        self._led_cv.pack(side="left")
        self._led_cv.create_oval(4, 4, 56, 56, fill=LED_OFF, outline=BORDER, width=3, tags="led")

        # Información de estado
        info = tk.Frame(inner, bg=CARD_BG, padx=20)
        info.pack(side="left", fill="x", expand=True)

        tk.Label(
            info, text="Control LED", bg=CARD_BG, fg=TEXT,
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")

        self._led_badge = tk.Label(
            info, text="DESCONOCIDO", bg=BAR_BG, fg=DIM,
            font=("Segoe UI", 8, "bold"), padx=12, pady=3,
        )
        self._led_badge.pack(anchor="w", pady=(6, 0))

        # Botones Encender / Apagar
        btns = tk.Frame(inner, bg=CARD_BG)
        btns.pack(side="right")

        tk.Button(
            btns, text="Encender", bg=GREEN, fg=BG,
            font=("Segoe UI", 10, "bold"), padx=20, pady=8,
            relief="flat", cursor="hand2",
            activebackground=GREEN, activeforeground=BG,
            command=lambda: self.mqtt.publish("led/uno", "ON"),
        ).pack(side="left", padx=(0, 12))

        tk.Button(
            btns, text="Apagar", bg=RED_C, fg="white",
            font=("Segoe UI", 10, "bold"), padx=20, pady=8,
            relief="flat", cursor="hand2",
            activebackground=RED_C, activeforeground="white",
            command=lambda: self.mqtt.publish("led/uno", "OFF"),
        ).pack(side="left")

    def _build_footer(self):
        foot = tk.Frame(self.root, bg=BG)
        foot.pack(fill="x", padx=24, pady=(0, 16))

        self._ts_lbl = tk.Label(
            foot, text="—", bg=BG, fg=DIMMER,
            font=("Segoe UI", 8, "italic"),
        )
        self._ts_lbl.pack(side="right")

        tk.Label(
            foot, text="Última actualización: ", bg=BG, fg=DIMMER,
            font=("Segoe UI", 8),
        ).pack(side="right")

    # ── Callbacks MQTT (hilo secundario → programa en main thread) ────────────

    def _on_connect(self, connected: bool):
        self.root.after(0, self._set_broker, connected)

    def _on_message(self, topic: str, payload: str):
        self.root.after(0, self._dispatch, topic, payload)

    # ── Actualizaciones de la UI (siempre en el main thread) ─────────────────

    def _set_broker(self, connected: bool):
        if connected:
            self._dot.itemconfig("d", fill=GREEN)
            self._broker_lbl.config(text="Broker conectado")
        else:
            self._dot.itemconfig("d", fill=RED_C)
            self._broker_lbl.config(text="Desconectado")

    def _dispatch(self, topic: str, payload: str):
        try:
            val = float(payload)
        except ValueError:
            val = None

        topic_map = {
            "pot/uno":  "pot1",
            "pot/dos":  "pot2",
            "pot/tres": "pot3",
            "LM35/uno": "lm35",
        }

        if topic in topic_map and val is not None:
            self._cards[topic_map[topic]].set_value(val)
        elif topic == "led/estado":
            self._update_led(payload.strip().upper())

        self._ts_lbl.config(text=datetime.now().strftime("%H:%M:%S"))

    def _update_led(self, state: str):
        if state == "ON":
            self._led_cv.itemconfig("led", fill=LED_ON, outline="#e9b50b")
            self._led_badge.config(text="ON", bg="#332d00", fg=LED_ON)
        else:
            self._led_cv.itemconfig("led", fill=LED_OFF, outline=BORDER)
            self._led_badge.config(text="OFF", bg=BAR_BG, fg=DIM)

    def _on_close(self):
        self.mqtt.stop()
        self.root.destroy()


# ── Punto de entrada ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    Dashboard(root)
    root.mainloop()
