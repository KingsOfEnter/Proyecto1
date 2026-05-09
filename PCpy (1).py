from machine import Pin, PWM
import time
import ujson as json
import sys
import uselect


DATA_PIN = 16   
CLK_PIN  = 17   
BUTTON_PIN = 0
BUZZER_PIN = 15
MODE_SWITCH_PIN = 14  


UNIT_A = 0.2  
UNIT_B = 0.3
DOT_DASH_THRESHOLD = 0.4  
INTER_SYMBOL_GAP = UNIT_A
INTER_CHAR_GAP = 3 * UNIT_A
INTER_WORD_GAP = 7 * UNIT_A


MORSE_TO_CHAR = {
    ".-":"A","-...":"B","-.-.":"C","-..":"D",".":"E","..-.":"F","--.":"G","....":"H",
    "..":"I",".---":"J","-.-":"K",".-..":"L","--":"M","-.":"N","---":"O",".--.":"P",
    "--.-":"Q",".-.":"R","...":"S","-":"T","..-":"U","...-":"V",".--":"W","-..-":"X",
    "-.--":"Y","--..":"Z",
    "-----":"0",".----":"1","..---":"2","...--":"3","....-":"4",".....":"5","-....":"6","--...":"7","---..":"8","----.":"9",
    ".-.-.":"+","-....-":"-","-..-.":"/"
}


LED_MAP = [
    'A','C','E','G','I','K','M','O',   
    'Q','S','U','W','Y','B','D','F'    
]



data = Pin(DATA_PIN, Pin.OUT)
clk  = Pin(CLK_PIN, Pin.OUT)
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
mode_switch = Pin(MODE_SWITCH_PIN, Pin.IN, Pin.PULL_DOWN)
buzzer = PWM(Pin(BUZZER_PIN))
buzzer.freq(2000)
buzzer.duty_u16(0)


def shift_out_16(value): #prende los leds
    
    for i in range(15, -1, -1):
        bit = (value >> i) & 1
        data.value(bit)
        
        clk.value(1)
        time.sleep_us(50)
        clk.value(0)
        time.sleep_us(50)


def set_led_index(idx): #prende un led en especifico
    if idx is None:
        shift_out_16(0)
        return
    if idx < 0 or idx > 15:
        shift_out_16(0)
        return
    mask = 1 << idx
    shift_out_16(mask)


def char_to_led_index(ch): #busca en el led map y prende el led que le corresponde
    ch = ch.upper()
    for i, label in enumerate(LED_MAP):
        if label == ch:
            return i
    return None


current_symbol = ""   
current_message = ""  
last_event_time = time.ticks_ms()
listening = True


def send_json(obj): #convierte los daos de la pico y los manda a un txt json y lo imprime
    try:
        s = json.dumps(obj)
        sys.stdout.write(s + "\n")
    except Exception as e:
        pass


def present_phrase_via_leds(text, unit=UNIT_A): #muestra el contenido en los leds
    for ch in text:
        idx = char_to_led_index(ch)
        set_led_index(idx)
        
        time.sleep(3 * unit)
        set_led_index(None)
        time.sleep(unit)  


def present_phrase_via_buzzer_morse(text, unit=UNIT_A): #muestra el contenido a través de morse y sonido por el buzzer
    for ch in text:
        if ch == ' ':
            time.sleep(7 * unit)
            continue
        morse = None
        
        for k,v in MORSE_TO_CHAR.items():
            if v == ch:
                morse = k
                break
        if morse is None:
            
            morse = next((k for k,v in MORSE_TO_CHAR.items() if v==ch), None)
        if morse is None:
            time.sleep(3 * unit)
            continue
        for symbol in morse:
            buzzer.duty_u16(20000)
            if symbol == '.':
                time.sleep(unit)
            else:
                time.sleep(3 * unit)
            buzzer.duty_u16(0)
            time.sleep(unit)  
        time.sleep(2 * unit)  


def main_loop(): #el corazón del programa, el que va checando en bucle infinito si la pc hace algo, el tiempo presionado del botón y cuando enviar la palabra final a la computadora
    global current_symbol, current_message, last_event_time
    unit = UNIT_A
    symbol_start = None
    last_change = time.ticks_ms()
    while True:
       
        try:
            if sys.stdin in select_readable():
                line = sys.stdin.readline()
                if line:
                    try:
                        cmd = json.loads(line)
                        if cmd.get("cmd") == "PHRASE":
                            text = cmd.get("text","")
                            
                            present_phrase_via_leds(text, unit)
                        elif cmd.get("cmd") == "PHRASE_BUZZ":
                            present_phrase_via_buzzer_morse(cmd.get("text",""), unit)
                        elif cmd.get("cmd") == "SET_UNIT":
                            if cmd.get("unit") == "A":
                                unit = UNIT_A
                            else:
                                unit = UNIT_B
                    except Exception:
                        pass
        except Exception:
            
            pass

        btn = button.value()
        now = time.ticks_ms()
        
        if btn:
            if symbol_start is None:
                symbol_start = now
                buzzer.duty_u16(20000)
            
        else:
            if symbol_start is not None:
                
                duration = (now - symbol_start) / 1000.0
                buzzer.duty_u16(0)
                if duration < DOT_DASH_THRESHOLD:
                    current_symbol += "."
                else:
                    current_symbol += "-"
                
                last_change = now
                symbol_start = None
                
                time.sleep(0.05)

        
        if current_symbol != "":
            gap = (now - last_change) / 1000.0
            if gap >= INTER_CHAR_GAP:
                
                ch = MORSE_TO_CHAR.get(current_symbol, '?')
                current_message += ch
                
                send_json({"event":"CHAR","morse":current_symbol,"char":ch})
                current_symbol = ""
                last_change = now
        else:
            
            gap2 = (now - last_change) / 1000.0
            if gap2 >= INTER_WORD_GAP and current_message.endswith(" ") is False and current_message != "":
                current_message += " "
                send_json({"event":"WORD_GAP"})
                last_change = now

        
        if current_message != "":
            silence = (now - last_change) / 1000.0
            if silence >= 3 * INTER_CHAR_GAP:
                
                send_json({"event":"MESSAGE","text":current_message})
                current_message = ""
                last_change = now

        time.sleep(0.01)


def select_readable(): #si hay una señal nueva se la mando a la pico para que la revise
    res = uselect.select([sys.stdin], [], [], 0)
    return res[0]


if __name__ == "__main__":
    send_json({"event":"READY","unit":"A"})
    try:
        main_loop()
    except KeyboardInterrupt:
        pass
    

git remote add origin https://github.com/KingsOfEnter/Proyecto1.git
git branch -M main
git push -u origin main