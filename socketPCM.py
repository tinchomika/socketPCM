import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import socket
import threading
import logging
import traceback
from datetime import datetime
import os
import json
import sys
import time

# Determine the appropriate PyAudio library based on the operating system
if sys.platform.startswith("win"):
    import pyaudiowpatch as pyaudio  #This library adds wasapi loopback support
    pyaudio_library = "PyAudioWPatch" #Logged for debugging
else:
    import pyaudio
    pyaudio_library = "pyaudio"

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            return local_ip
    except OSError as e:
        return "127.0.0.1"


class AudioStreamer:
    def __init__(self, master):
        self.master = master
        master.title("SocketPCM")
        master.geometry("500x600")

        # Logging setup
        self.setup_logging()

        # Audio Configuration
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 44100

        # Network Configuration
        self.HOST = ''
        self.PORT = 65432

        # Streaming control
        self.is_streaming = False
        self.stream_thread = None
        self.stream_socket = None
        self.stop_event = threading.Event()

        # PyAudio Instance
        self.p = pyaudio.PyAudio()

        # Load last settings
        self.last_settings = self.load_last_settings()

        try:
            if os.path.exists("tinchopcm.ico"):
                self.master.iconbitmap("tinchopcm.ico") # Set window icon, there are problems with retrieving the icon from inside the exe
            else:
                print("Icon file not found.")
        except tk.TclError as e:
            print(f"Error setting icon: {e}")

        # Language Configuration
        self.language_strings = {
            "en": {
                "mode_label": "Select Mode:",
                "sender": "Sender",
                "receiver": "Receiver",
                "input_label": "Input Device:",
                "output_label": "Output Device:",
                "ip_label": "IP Address:",
                "port_label": "Port:",
                "sample_rate_label": "Sample Rate:",
                "low_latency": "Low Latency",
                "start_button": "Stream",
                "stop_button": "Stop Streaming",
                "logs_label": "Logs:",
                "select_input": "Select Input Device",
                "select_output": "Select Output Device",
                "error_ip_port": "Enter IP address and port...",
                "error_port": "Invalid port.",
                "streaming_start_input": "Streaming audio using input device: ",
                "streaming_start_output": "Receiving audio using output device: ",
                "streaming_rate": "Streaming at ",
                "low_latency_on": "Low latency enabled, CHUNK = 256",
                "low_latency_off": "Low latency disabled, CHUNK = 1024",
                "streaming_stopped": "Streaming stopped by user",
                "connecting_to": "Attempting to connect to ",
                "connected_to": "Connected to ",
                "sender_error": "Sender error: ",
                "receiver_error": "Receiver error: ",
                "socket_close_error": "Error closing socket: ",
                "stream_close_error": "Error closing stream: ",
                "accept_connection_error": "Error accepting connection: ",
                "audio_receive_error": "Error receiving/playing audio: ",
                "save_settings_error": "Error saving last settings: ",
                "address_in_use": "Address {ip}:{port} already in use. Retrying in {delay} seconds...",
                "waiting_for_connection": "Waiting for sender connection...",
                "connection_from": "Connection from ",
                "error_starting_stream": "Error starting stream: "
            },
            "es": {
                "mode_label": "Seleccionar Modo:",
                "sender": "Emisor",
                "receiver": "Receptor",
                "input_label": "Dispositivo de Entrada:",
                "output_label": "Dispositivo de Salida:",
                "ip_label": "Dirección IP:",
                "port_label": "Puerto:",
                "sample_rate_label": "Sample Rate:",
                "low_latency": "Baja Latencia",
                "start_button": "Transmitir",
                "stop_button": "Detener transmisión",
                "logs_label": "Logs:",
                "select_input": "Seleccionar Dispositivo de Entrada",
                "select_output": "Seleccionar Dispositivo de Salida",
                "error_ip_port": "Escribí la dirección IP y el puerto...",
                "error_port": "Puerto inválido.",
                "streaming_start_input": "Transmitiendo audio utilizando el dispositivo de entrada: ",
                "streaming_start_output": "Recibiendo audio utilizando el dispositivo de salida: ",
                "streaming_rate": "Transmitiendo a ",
                "low_latency_on": "Baja latencia activada, CHUNK = 128",
                "low_latency_off": "Baja latencia desactivada, CHUNK = 1024",
                "streaming_stopped": "Transmisión detenida por el usuario",
                "connecting_to": "Intentando conectar a ",
                "connected_to": "Conectado a ",
                "sender_error": "Error del emisor: ",
                "receiver_error": "Error del receptor: ",
                "socket_close_error": "Error al cerrar el socket: ",
                "stream_close_error": "Error cerrando transmisión: ",
                "accept_connection_error": "Error aceptando conexión: ",
                "audio_receive_error": "Error en la recepción/reproducción de audio: ",
                "save_settings_error": "Error guardando la última configuración: ",
                "address_in_use": "Dirección {ip}:{port} ya en uso. Reintentando en {delay} segundos...",
                "waiting_for_connection": "Esperando conexión del emisor...",
                "connection_from": "Conexión desde ",
                "error_starting_stream": "Error al iniciar la transmisión: "
            }
        }
        self.current_language = self.last_settings.get('language', 'en')

        # Create UI Components
        self.create_ui()
        self.log_message(f"PyAudio lib: {pyaudio_library}")
        self.set_language(self.current_language)
        self.set_dropdown_values()

        # Bind window close event to stop_streaming
        self.master.protocol("WM_DELETE_WINDOW", self.on_window_close)

    def setup_logging(self):
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')

        # Configure logging
        log_filename = f"logs/audio_streamer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def create_ui(self):
        # Language Selection
        self.lang_var = tk.StringVar(value=self.current_language)
        lang_frame = tk.Frame(self.master)
        lang_frame.pack(side=tk.TOP, anchor=tk.NE, padx=5, pady=5)
        lang_dropdown = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=["en", "es"],
            width=3,
            state="readonly"
        )
        lang_dropdown.pack(side=tk.RIGHT)
        lang_dropdown.bind("<<ComboboxSelected>>", self.on_language_change)

        # Mode Selection
        self.mode_label = tk.Label(self.master, text=self.language_strings[self.current_language]["mode_label"], font=("Arial", 12))
        self.mode_label.pack(pady=10)
        self.mode_var = tk.StringVar(value="sender")
        modes = [(self.language_strings[self.current_language]["sender"], "sender"), (self.language_strings[self.current_language]["receiver"], "receiver")]
        mode_frame = tk.Frame(self.master)
        mode_frame.pack()
        for text, mode in modes:
            tk.Radiobutton(
                mode_frame, 
                text=text, 
                variable=self.mode_var, 
                value=mode,
                command=self.update_device_selectors
            ).pack(side=tk.LEFT, padx=10)

        # Input Device Selection
        self.input_label = tk.Label(self.master, text=self.language_strings[self.current_language]["input_label"], font=("Arial", 12))
        self.input_label.pack(pady=5)
        self.input_devices = self.get_audio_devices('input')
        self.input_device_var = tk.StringVar()
        self.input_dropdown = ttk.Combobox(
            self.master, 
            textvariable=self.input_device_var, 
            values=self.input_devices,
            width=40
        )
        self.input_dropdown.pack(pady=5)
        self.input_dropdown.set(self.language_strings[self.current_language]["select_input"])
        if self.last_settings and self.last_settings.get('input_device'):
            self.input_device_var.set(self.last_settings['input_device'])

        # Output Device Selection
        self.output_label = tk.Label(self.master, text=self.language_strings[self.current_language]["output_label"], font=("Arial", 12))
        self.output_label.pack(pady=5)
        self.output_devices = self.get_audio_devices('output')
        self.output_device_var = tk.StringVar()
        self.output_dropdown = ttk.Combobox(
            self.master, 
            textvariable=self.output_device_var, 
            values=self.output_devices,
            width=40
        )
        self.output_dropdown.pack(pady=5)
        self.output_dropdown.set(self.language_strings[self.current_language]["select_output"])
        if self.last_settings and self.last_settings.get('output_device'):
            self.output_device_var.set(self.last_settings['output_device'])


        # IP Address Entry
        self.ip_label = tk.Label(self.master, text=self.language_strings[self.current_language]["ip_label"], font=("Arial", 12))
        self.ip_label.pack(pady=10)
        self.ip_var = tk.StringVar(value=self.last_settings.get('ip') or get_local_ip()) # Use last IP or local IP
        ip_entry = tk.Entry(self.master, textvariable=self.ip_var, width=20)
        ip_entry.pack(pady=5)

        # Port Entry (added)
        self.port_label = tk.Label(self.master, text=self.language_strings[self.current_language]["port_label"], font=("Arial", 12))
        self.port_label.pack(pady=5)
        self.port_var = tk.StringVar(value=str(self.PORT))
        port_entry = tk.Entry(self.master, textvariable=self.port_var, width=10)
        port_entry.pack(pady=5)

        # Sample Rate Selection
        self.sample_rate_label = tk.Label(self.master, text=self.language_strings[self.current_language]["sample_rate_label"], font=("Arial", 12))
        self.sample_rate_label.pack(pady=5)
        self.sample_rate_var = tk.StringVar(value="44100")
        sample_rates = ["44100", "48000"]
        self.sample_rate_dropdown = ttk.Combobox(
            self.master,
            textvariable=self.sample_rate_var,
            values=sample_rates,
            width=10
        )
        self.sample_rate_dropdown.pack(pady=5)
        self.sample_rate_dropdown.set("44100")

        # Low Latency Checkbox
        self.low_latency_var = tk.BooleanVar(value=self.last_settings.get('low_latency', False))
        low_latency_check = tk.Checkbutton(
            self.master,
            text=self.language_strings[self.current_language]["low_latency"],
            variable=self.low_latency_var
        )
        low_latency_check.pack(pady=5)


        # Buttons Frame
        button_frame = tk.Frame(self.master)
        button_frame.pack(pady=10)

        # Start Button
        self.start_button = tk.Button(
            button_frame, 
            text=self.language_strings[self.current_language]["start_button"],
            command=self.start_streaming
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        # Stop Button
        self.stop_button = tk.Button(
            button_frame, 
            text=self.language_strings[self.current_language]["stop_button"],
            command=self.stop_streaming,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Logging Text Area
        self.logs_label = tk.Label(self.master, text=self.language_strings[self.current_language]["logs_label"], font=("Arial", 12))
        self.logs_label.pack(pady=5)
        self.log_text = scrolledtext.ScrolledText(
            self.master, 
            wrap=tk.WORD, 
            width=60, 
            height=10
        )
        self.log_text.pack(pady=10)

        # Initial device selector state
        self.update_device_selectors()

    def update_device_selectors(self):
        mode = self.mode_var.get()
        if mode == "sender":
            # In sender mode, disable output device selector
            self.output_dropdown.config(state='disabled')
            self.output_label.config(fg='gray')
            self.input_dropdown.config(state='normal')
            self.input_label.config(fg='black')
        else:
            # In receiver mode, disable input device selector
            self.input_dropdown.config(state='disabled')
            self.input_label.config(fg='gray')
            self.output_dropdown.config(state='normal')
            self.output_label.config(fg='black')

    def log_message(self, message, level='info'):
        # Log to file and update scrolled text widget
        if level == 'info':
            self.logger.info(message)
        elif level == 'error':
            self.logger.error(message)
        elif level == 'warning':
            self.logger.warning(message)
        
        # Update log text widget
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def get_audio_devices(self, direction):
        devices = []
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            if direction == 'input' and dev['maxInputChannels'] > 0:
                devices.append(f"{i}: {dev['name']}")
            elif direction == 'output' and dev['maxOutputChannels'] > 0:
                devices.append(f"{i}: {dev['name']}")
        return devices

    def start_streaming(self):
        try:
            # Reset log text
            self.log_text.delete('1.0', tk.END)

            # Validate inputs
            ip_address = self.ip_var.get()
            port = self.port_var.get()
            if not ip_address or not port:
                messagebox.showerror("Error", self.language_strings[self.current_language]["error_ip_port"])
                return
            try:
                port = int(port)
            except ValueError:
                messagebox.showerror("Error", self.language_strings[self.current_language]["error_port"])
                return

            input_device_index = None
            output_device_index = None

            mode = self.mode_var.get()
            if mode == "sender":
                input_device_index = int(self.input_device_var.get().split(':')[0])
                self.log_message(f"{self.language_strings[self.current_language]['streaming_start_input']}{input_device_index}")
            else:
                output_device_index = int(self.output_device_var.get().split(':')[0])
                self.log_message(f"{self.language_strings[self.current_language]['streaming_start_output']}{output_device_index}")

            # Get selected sample rate
            self.RATE = int(self.sample_rate_var.get())
            self.log_message(f"{self.language_strings[self.current_language]['streaming_rate']}{self.RATE} Hz")

            # Select low latency chunk size, the default 1024 chunk size should be more stable
            low_latency = self.low_latency_var.get()
            if low_latency:
                self.CHUNK = 128 #In case of instability, set to 256 or 512
                self.log_message(self.language_strings[self.current_language]["low_latency_on"])
            else:
                self.CHUNK = 1024 
                self.log_message(self.language_strings[self.current_language]["low_latency_off"])


            # start/stop button switch
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)

            # Set streaming flag
            self.is_streaming = True
            self.stop_event.clear()

            # Start streaming thread
            if mode == "sender":
                self.stream_thread = threading.Thread(
                    target=self.start_sender, 
                    args=(input_device_index, ip_address, port), 
                    daemon=True
                )
            else:
                self.stream_thread = threading.Thread(
                    target=self.start_receiver, 
                    args=(output_device_index, ip_address, port), 
                    daemon=True
                )
            
            self.stream_thread.start()

            self.save_last_settings(ip_address, port, self.output_device_var.get(), self.input_device_var.get(), self.sample_rate_var.get(), low_latency, self.current_language) #Save settings after starting

        except Exception as e:
            self.log_message(f"{self.language_strings[self.current_language]['error_starting_stream']}{e}", 'error')
            self.log_message(traceback.format_exc(), 'error')
            messagebox.showerror("Error", str(e))
            self.reset_ui()

    def stop_streaming(self):
        self.is_streaming = False
        self.stop_event.set()
        
        # Close socket if exists
        if self.stream_socket:
            try:
                self.stream_socket.close()
            except Exception as e:
                self.log_message(f"{self.language_strings[self.current_language]['socket_close_error']}{e}", 'error')

        # Reset UI
        self.reset_ui()
        self.log_message(self.language_strings[self.current_language]["streaming_stopped"])

    def reset_ui(self):
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def start_sender(self, input_device, ip, port):
        stream = None
        sock = None
        try:
            self.log_message(f"{self.language_strings[self.current_language]['connecting_to']}{ip}:{port}")
            
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.stream_socket = sock
            sock.connect((ip, port))
            self.log_message(f"{self.language_strings[self.current_language]['connected_to']}{ip}:{port}")

            # Open input stream
            stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                input_device_index=input_device,
                frames_per_buffer=self.CHUNK
            )

            # Send audio
            while self.is_streaming and not self.stop_event.is_set():
                data = stream.read(self.CHUNK)
                sock.sendall(data)

        except Exception as e:
            self.log_message(f"{self.language_strings[self.current_language]['sender_error']}{e}", 'error')
            self.log_message(traceback.format_exc(), 'error')
        finally:
            self.is_streaming = False
            if sock:
                try:
                    sock.close()
                except Exception as e:
                    self.log_message(f"{self.language_strings[self.current_language]['socket_close_error']}{e}", 'error')
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception as e:
                    self.log_message(f"{self.language_strings[self.current_language]['stream_close_error']}{e}", 'error')
            
            # Reset UI
            self.master.after(0, self.reset_ui)

    def start_receiver(self, output_device, ip, port):
        sock = None
        conn = None
        stream = None
        try:
            self.log_message(f"{self.language_strings[self.current_language]['receiver_error']}{ip}:{port}")
            
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Added SO_REUSEADDR
            self.stream_socket = sock  # Store for potential stopping
            
            delay = 1
            max_retries = 10
            retries = 0
            while retries < max_retries:
                try:
                    sock.bind((ip, port))
                    break
                except OSError as e:
                    if e.errno == 98:
                        self.logger.warning(f"{self.language_strings[self.current_language]['address_in_use'].format(ip=ip, port=port, delay=delay)}")
                        time.sleep(delay)
                        delay *= 2
                        retries += 1
                    else:
                        raise e

            sock.listen(1)
            
            self.log_message(self.language_strings[self.current_language]["waiting_for_connection"])
            while self.is_streaming and not self.stop_event.is_set():
                if not self.is_streaming or self.stop_event.is_set():
                    break
                try:
                    conn, addr = sock.accept()
                    self.log_message(f"{self.language_strings[self.current_language]['connection_from']}{addr}")

                    # Open output stream
                    stream = self.p.open(
                        format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        output=True,
                        output_device_index=output_device,
                        frames_per_buffer=self.CHUNK
                    )

                    # Receive and play audio
                    while self.is_streaming and not self.stop_event.is_set():
                        if not self.is_streaming or self.stop_event.is_set():
                            break
                        try:
                            data = conn.recv(self.CHUNK * 2)
                            if not data:
                                break
                            stream.write(data)
                        except Exception as e:
                            self.log_message(f"{self.language_strings[self.current_language]['audio_receive_error']}{e}", 'error')	
                            break
                    
                except Exception as e:
                    self.log_message(f"{self.language_strings[self.current_language]['accept_connection_error']}{e}", 'error')
                    break
                finally:
                    if stream:
                        try:
                            stream.stop_stream()
                            stream.close()
                        except Exception as e:
                            self.log_message(f"{self.language_strings[self.current_language]['stream_close_error']}{e}", 'error')
                    if conn:
                        try:
                            conn.close()
                        except Exception as e:
                            self.log_message(f"{self.language_strings[self.current_language]['socket_close_error']}{e}", 'error')


        except Exception as e:
            self.log_message(f"{self.language_strings[self.current_language]['receiver_error']}{e}", 'error')
            self.log_message(traceback.format_exc(), 'error')
        finally:
            self.is_streaming = False
            if conn:
                try:
                    conn.close()
                except Exception as e:
                    self.log_message(f"{self.language_strings[self.current_language]['socket_close_error']}{e}", 'error')
            if sock:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()
                except Exception as e:
                    self.log_message(f"{self.language_strings[self.current_language]['socket_close_error']}{e}", 'error')
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception as e:
                    self.log_message(f"{self.language_strings[self.current_language]['stream_close_error']}{e}", 'error')
            
            
            self.master.after(0, self.reset_ui)

    def save_last_settings(self, ip, port, output_device, input_device, sample_rate, low_latency, language):
        try:
            with open('last_settings.json', 'w') as f:
                json.dump({'ip': ip, 'port': port, 'output_device': output_device, 'input_device': input_device, 'sample_rate': sample_rate, 'low_latency': low_latency, 'language': language, 'chunk_size': self.CHUNK}, f)
        except Exception as e:
            self.log_message(f"{self.language_strings[self.current_language]['save_settings_error']}{e}", 'error')
            print(f"Error guardando la última configuración: {e}")

    def load_last_settings(self):
        try:
            with open('last_settings.json', 'r') as f:
                data = json.load(f)
                return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return {}
    
    def set_language(self, language):
        self.current_language = language
        self.mode_label.config(text=self.language_strings[language]["mode_label"])
        modes = [(self.language_strings[language]["sender"], "sender"), (self.language_strings[language]["receiver"], "receiver")]
        for widget in self.master.winfo_children():
            if isinstance(widget, tk.Frame):
                for sub_widget in widget.winfo_children():
                    if isinstance(sub_widget, tk.Radiobutton):
                        if sub_widget['value'] == 'sender':
                            sub_widget.config(text=self.language_strings[language]["sender"])
                        elif sub_widget['value'] == 'receiver':
                            sub_widget.config(text=self.language_strings[language]["receiver"])
        self.input_label.config(text=self.language_strings[language]["input_label"])
        self.output_label.config(text=self.language_strings[language]["output_label"])
        self.ip_label.config(text=self.language_strings[language]["ip_label"])
        self.port_label.config(text=self.language_strings[language]["port_label"])
        self.sample_rate_label.config(text=self.language_strings[language]["sample_rate_label"])
        self.start_button.config(text=self.language_strings[language]["start_button"])
        self.stop_button.config(text=self.language_strings[language]["stop_button"])
        self.logs_label.config(text=self.language_strings[language]["logs_label"])
        self.input_dropdown.set(self.language_strings[language]["select_input"])
        self.output_dropdown.set(self.language_strings[language]["select_output"])
        for widget in self.master.winfo_children():
            if isinstance(widget, tk.Checkbutton):
                widget.config(text=self.language_strings[language]["low_latency"])

    def on_language_change(self, event):
        selected_language = self.lang_var.get()
        self.set_language(selected_language)
        self.save_last_settings(self.ip_var.get(), self.port_var.get(), self.output_device_var.get(), self.input_device_var.get(), self.sample_rate_var.get(), self.low_latency_var.get(), selected_language)

    def on_window_close(self):
        self.stop_streaming()
        self.master.destroy()
    
    def set_dropdown_values(self):
        if self.last_settings and self.last_settings.get('input_device'):
            self.input_device_var.set(self.last_settings['input_device'])
        if self.last_settings and self.last_settings.get('output_device'):
            self.output_device_var.set(self.last_settings['output_device'])

def main():
    root = tk.Tk()
    app = AudioStreamer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
