#!/usr/bin/env python3
"""
Razreshenie - SeqOVL & HostFakeSplit Edition
Упрощенный трей, новые стратегии
"""

import os
import sys
import ctypes
import subprocess
import threading
import queue
import tkinter as tk
import time

def elevate():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

elevate()

try:
    import customtkinter as ctk
    from PIL import Image, ImageDraw
    import pystray
except ImportError:
    ctypes.windll.user32.MessageBoxW(0, "pip install customtkinter pystray pillow", "Ошибка", 0x10)
    sys.exit()

os.chdir(os.path.dirname(os.path.abspath(__file__)))

SERVICE_NAME = "RazreshenieService"
CMD_FILE = "razreshenie_svc.cmd"

# Проверка наличия файлов паттернов
def check_bin(filename):
    return "✓" if os.path.exists(filename) else "✗"

STRATEGIES = {
    "ts_v1": {
        "name": "🔒 TS Fooling v1",
        "desc": "Классика, стабильно",
        "args": [
            "--wf-tcp=80,443,2053,2083,2087,2096,8443",
            "--wf-udp=443,19294-19344,50000-50100",
            "--filter-udp=443", "--hostlist=list-general.txt", "--dpi-desync=fake", "--dpi-desync-repeats=6",
            "--dpi-desync-fake-quic=quic_initial_www_google_com.bin", "--new",
            "--filter-udp=19294-19344,50000-50100", "--filter-l7=discord,stun", "--dpi-desync=fake", "--dpi-desync-repeats=6", "--new",
            "--filter-tcp=2053,2083,2087,2096,8443", "--hostlist-domains=discord.media", "--dpi-desync=fake", 
            "--dpi-desync-repeats=6", "--dpi-desync-fooling=ts", "--new",
            "--filter-tcp=443", "--hostlist=list-google.txt", "--ip-id=zero", "--dpi-desync=fake", 
            "--dpi-desync-repeats=6", "--dpi-desync-fooling=ts", "--new",
            "--filter-tcp=80,443", "--hostlist=list-general.txt", "--dpi-desync=fake", 
            "--dpi-desync-repeats=6", "--dpi-desync-fooling=ts", "--new",
            "--filter-udp=443", "--ipset=ipset-all.txt", "--dpi-desync=fake", "--dpi-desync-repeats=6", 
            "--dpi-desync-fake-quic=quic_initial_www_google_com.bin", "--new",
            "--filter-tcp=80,443", "--ipset=ipset-all.txt", "--dpi-desync=fake", "--dpi-desync-repeats=6", 
            "--dpi-desync-fooling=ts"
        ]
    },
    "seqovl_google": {
        "name": f"🔀 SeqOVL Google {check_bin('tls_clienthello_www_google_com.bin')}",
        "desc": "Перекрытие последовательности 681 байт",
        "args": [
            "--wf-tcp=80,443,2053,2083,2087,2096,8443",
            "--wf-udp=443,19294-19344,50000-50100",
            "--filter-udp=443", "--hostlist=list-general.txt", "--dpi-desync=fake", "--dpi-desync-repeats=6",
            "--dpi-desync-fake-quic=quic_initial_www_google_com.bin", "--new",
            "--filter-udp=19294-19344,50000-50100", "--filter-l7=discord,stun", "--dpi-desync=fake", "--dpi-desync-repeats=6", "--new",
            "--filter-tcp=2053,2083,2087,2096,8443", "--hostlist-domains=discord.media", 
            "--dpi-desync=multisplit", "--dpi-desync-split-seqovl=681", "--dpi-desync-split-pos=1",
            "--dpi-desync-split-seqovl-pattern=tls_clienthello_www_google_com.bin", "--new",
            "--filter-tcp=443", "--hostlist=list-google.txt", "--ip-id=zero", 
            "--dpi-desync=multisplit", "--dpi-desync-split-seqovl=681", "--dpi-desync-split-pos=1",
            "--dpi-desync-split-seqovl-pattern=tls_clienthello_www_google_com.bin", "--new",
            "--filter-tcp=80,443", "--hostlist=list-general.txt", 
            "--dpi-desync=multisplit", "--dpi-desync-split-seqovl=568", "--dpi-desync-split-pos=1",
            "--dpi-desync-split-seqovl-pattern=tls_clienthello_4pda_to.bin", "--new",
            "--filter-udp=443", "--ipset=ipset-all.txt", "--dpi-desync=fake", "--dpi-desync-repeats=6",
            "--dpi-desync-fake-quic=quic_initial_www_google_com.bin", "--new",
            "--filter-tcp=80,443", "--ipset=ipset-all.txt", 
            "--dpi-desync=multisplit", "--dpi-desync-split-seqovl=568", "--dpi-desync-split-pos=1",
            "--dpi-desync-split-seqovl-pattern=tls_clienthello_4pda_to.bin"
        ]
    },
    "hostfakesplit_google": {
        "name": f"🎭 HostFakeSplit Google {check_bin('tls_clienthello_www_google_com.bin')}",
        "desc": "Фейковый хост в разделенном пакете",
        "args": [
            "--wf-tcp=80,443,2053,2083,2087,2096,8443",
            "--wf-udp=443,19294-19344,50000-50100",
            "--filter-udp=443", "--hostlist=list-general.txt", "--dpi-desync=fake", "--dpi-desync-repeats=6",
            "--dpi-desync-fake-quic=quic_initial_www_google_com.bin", "--new",
            "--filter-udp=19294-19344,50000-50100", "--filter-l7=discord,stun", "--dpi-desync=fake", "--dpi-desync-repeats=6", "--new",
            "--filter-tcp=2053,2083,2087,2096,8443", "--hostlist-domains=discord.media", 
            "--dpi-desync=fake,hostfakesplit", "--dpi-desync-fake-tls-mod=rnd,dupsid,sni=www.google.com",
            "--dpi-desync-hostfakesplit-mod=host=www.google.com,altorder=1", "--dpi-desync-fooling=ts", "--new",
            "--filter-tcp=443", "--hostlist=list-google.txt", "--ip-id=zero", 
            "--dpi-desync=fake,hostfakesplit", "--dpi-desync-fake-tls-mod=rnd,dupsid,sni=www.google.com",
            "--dpi-desync-hostfakesplit-mod=host=www.google.com,altorder=1", "--dpi-desync-fooling=ts", "--new",
            "--filter-tcp=80,443", "--hostlist=list-general.txt", 
            "--dpi-desync=fake,hostfakesplit", "--dpi-desync-fake-tls-mod=rnd,dupsid,sni=ya.ru",
            "--dpi-desync-hostfakesplit-mod=host=ya.ru,altorder=1", "--dpi-desync-fooling=ts", "--new",
            "--filter-udp=443", "--ipset=ipset-all.txt", "--dpi-desync=fake", "--dpi-desync-repeats=6",
            "--dpi-desync-fake-quic=quic_initial_www_google_com.bin", "--new",
            "--filter-tcp=80,443", "--ipset=ipset-all.txt", 
            "--dpi-desync=fake,hostfakesplit", "--dpi-desync-fake-tls-mod=rnd,dupsid,sni=ya.ru",
            "--dpi-desync-hostfakesplit-mod=host=ya.ru,altorder=1", "--dpi-desync-fooling=ts"
        ]
    },
    "multidisorder_v2": {
        "name": "💀 MultiDisorder v2",
        "desc": "Агрессивный, repeats=11",
        "args": [
            "--wf-tcp=80,443,2053,2083,2087,2096,8443",
            "--wf-udp=443,19294-19344,50000-50100",
            "--filter-udp=443", "--hostlist=list-general.txt", "--dpi-desync=fake", "--dpi-desync-repeats=11",
            "--dpi-desync-fake-quic=quic_initial_www_google_com.bin", "--new",
            "--filter-udp=19294-19344,50000-50100", "--filter-l7=discord,stun", "--dpi-desync=fake", "--dpi-desync-repeats=6", "--new",
            "--filter-tcp=2053,2083,2087,2096,8443", "--hostlist-domains=discord.media", 
            "--dpi-desync=fake,multidisorder", "--dpi-desync-split-pos=1,midsld", "--dpi-desync-repeats=11", 
            "--dpi-desync-fooling=badseq", "--dpi-desync-fake-tls-mod=rnd,dupsid,sni=www.google.com", "--new",
            "--filter-tcp=443", "--hostlist=list-google.txt", "--ip-id=zero", "--dpi-desync=fake,multidisorder", 
            "--dpi-desync-split-pos=1,midsld", "--dpi-desync-repeats=11", "--dpi-desync-fooling=badseq", 
            "--dpi-desync-fake-tls-mod=rnd,dupsid,sni=www.google.com", "--new",
            "--filter-tcp=80,443", "--hostlist=list-general.txt", "--dpi-desync=fake,multidisorder", 
            "--dpi-desync-split-pos=1,midsld", "--dpi-desync-repeats=11", "--dpi-desync-fooling=badseq", 
            "--dpi-desync-fake-tls-mod=rnd,dupsid,sni=www.google.com", "--new",
            "--filter-udp=443", "--ipset=ipset-all.txt", "--dpi-desync=fake", "--dpi-desync-repeats=11",
            "--dpi-desync-fake-quic=quic_initial_www_google_com.bin", "--new",
            "--filter-tcp=80,443", "--ipset=ipset-all.txt", "--dpi-desync=fake,multidisorder", 
            "--dpi-desync-split-pos=1,midsld", "--dpi-desync-repeats=11", "--dpi-desync-fooling=badseq", 
            "--dpi-desync-fake-tls-mod=rnd,dupsid,sni=www.google.com"
        ]
    },
    "aggressive_combo": {
        "name": "🚀 Aggressive Combo (Эксперимент)",
        "desc": "Комбо: multidisorder + hostfakesplit + ts",
        "args": [
            "--wf-tcp=80,443,2053,2083,2087,2096,8443",
            "--wf-udp=443,19294-19344,50000-50100",
            "--filter-udp=443", "--hostlist=list-general.txt", "--dpi-desync=fake", "--dpi-desync-repeats=8",
            "--dpi-desync-fake-quic=quic_initial_www_google_com.bin", "--new",
            "--filter-tcp=443", "--hostlist=list-google.txt", "--ip-id=zero", 
            "--dpi-desync=fake,multidisorder,hostfakesplit", "--dpi-desync-split-pos=1,midsld", 
            "--dpi-desync-repeats=8", "--dpi-desync-fooling=badseq,ts",
            "--dpi-desync-fake-tls-mod=rnd,dupsid,sni=www.google.com",
            "--dpi-desync-hostfakesplit-mod=host=www.google.com,altorder=1", "--new",
            "--filter-tcp=80,443", "--hostlist=list-general.txt", 
            "--dpi-desync=fake,multidisorder", "--dpi-desync-split-pos=1", "--dpi-desync-repeats=8",
            "--dpi-desync-fooling=ts", "--new",
            "--filter-udp=50000-50100", "--ipset=ipset-all.txt", "--dpi-desync=fake", 
            "--dpi-desync-autottl=2", "--dpi-desync-repeats=12"
        ]
    },
    "lightweight": {
        "name": "🪶 Lightweight (Для слабых ПК)",
        "desc": "Минимум нагрузки, только TCP",
        "args": [
            "--wf-tcp=443",
            "--wf-udp=443",
            "--filter-tcp=443", "--hostlist=list-general.txt", "--dpi-desync=fake", 
            "--dpi-desync-repeats=3", "--dpi-desync-ttl=5", "--new",
            "--filter-udp=443", "--dpi-desync=fake", "--dpi-desync-repeats=2"
        ]
    },
    "ghost": {
        "name": "👻 Ghost (Safe Mode)",
        "desc": "Только фейки, без сплита",
        "args": [
            "--wf-tcp=443",
            "--wf-udp=443",
            "--filter-tcp=443", "--hostlist=list-general.txt", "--dpi-desync=fake", 
            "--dpi-desync-repeats=10", "--dpi-desync-ttl=3", "--new",
            "--filter-udp=443", "--dpi-desync=fake", "--dpi-desync-repeats=6"
        ]
    }
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Razreshenie - Extended Edition")
        self.geometry("900x750")
        ctk.set_appearance_mode("dark")
        
        self.process = None
        self.log_queue = queue.Queue()
        self.tray_icon = None
        self.running = False
        self.current_strategy = "ts_v1"
        
        self.build_ui()
        self.after(100, self.check_queue)
        self.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        self.kill_all_winws()
        
        # Проверка файлов при старте
        self.check_files()
        
    def check_files(self):
        missing = []
        for f in ["tls_clienthello_www_google_com.bin", "tls_clienthello_4pda_to.bin", "quic_initial_www_google_com.bin"]:
            if not os.path.exists(f):
                missing.append(f)
        if missing:
            self.log(f"⚠️ Отсутствуют файлы: {', '.join(missing)}")
            self.log("ℹ️ Некоторые стратегии могут не работать без .bin файлов")
        
    def build_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=("gray20", "gray10"))
        header.pack(fill="x", padx=10, pady=10)
        
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(title_frame, text="🛡️ Razreshenie Extended", font=("Roboto", 26, "bold")).pack(side="left", padx=20)
        
        ctk.CTkButton(title_frame, text="💀 Убить процессы", command=self.kill_all_winws,
                     fg_color="#c0392b", hover_color="#e74c3c", height=35, width=200).pack(side="right", padx=20)
        
        # Main
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left - Strategies (2 columns)
        left = ctk.CTkFrame(main, width=450)
        left.pack(side="left", fill="y", padx=5, pady=5)
        left.pack_propagate(False)
        
        ctk.CTkLabel(left, text="Выбор стратегии:", font=("Roboto", 16, "bold")).pack(anchor="w", padx=10, pady=(10,5))
        
        self.strategy_var = ctk.StringVar(value=self.current_strategy)
        
        # Frame for radio buttons
        radio_frame = ctk.CTkFrame(left, fg_color="transparent")
        radio_frame.pack(fill="both", expand=True, padx=5)
        
        for key, data in STRATEGIES.items():
            frame = ctk.CTkFrame(radio_frame, fg_color=("gray25", "gray17"))
            frame.pack(fill="x", padx=5, pady=3)
            
            rb = ctk.CTkRadioButton(frame, text=data["name"], variable=self.strategy_var, value=key,
                                   command=self.on_strategy_change, font=("Roboto", 12, "bold"))
            rb.pack(anchor="w", padx=10, pady=(5,0))
            
            ctk.CTkLabel(frame, text=data["desc"], font=("Roboto", 10), text_color="gray").pack(anchor="w", padx=30, pady=(0,5))
        
        # Controls
        btn_frame = ctk.CTkFrame(left, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=15)
        
        self.btn_toggle = ctk.CTkButton(btn_frame, text="▶ ЗАПУСТИТЬ", command=self.toggle,
                                       fg_color="#2ecc71", height=50, font=("Roboto", 18, "bold"))
        self.btn_toggle.pack(fill="x", pady=5)
        
        ctk.CTkButton(btn_frame, text="🔄 Перезапуск со сменой", command=self.restart_with_new_strategy,
                     height=40, font=("Roboto", 13)).pack(fill="x", pady=5)
        
        # Service
        svc = ctk.CTkFrame(left)
        svc.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(svc, text="Автозагрузка:", font=("Roboto", 13, "bold")).pack(pady=5)
        
        svc_btns = ctk.CTkFrame(svc, fg_color="transparent")
        svc_btns.pack(fill="x", pady=5)
        ctk.CTkButton(svc_btns, text="💾 Установить", command=self.install_service, width=130).pack(side="left", padx=5)
        ctk.CTkButton(svc_btns, text="🗑️ Удалить", command=self.remove_service, width=130, fg_color="#e74c3c").pack(side="right", padx=5)
        
        # Right - Logs
        right = ctk.CTkFrame(main)
        right.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        log_header = ctk.CTkFrame(right, fg_color="transparent")
        log_header.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(log_header, text="Лог выполнения:", font=("Roboto", 14, "bold")).pack(side="left")
        ctk.CTkButton(log_header, text="📋 Копировать всё", command=self.copy_all_logs, width=150).pack(side="right")
        
        self.log_text = ctk.CTkTextbox(right, font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.status_label = ctk.CTkLabel(right, text="⭕ Остановлено", text_color="gray", font=("Roboto", 12))
        self.status_label.pack(anchor="w", padx=10)
        
        # Context menu
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Копировать выделенное", command=self.copy_selected)
        self.menu.add_command(label="Копировать всё", command=self.copy_all_logs)
        self.log_text.bind("<Button-3>", lambda e: self.menu.post(e.x_root, e.y_root))
        
    def kill_all_winws(self):
        self.log("💀 Очистка процессов...")
        subprocess.run(["taskkill", "/f", "/im", "winws.exe"], capture_output=True)
        time.sleep(0.3)
        self.log("✅ Готово")
        
    def on_strategy_change(self):
        new = self.strategy_var.get()
        if new != self.current_strategy:
            old = self.current_strategy
            self.current_strategy = new
            self.log(f"🔄 {STRATEGIES[old]['name']} → {STRATEGIES[new]['name']}")
            if self.running:
                self.log("⚠️ Нажми 'Перезапуск' для применения")
                
    def restart_with_new_strategy(self):
        if self.running:
            self.log("🔄 Перезапуск...")
            self.stop()
            self.after(800, self.start)
        else:
            self.start()
            
    def get_cmd(self):
        if not os.path.exists("winws.exe"):
            self.log("❌ Нет winws.exe!")
            return None
        exe = os.path.abspath("winws.exe")
        strategy = STRATEGIES[self.current_strategy]
        return [exe] + strategy["args"]
        
    def log(self, msg):
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        
    def check_queue(self):
        try:
            while True:
                self.log(self.log_queue.get_nowait())
        except queue.Empty:
            pass
        self.after(100, self.check_queue)
        
    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()
            
    def start(self):
        self.kill_all_winws()
        
        cmd = self.get_cmd()
        if not cmd:
            return
            
        self.log(f"▶ {STRATEGIES[self.current_strategy]['name']}")
        
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                          text=True, bufsize=1, creationflags=0x08000000)
            self.running = True
            self.btn_toggle.configure(text="⏹ ОСТАНОВИТЬ", fg_color="#e74c3c")
            self.status_label.configure(text=f"🟢 {STRATEGIES[self.current_strategy]['name'][:30]}", text_color="#2ecc71")
            threading.Thread(target=self.read_output, daemon=True).start()
        except Exception as e:
            self.log(f"❌ Ошибка: {e}")
            
    def read_output(self):
        if self.process:
            for line in self.process.stdout:
                if line:
                    self.log_queue.put(line.strip())
        self.log_queue.put("⏹ Завершено")
        self.running = False
        self.after(0, self.reset_ui)
        
    def reset_ui(self):
        self.btn_toggle.configure(text="▶ ЗАПУСТИТЬ", fg_color="#2ecc71")
        self.status_label.configure(text="⭕ Остановлено", text_color="gray")
        
    def stop(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=1)
            except:
                self.process.kill()
            self.process = None
        self.kill_all_winws()
        self.running = False
        self.reset_ui()
        self.log("⏹ Остановлено")
        
    def copy_selected(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(self.log_text.get("sel.first", "sel.last"))
        except:
            pass
            
    def copy_all_logs(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(self.log_text.get("1.0", "end-1c"))
            self.log("✅ Лог скопирован")
        except:
            pass
            
    def hide_window(self):
        self.withdraw()
        if not self.tray_icon:
            image = Image.new('RGB', (64, 64), (30, 30, 30))
            ImageDraw.Draw(image).rectangle((16, 16, 48, 48), fill=(46, 204, 113))
            
            # УПРОЩЕННОЕ МЕНЮ - без выбора стратегий (так как они не работают корректно из трея)
            menu = pystray.Menu(
                pystray.MenuItem("Открыть Razreshenie", self.show_window),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("💀 Убить процессы", self.kill_all_winws),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Выход", self.quit_app)
            )
            self.tray_icon = pystray.Icon("Razreshenie", image, "Razreshenie", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            
    def show_window(self):
        self.deiconify()
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
            
    def quit_app(self):
        self.stop()
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy()
        sys.exit()
        
    def install_service(self):
        self.kill_all_winws()
        cmd = self.get_cmd()
        if not cmd:
            return
        bat = f'@echo off\ncd /d "{os.getcwd()}"\n' + " ".join(f'"{x}"' if " " in x else x for x in cmd)
        with open(CMD_FILE, "w") as f:
            f.write(bat)
        r = subprocess.run(f'sc create "{SERVICE_NAME}" binPath= "cmd /c \"{os.path.abspath(CMD_FILE)}\"" start= auto displayname= "Razreshenie"', 
                          shell=True, capture_output=True, text=True)
        if r.returncode == 0:
            subprocess.run(f'sc start "{SERVICE_NAME}"', shell=True, capture_output=True)
            self.log("✅ Служба установлена")
        else:
            self.log(f"⚠️ {r.stdout[:100]}")
            
    def remove_service(self):
        subprocess.run(f'sc stop "{SERVICE_NAME}"', shell=True, capture_output=True)
        r = subprocess.run(f'sc delete "{SERVICE_NAME}"', shell=True, capture_output=True)
        self.log("🗑️ Удалена" if r.returncode == 0 else "ℹ️ Не найдена")

if __name__ == "__main__":
    app = App()
    app.mainloop()