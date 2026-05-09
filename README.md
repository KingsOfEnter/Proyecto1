StrangerTEC Morse Translator
Documentación del Proyecto
1. Introducción
El proyecto StrangerTEC Morse Translator consiste en un prototipo inspirado en la serie Stranger Things, que permite la comunicación en código Morse entre dos jugadores mediante una maqueta con LEDs y buzzer controlados por una Raspberry Pi Pico W, y una aplicación en la PC desarrollada en Python.
2. Antecedentes
El proyecto se inspira en escenas de Stranger Things donde se utiliza código Morse y luces para comunicarse. Se busca recrear esa experiencia en un entorno académico, integrando electrónica, programación embebida y desarrollo de interfaces gráficas.
3. Descripción del sistema
•	Maqueta:
o	16 LEDs controlados por dos registros 74HC164.
o	Buzzer pasivo para retroalimentación sonora.
o	Botón pulsador para ingresar puntos y rayas.
o	Switch de modo para seleccionar Local o Versus.
•	Raspberry Pi Pico W:
o	Firmware en MicroPython (thonnypy.py).
o	Decodificación de Morse y comunicación con la PC.
•	PC:
o	Aplicación en Python/Tkinter (pcpy.py).
o	Interfaz gráfica para frases, configuración de unidad de tiempo, puntajes y resultados.
4. Documentación del código
4.1 Archivo thonnypy.py (MicroPython)
•	Funciones principales:
o	shift_out_16(value): envía 16 bits a los registros 74HC165.
o	set_led_index(idx): enciende un LED específico.
o	char_to_led_index(ch): mapea un carácter a un LED.
o	Decodificación Morse: mide duración de pulsación, distingue punto/raya, detecta pausas para caracteres y palabras.
o	Presentación de frases: por LEDs o buzzer según comando recibido.
o	Comunicación: envío/recepción de mensajes JSON.
•	Mapeo de pines (por defecto):
o	DATA → GP2
o	CLK → GP3
o	BUTTON → GP15
o	BUZZER → GP16
o	MODE_SWITCH → GP14
•	Mensajes JSON:
o	Comandos PC→Pico: PHRASE, PHRASE_BUZZ, SET_UNIT.
o	Eventos Pico→PC: READY, CHAR, WORD_GAP, MESSAGE.
4.2 Archivo pcpy.py (Python/Tkinter)
•	Funciones principales:
o	Interfaz gráfica con lista de frases (máx. 10).
o	Selección de unidad A/B.
o	Conexión serie con la Pico.
o	Envío de frases y recepción de eventos JSON.
o	Cálculo de puntaje básico por coincidencia de caracteres.
•	Dependencias:
o	Python 3.8+
o	Tkinter (incluido en Python)
o	pyserial (pip install pyserial)
5. Análisis de resultados
•	El sistema no logra transmitir y recibir mensajes en Morse con decodificación en la Pico y visualización en la PC.
•	La interfaz gráfica permite gestionar frases y visualizar puntajes.
6. Conclusiones
•	El prototipo no pudo cumplirr con los objetivos básicos del proyecto.
•	La modularidad del código facilita futuras extensiones.
7. Recomendaciones
•	Ajustar parámetros de tiempo (DOT_DASH_THRESHOLD, UNIT_A/B) según pruebas con usuarios.
•	Documentar el mapeo físico exacto de LEDs en la maqueta.
•	Implementar modo Versus por WiFi para obtener puntos extra.
•	Cambiar los repgistros po 74HC164r.
8. Evaluación (según enunciado)
•	Funcionalidades del prototipo: 70%.
•	Documentación: 30%.
•	Puntos extra: 10% (modo Versus WiFi).
9. Archivos del repositorio
•	thonnypy.py — firmware MicroPython.
•	pcpy.py — aplicación PC.
•	DOCUMENTACION_PROYECTO.md — este documento.
10. Fuentes consultadas
•	Documentación oficial Raspberry Pi Pico / MicroPython.
•	morsecw.com (morsecw.com in Bing)
•	micropython.org

