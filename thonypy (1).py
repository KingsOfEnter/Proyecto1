
import tkinter as tk
from tkinter import simpledialog, messagebox
import threading
import serial
import serial.tools.list_ports
import json
import time
import random

DEFAULT_PHRASES = ["SOS","SI","NO","HOLA","AMIGO","AYUDA","OK","GRACIAS","BUENAS","ADIOS"]

class PCMorseApp:
    def __init__(self, root):
        self.root = root
        root.title("StrangerTEC Morse - PC Interface")
        self.unit = tk.StringVar(value="A")
        self.ports = []
        self.ser = None
        self.read_thread = None
        self.running = False
        self.current_phrase = ""
        self.scoreA = 0
        self.scoreB = 0

        
        frame = tk.Frame(root)
        frame.pack(padx=10, pady=10)

        
        port_frame = tk.Frame(frame)
        port_frame.pack(fill="x")
        tk.Label(port_frame, text="Serial port:").pack(side="left")
        self.port_cb = tk.StringVar()
        self.port_menu = tk.OptionMenu(port_frame, self.port_cb, ())
        self.port_menu.pack(side="left")
        tk.Button(port_frame, text="Refresh", command=self.refresh_ports).pack(side="left")
        tk.Button(port_frame, text="Connect", command=self.connect_serial).pack(side="left")

        
        unit_frame = tk.Frame(frame)
        unit_frame.pack(fill="x", pady=(8,0))
        tk.Label(unit_frame, text="Unit:").pack(side="left")
        tk.Radiobutton(unit_frame, text="A (0.2s)", variable=self.unit, value="A").pack(side="left")
        tk.Radiobutton(unit_frame, text="B (0.3s)", variable=self.unit, value="B").pack(side="left")
        tk.Button(unit_frame, text="Send Unit to Pico", command=self.send_unit).pack(side="left", padx=8)

        
        phrase_frame = tk.Frame(frame)
        phrase_frame.pack(fill="x", pady=(8,0))
        tk.Label(phrase_frame, text="Phrases (max 10, <=16 chars):").pack(anchor="w")
        self.phrase_listbox = tk.Listbox(phrase_frame, height=6, width=40)
        self.phrase_listbox.pack(side="left")
        for p in DEFAULT_PHRASES:
            self.phrase_listbox.insert("end", p)
        btns = tk.Frame(phrase_frame)
        btns.pack(side="left", padx=8)
        tk.Button(btns, text="Add", command=self.add_phrase).pack(fill="x")
        tk.Button(btns, text="Edit", command=self.edit_phrase).pack(fill="x")
        tk.Button(btns, text="Remove", command=self.remove_phrase).pack(fill="x")

        
        game_frame = tk.Frame(frame)
        game_frame.pack(fill="x", pady=(8,0))
        tk.Button(game_frame, text="Start Round (send phrase to Pico)", command=self.start_round).pack(side="left")
        tk.Button(game_frame, text="Request Present (LED)", command=self.request_present).pack(side="left", padx=6)

        
        status_frame = tk.Frame(frame)
        status_frame.pack(fill="x", pady=(8,0))
        self.status_label = tk.Label(status_frame, text="Not connected")
        self.status_label.pack(anchor="w")
        self.result_text = tk.Text(frame, height=8, width=60)
        self.result_text.pack()

        self.refresh_ports()

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        self.ports = [p.device for p in ports]
        menu = self.port_menu["menu"]
        menu.delete(0, "end")
        for p in self.ports:
            menu.add_command(label=p, command=lambda v=p: self.port_cb.set(v))
        if self.ports:
            self.port_cb.set(self.ports[0])

    def connect_serial(self):
        port = self.port_cb.get()
        if not port:
            messagebox.showwarning("No port", "Select a serial port first.")
            return
        try:
            self.ser = serial.Serial(port, 115200, timeout=0.1)
            self.status_label.config(text=f"Connected to {port}")
            self.running = True
            self.read_thread = threading.Thread(target=self.read_loop, daemon=True)
            self.read_thread.start()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def send_unit(self):
        if not self.ser:
            messagebox.showwarning("Not connected", "Connect to Pico first.")
            return
        unit = self.unit.get()
        msg = {"cmd":"SET_UNIT","unit":unit}
        self.ser.write((json.dumps(msg)+"\n").encode())

    def add_phrase(self):
        if self.phrase_listbox.size() >= 10:
            messagebox.showwarning("Limit", "Maximum 10 phrases.")
            return
        p = simpledialog.askstring("Add phrase", "Enter phrase (<=16 chars):")
        if p and len(p) <= 16:
            self.phrase_listbox.insert("end", p.upper())

    def edit_phrase(self):
        sel = self.phrase_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        cur = self.phrase_listbox.get(idx)
        p = simpledialog.askstring("Edit phrase", "Edit phrase (<=16 chars):", initialvalue=cur)
        if p and len(p) <= 16:
            self.phrase_listbox.delete(idx)
            self.phrase_listbox.insert(idx, p.upper())

    def remove_phrase(self):
        sel = self.phrase_listbox.curselection()
        if not sel:
            return
        self.phrase_listbox.delete(sel[0])

    def start_round(self):
        if not self.ser:
            messagebox.showwarning("Not connected", "Connect to Pico first.")
            return
        
        size = self.phrase_listbox.size()
        if size == 0:
            messagebox.showwarning("No phrases", "Add at least one phrase.")
            return
        idx = random.randrange(size)
        phrase = self.phrase_listbox.get(idx)
        self.current_phrase = phrase
        
        msg = {"cmd":"PHRASE","text":phrase}
        self.ser.write((json.dumps(msg)+"\n").encode())
        self.result_text.insert("end", f"Sent phrase: {phrase}\n")
        self.result_text.see("end")

    def request_present(self):
        if not self.ser:
            messagebox.showwarning("Not connected", "Connect to Pico first.")
            return
        
        phrase = self.current_phrase or (self.phrase_listbox.get(0) if self.phrase_listbox.size()>0 else "")
        msg = {"cmd":"PHRASE_BUZZ","text":phrase}
        self.ser.write((json.dumps(msg)+"\n").encode())

    def read_loop(self):
        while self.running:
            try:
                line = self.ser.readline().decode().strip()
                if not line:
                    time.sleep(0.05)
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    self.result_text.insert("end", f"RAW: {line}\n")
                    self.result_text.see("end")
                    continue
                self.handle_pico_event(obj)
            except Exception:
                time.sleep(0.1)

    def handle_pico_event(self, obj):
        ev = obj.get("event")
        if ev == "READY":
            self.result_text.insert("end", "Pico ready\n")
        elif ev == "CHAR":
            morse = obj.get("morse")
            ch = obj.get("char")
            self.result_text.insert("end", f"Decoded char: {ch} (morse {morse})\n")
        elif ev == "MESSAGE":
            text = obj.get("text")
            self.result_text.insert("end", f"Full message from Pico: {text}\n")
            
            if self.current_phrase:
                score = self.compute_score(self.current_phrase, text)
                self.result_text.insert("end", f"Score: {score} / {len(self.current_phrase)}\n")
        else:
            self.result_text.insert("end", f"Event: {obj}\n")
        self.result_text.see("end")

    def compute_score(self, original, received):
        
        orig = original.upper()
        rec = received.upper()
        matches = sum(1 for a,b in zip(orig, rec) if a==b)
        return matches

if __name__ == "__main__":
    root = tk.Tk()
    app = PCMorseApp(root)
    root.mainloop()
