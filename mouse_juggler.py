#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mouse Juggler - Mouse movement automation with natural patterns.

This script provides a tool to automatically move the mouse with movement
patterns that simulate human behavior using Bezier curves.
Includes both a GUI mode (Tkinter) and a console mode.

Author: Arturo
License: MIT
"""

# Version information (used by setup.py and release scripts)
VERSION = "1.0.0"

import logging
import random
import sys
import threading
import time
import math
from itertools import islice

import numpy as np
import pyautogui as pag

# --------------------------------- utilities ---------------------------------
def pairwise(iterable):
    "equivalent to itertools.pairwise (Python 3.10+) for 3.8+"
    it = iter(iterable)
    prev = next(it, None)
    for item in it:
        yield prev, item
        prev = item

def ease_in_out_cubic(t):
    """Easing function para movimiento natural aceleración/desaceleración"""
    if t < 0.5:
        return 4 * t * t * t
    else:
        p = 2 * t - 2
        return 0.5 * p * p * p + 1

def ease_in_out_quartic(t):
    """Easing function con más suavidad en los extremos"""
    if t < 0.5:
        return 8 * t * t * t * t
    else:
        t = t - 1
        return -8 * t * t * t * t + 1

def cubic_bezier_curve(p0, p1, p2, p3, num_points):
    """Curva de Bezier cúbica para movimiento más natural"""
    t = np.linspace(0, 1, num_points)
    
    # Aplicar easing para distribución de tiempo no lineal (más natural)
    t_eased = np.array([ease_in_out_quartic(float(x)) for x in t])
    
    # Preparar arrays para broadcasting
    t_eased_reshaped = t_eased.reshape(-1, 1)
    
    # Fórmula para curva de Bezier cúbica
    curve = ((1-t_eased_reshaped)**3 * p0 + 
             3 * (1-t_eased_reshaped)**2 * t_eased_reshaped * p1 + 
             3 * (1-t_eased_reshaped) * t_eased_reshaped**2 * p2 + 
             t_eased_reshaped**3 * p3)
    
    # Añadir pequeña variación aleatoria para simular imprecisión humana
    human_noise = np.random.normal(0, 0.5, curve.shape)
    curve = curve + human_noise
    
    return curve.astype(int)

def natural_trajectory(origin, destination, steps):
    """Genera una trayectoria natural entre dos puntos usando curvas de Bezier cúbicas"""
    origin = np.array(origin)
    destination = np.array(destination)
    vec = destination - origin
    dist = np.linalg.norm(vec)
    
    if dist < 1:
        return [origin]
    
    # Vector perpendicular para controlar la curvatura
    perp = np.array([-vec[1], vec[0]]) / dist
    
    # Crear puntos de control con más naturalidad
    # El punto de control 1 está más cerca del origen
    curvature1 = random.uniform(-dist/3, dist/3)
    control1 = origin + vec * 0.3 + perp * curvature1
    
    # El punto de control 2 está más cerca del destino
    curvature2 = random.uniform(-dist/3, dist/3)
    control2 = origin + vec * 0.7 + perp * curvature2
    
    # Generar la trayectoria con la curva de Bezier cúbica
    return cubic_bezier_curve(origin, control1, control2, destination, steps)

def human_move(origin, destination, speed_range, steps_range, stop_evt=None):
    """Mueve el ratón de una manera muy orgánica entre dos puntos"""
    # Aumentar el número de pasos para movimiento más suave
    min_steps = steps_range[0]
    max_steps = steps_range[1]
    
    # Usar más pasos para distancias más largas
    distance = np.linalg.norm(np.array(destination) - np.array(origin))
    points_factor = min(1.0, distance / 500)  # Factor basado en distancia
    
    # Calcular número adaptativo de puntos
    adaptive_steps = int(min_steps + (max_steps - min_steps) * points_factor) + random.randint(5, 15)
    
    # Generar trayectoria natural
    points = natural_trajectory(origin, destination, adaptive_steps)
    
    # Calcular la distancia total del camino
    # Asegurarnos de que points es una lista de puntos individuales, no un array multidimensional
    point_list = []
    for point in points:
        # Manejar tanto arrays de NumPy como puntos individuales
        try:
            # Si es un elemento array-like con valores accesibles por índice
            x, y = float(point[0]), float(point[1])
            point_list.append(np.array([x, y]))
        except (TypeError, IndexError):
            # Si ya es un punto individual o tiene otra estructura
            point_list.append(point)
    
    # Ahora calcular distancias con los puntos normalizados
    total_distance = 0
    for a, b in pairwise(point_list):
        try:
            total_distance += np.linalg.norm(np.array(b) - np.array(a))
        except (ValueError, TypeError):
            # En caso de error, simplemente continuamos
            continue
    
    # Velocidad pixels/segundo con pequeña variación
    speed = random.uniform(*speed_range) * random.uniform(0.9, 1.1)
    
    # Tiempo total estimado (con protección contra división por cero)
    total_time = total_distance / max(speed, 0.001)
    
    # Crear tiempos no lineales entre puntos (más naturales)
    progress = np.linspace(0, 1, len(point_list))
    eased_progress = np.array([ease_in_out_cubic(float(t)) for t in progress])
    
    # Normalizar para que sume el tiempo total
    if len(eased_progress) > 1:
        time_diffs = np.diff(eased_progress)
        if np.sum(time_diffs) > 0:
            time_diffs = time_diffs / np.sum(time_diffs) * total_time
        else:
            time_diffs = np.ones_like(time_diffs) * total_time / len(time_diffs)
    else:
        time_diffs = [0]  # No hay diferencias si solo hay un punto
    
    # Ejecutar el movimiento
    for i, point in enumerate(point_list[:-1]):
        # Verificar señal de parada
        if stop_evt and stop_evt.is_set():
            break
        
        try:
            # Extraer coordenadas asegurándonos de que sean escalares
            x = int(float(point[0]))
            y = int(float(point[1]))
            
            # Mover a la posición actual
            pag.moveTo(x, y)
        except (TypeError, IndexError, ValueError) as e:
            logging.warning(f"Error moviendo el cursor: {e}")
            continue
        
        # Calcular pausa hasta el siguiente punto
        if i < len(time_diffs):
            pause = time_diffs[i]
        else:
            pause = 0.01  # Tiempo por defecto si hay algún problema
        
        # Para pausas largas, dividir en segmentos para permitir mejor cancelación
        if pause > 0.05 and stop_evt:
            segments = int(pause / 0.05)
            for _ in range(segments):
                if stop_evt and stop_evt.is_set():
                    return
                time.sleep(0.05)
            # Resto del tiempo
            remaining = pause % 0.05
            if remaining > 0:
                time.sleep(remaining)
        else:
            time.sleep(max(0.001, pause))  # Evitar pausas negativas
    
    # Mover al punto final exacto
    if not (stop_evt and stop_evt.is_set()) and len(point_list) > 0:
        try:
            dest_x = int(float(destination[0]))
            dest_y = int(float(destination[1]))
            pag.moveTo(dest_x, dest_y)
        except (TypeError, IndexError, ValueError) as e:
            logging.warning(f"Error moviendo al punto final: {e}")

# --------------------------- default configuration -------------------------
CFG_DEFAULT = dict(
    dx=(80, 300),
    dy=(80, 300),
    pause=(1.5, 7),
    steps=(60, 150),  # Aumentado para movimientos más suaves
    vel=(200, 800),
)

def movement_loop(stop_evt, cfg):
    """Thread that moves the mouse until stop_evt is active."""
    logging.info("Movement loop started.")
    while not stop_evt.is_set():
        x0, y0 = pag.position()
        
        # Crear movimientos más naturales con probabilidad de distancias variadas
        if random.random() < 0.7:
            # Movimientos normales
            dx = random.randint(*cfg['dx']) * random.choice((-1, 1))
            dy = random.randint(*cfg['dy']) * random.choice((-1, 1))
        else:
            # Ocasionalmente movimientos más pequeños o más grandes
            factor = random.choice([0.3, 2.0])
            dx = int(random.randint(*cfg['dx']) * factor) * random.choice((-1, 1))
            dy = int(random.randint(*cfg['dy']) * factor) * random.choice((-1, 1))
        
        # Asegurar que el destino esté en pantalla
        w, h = pag.size()
        x1 = max(1, min(w - 2, x0 + dx))
        y1 = max(1, min(h - 2, y0 + dy))
        
        # Mover el ratón
        human_move((x0, y0), (x1, y1), cfg['vel'], cfg['steps'], stop_evt)
        
        # Verificar si debemos terminar antes de la pausa
        if stop_evt.is_set():
            break
            
        # Pausas variables entre movimientos
        total_pause = random.uniform(*cfg['pause'])
        
        # Ocasionalmente añadir micro-movimientos durante las pausas
        if random.random() < 0.3 and total_pause > 2:
            # Dividir el tiempo de pausa
            first_part = total_pause * random.uniform(0.3, 0.7)
            
            for _ in range(int(first_part)):
                if stop_evt.is_set():
                    break
                time.sleep(1)
                
            if not stop_evt.is_set():
                time.sleep(first_part % 1)
                
            # Hacer un micro-movimiento
            if not stop_evt.is_set():
                curr_x, curr_y = pag.position()
                micro_dx = random.randint(1, 10) * random.choice((-1, 1))
                micro_dy = random.randint(1, 10) * random.choice((-1, 1))
                micro_x = max(1, min(w - 2, curr_x + micro_dx))
                micro_y = max(1, min(h - 2, curr_y + micro_dy))
                
                # Movimiento pequeño con menos pasos y más lento
                micro_steps = (10, 25)
                micro_vel = (50, 150)
                human_move((curr_x, curr_y), (micro_x, micro_y), 
                          micro_vel, micro_steps, stop_evt)
                
            # Resto del tiempo de pausa
            remaining = total_pause - first_part
            for _ in range(int(remaining)):
                if stop_evt.is_set():
                    break
                time.sleep(1)
                
            if not stop_evt.is_set():
                time.sleep(remaining % 1)
        else:
            # Pausa normal, dividida para mejor respuesta
            for _ in range(int(total_pause)):
                if stop_evt.is_set():
                    break
                time.sleep(1)
                
            if not stop_evt.is_set():
                time.sleep(total_pause % 1)
    
    logging.info("Movement loop stopped.")

# ----------------------------- keyboard listener -----------------------------
try:
    from pynput import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    logging.warning("pynput not found; global keyboard stop disabled.")

def start_keyboard_listener(stop_evt, on_first_key=None):
    if not KEYBOARD_AVAILABLE:
        return None

    def _on_press(key):
        if not stop_evt.is_set():
            stop_evt.set()
            logging.info("Stop requested by key press: %s", key)
            if on_first_key and _app_instance:
                # Schedule safe call in UI main thread
                _app_instance.after(100, on_first_key)
            elif on_first_key:
                on_first_key()
        # stop on first event
        return False

    listener = keyboard.Listener(on_press=_on_press, suppress=False)
    listener.start()
    return listener

# -------------------------------- GUI (Tkinter) -------------------------------
GUI_AVAILABLE = False
GUI_ERROR = None
_app_instance = None      # To update UI from other threads

try:
    import tkinter as tk
    from tkinter import ttk
    GUI_AVAILABLE = True
except Exception as e:
    GUI_ERROR = e
    GUI_AVAILABLE = False
    logging.warning("GUI not available (%s). Console mode will be used.", e)

class MouseJugglerApp(tk.Tk):
    """Blue interface with controls and dynamic status."""
    COLOR_BG = "#cbe2ff"
    COLOR_FG = "#043b74"
    COLOR_ACCENT = "#0078d7"
    COLOR_START = "#4CAF50"    # Verde
    COLOR_STOP = "#FF5252"     # Rojo
    
    def __init__(self):
        super().__init__()
        global _app_instance
        _app_instance = self

        self.title("Mouse Juggler")
        self.resizable(False, False)
        self.configure(bg=self.COLOR_BG)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # ttk styles
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=self.COLOR_BG, foreground=self.COLOR_FG)
        style.configure("TButton", font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("Stop.TButton", background="#FF5252", foreground="white")
        style.configure("Settings.TButton", font=("Segoe UI", 10), padding=2)
        style.configure("TMenubutton", font=("Segoe UI", 10))

        # Tk variables for parameters
        self.v_dx_min   = tk.IntVar(value=80)
        self.v_dx_max   = tk.IntVar(value=300)
        self.v_dy_min   = tk.IntVar(value=80)
        self.v_dy_max   = tk.IntVar(value=300)
        self.v_pause_min = tk.DoubleVar(value=1.5)
        self.v_pause_max = tk.DoubleVar(value=7)
        self.v_steps_min = tk.IntVar(value=60)
        self.v_steps_max = tk.IntVar(value=150)
        self.v_vel_min   = tk.DoubleVar(value=200)
        self.v_vel_max   = tk.DoubleVar(value=800)

        # Status (to show stops)
        self.status = tk.StringVar(value="Listo para iniciar")
        
        self._create_widgets()

        # Thread and stop signal
        self.stop_event = threading.Event()
        self.worker = None
        self.keyboard_listener = None

    def _create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 1. Título
        ttk.Label(main_frame, text="Mouse Juggler", 
                 font=("Segoe UI", 16, "bold")).grid(row=0, column=0, 
                                                    columnspan=2, pady=(0, 20))
        
        # 2. Botón redondo de inicio (centrado)
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=20)
        
        # Crear botón redondo usando Canvas
        self.canvas = tk.Canvas(btn_frame, width=140, height=140, 
                            bg=self.COLOR_BG, highlightthickness=0)
        self.canvas.pack()
        
        # Círculo y texto
        self.btn_circle = self.canvas.create_oval(10, 10, 130, 130, 
                                             fill=self.COLOR_START, outline="")
        self.btn_text = self.canvas.create_text(70, 70, text="Iniciar", 
                                           fill="white", font=("Segoe UI", 16, "bold"))
        
        # Asignar eventos al círculo y texto
        self.canvas.tag_bind(self.btn_circle, "<Button-1>", lambda e: self.start())
        self.canvas.tag_bind(self.btn_text, "<Button-1>", lambda e: self.start())
        
        # Fila inferior
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        bottom_frame.columnconfigure(0, weight=1)  # Para alinear a la izquierda
        bottom_frame.columnconfigure(1, weight=1)  # Para alinear a la derecha
        
        # 3. Estado (izquierda)
        ttk.Label(bottom_frame, textvariable=self.status,
                 font=("Segoe UI", 10, "italic")).grid(row=0, column=0, sticky="w")
        
        # 4. Menú desplegable (centro)
        self.options_menu = tk.StringVar(value="Opciones")
        options_btn = ttk.Menubutton(bottom_frame, textvariable=self.options_menu, 
                                    style="TMenubutton")
        options_btn.grid(row=0, column=1, sticky="e", padx=(0, 10))
        
        # Menú desplegable
        self.options_dropdown = tk.Menu(options_btn, tearoff=0)
        options_btn["menu"] = self.options_dropdown
        
        # Crear panel de configuración
        self._create_settings_panel()
        
        # 5. Botón de detener (esquina inferior derecha)
        self.stop_btn = ttk.Button(bottom_frame, text="Detener", command=self.stop,
                               style="Stop.TButton")
        self.stop_btn.grid(row=0, column=2, sticky="e")

    def _create_settings_panel(self):
        """Crear el menú desplegable con las opciones de configuración"""
        # Limpiar menú actual
        self.options_dropdown.delete(0, tk.END)
        
        # Agregar un comando para mostrar la ventana de configuración
        self.options_dropdown.add_command(label="Configuración avanzada...", 
                                        command=self.show_config_window)
        
        self.options_dropdown.add_separator()
        
        # Opciones comunes para velocidad
        velocidades = [
            ("Lenta", 100, 300), 
            ("Normal", 200, 800), 
            ("Rápida", 500, 1200)
        ]
        
        for nombre, vel_min, vel_max in velocidades:
            self.options_dropdown.add_command(
                label=f"Velocidad: {nombre}", 
                command=lambda min_v=vel_min, max_v=vel_max: self.set_speed(min_v, max_v)
            )
        
        self.options_dropdown.add_separator()
        
        # Opciones comunes para pausas
        pausas = [
            ("Cortas", 0.5, 2), 
            ("Medianas", 1.5, 7), 
            ("Largas", 5, 15)
        ]
        
        for nombre, pausa_min, pausa_max in pausas:
            self.options_dropdown.add_command(
                label=f"Pausas: {nombre}", 
                command=lambda min_p=pausa_min, max_p=pausa_max: self.set_pause(min_p, max_p)
            )
        
        self.options_dropdown.add_separator()
        
        # Opciones de naturalidad del movimiento
        naturalidad = [
            ("Estándar", 60, 150),  # Predeterminado
            ("Alta", 100, 200),     # Más suave
            ("Extrema", 150, 300)   # Ultra suave
        ]
        
        for nombre, steps_min, steps_max in naturalidad:
            self.options_dropdown.add_command(
                label=f"Organicidad: {nombre}", 
                command=lambda min_s=steps_min, max_s=steps_max: self.set_organicity(min_s, max_s)
            )
            
    def set_speed(self, min_vel, max_vel):
        """Configura rápidamente la velocidad"""
        self.v_vel_min.set(min_vel)
        self.v_vel_max.set(max_vel)
        self.status.set(f"Velocidad actualizada: {min_vel}-{max_vel} px/s")
        
    def set_pause(self, min_pause, max_pause):
        """Configura rápidamente las pausas"""
        self.v_pause_min.set(min_pause)
        self.v_pause_max.set(max_pause)
        self.status.set(f"Pausas actualizadas: {min_pause}-{max_pause}s")
        
    def set_organicity(self, min_steps, max_steps):
        """Configura la organicidad del movimiento"""
        self.v_steps_min.set(min_steps)
        self.v_steps_max.set(max_steps)
        self.status.set(f"Organicidad actualizada: {min_steps}-{max_steps} pasos")
    
    def show_config_window(self):
        """Muestra ventana emergente con todas las opciones de configuración"""
        config_window = tk.Toplevel(self)
        config_window.title("Configuración avanzada")
        config_window.configure(bg=self.COLOR_BG)
        config_window.resizable(False, False)
        config_window.grab_set()  # Modal window
        
        frame = ttk.Frame(config_window, padding=15)
        frame.grid(row=0, column=0)
        
        # ---- Función auxiliar para crear spinboxes ----
        def spin(frame, row, txt, var, mn, mx, inc):
            ttk.Label(frame, text=txt).grid(row=row, column=0, sticky="w", pady=2)
            sb = ttk.Spinbox(frame, textvariable=var, from_=mn, to=mx,
                             increment=inc, width=8, justify="right")
            sb.grid(row=row, column=1, padx=5, pady=2)
        
        # Parámetros de desplazamiento
        ttk.Label(frame, text="Configuración de movimiento", 
                 font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        spin(frame, 1, "ΔX mínimo (px)", self.v_dx_min, 1, 800, 10)
        spin(frame, 2, "ΔX máximo (px)", self.v_dx_max, 1, 1600, 10)
        spin(frame, 3, "ΔY mínimo (px)", self.v_dy_min, 1, 800, 10)
        spin(frame, 4, "ΔY máximo (px)", self.v_dy_max, 1, 1600, 10)
        
        ttk.Separator(frame, orient="horizontal").grid(row=5, column=0, columnspan=2, 
                                                     sticky="ew", pady=10)
        
        # Parámetros de velocidad y pausa
        ttk.Label(frame, text="Velocidad y pausas", 
                 font=("Segoe UI", 11, "bold")).grid(row=6, column=0, columnspan=2, pady=(0, 10))
        
        spin(frame, 7, "Velocidad mínima (px/s)", self.v_vel_min, 10, 3000, 50)
        spin(frame, 8, "Velocidad máxima (px/s)", self.v_vel_max, 20, 4000, 50)
        spin(frame, 9, "Pausa mínima (s)", self.v_pause_min, .1, 20, .1)
        spin(frame, 10, "Pausa máxima (s)", self.v_pause_max, .1, 60, .1)
        
        ttk.Separator(frame, orient="horizontal").grid(row=11, column=0, columnspan=2, 
                                                     sticky="ew", pady=10)
        
        # Parámetros de la curva - Actualizado para permitir más pasos
        ttk.Label(frame, text="Naturalidad del movimiento", 
                 font=("Segoe UI", 11, "bold")).grid(row=12, column=0, columnspan=2, pady=(0, 10))
        
        spin(frame, 13, "Pasos mínimos", self.v_steps_min, 5, 400, 10)
        spin(frame, 14, "Pasos máximos", self.v_steps_max, 5, 500, 10)
        
        # Botón para cerrar
        ttk.Button(frame, text="Aceptar", command=config_window.destroy).grid(
            row=15, column=0, columnspan=2, pady=(15, 0))

    # ---------------- movement control ----------------
    def _current_cfg(self):
        return dict(
            dx=(self.v_dx_min.get(), self.v_dx_max.get()),
            dy=(self.v_dy_min.get(), self.v_dy_max.get()),
            pause=(self.v_pause_min.get(), self.v_pause_max.get()),
            steps=(self.v_steps_min.get(), self.v_steps_max.get()),
            vel=(self.v_vel_min.get(), self.v_vel_max.get()),
        )

    def _update_status(self, txt):
        self.status.set(txt)

    def start(self):
        if self.worker and self.worker.is_alive():
            return
        self.stop_event.clear()
        
        # Create a new keyboard listener each time we start
        self.keyboard_listener = start_keyboard_listener(
            self.stop_event,
            on_first_key=self.key_stop_handler
        )
        
        self.worker = threading.Thread(target=movement_loop,
                                       args=(self.stop_event, self._current_cfg()),
                                       daemon=True)
        self.worker.start()
        self._update_status("En movimiento...")
        
        # Cambiar apariencia del botón de inicio
        self.canvas.itemconfig(self.btn_circle, fill=self.COLOR_STOP)
        self.canvas.itemconfig(self.btn_text, text="Activo")

    def stop(self):
        self.stop_event.set()
        self._update_status("Detenido")
        
        # Restaurar apariencia del botón de inicio
        self.canvas.itemconfig(self.btn_circle, fill=self.COLOR_START)
        self.canvas.itemconfig(self.btn_text, text="Iniciar")

    def on_close(self):
        self.stop()
        self.destroy()

    def key_stop_handler(self):
        self._update_status("Detenido por teclado")
        
        # Restaurar apariencia del botón de inicio
        self.canvas.itemconfig(self.btn_circle, fill=self.COLOR_START)
        self.canvas.itemconfig(self.btn_text, text="Iniciar")

# ------------------------------ console mode ----------------------------------
def run_console():
    """Run the movement without GUI."""
    logging.info("Running in console mode.")
    stop_evt = threading.Event()
    start_keyboard_listener(stop_evt,
                           on_first_key=lambda: print("Stopped by key."))
    try:
        movement_loop(stop_evt, CFG_DEFAULT)
    except KeyboardInterrupt:
        stop_evt.set()
    print("End.")

# ---------------------------------- main --------------------------------------
def main():
    logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s",
                        level=logging.INFO)

    if GUI_AVAILABLE:
        try:
            app = MouseJugglerApp()
            app.mainloop()
        except Exception as e:
            logging.exception("GUI failed (%s). Switching to console mode.", e)
            run_console()
    else:
        logging.info("GUI not available (%s).", GUI_ERROR or "no Tk")
        run_console()

if __name__ == "__main__":
    main()