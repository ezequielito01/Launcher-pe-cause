import sys
import os
import subprocess
import threading
import urllib.request
import json
import webbrowser
import minecraft_launcher_lib
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QComboBox, QPushButton, QMessageBox, QFrame, 
    QScrollArea
)
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import pyqtSignal, QObject, Qt

CURRENT_VERSION = "1.0.0"
CONFIG_URL = "https://raw.githubusercontent.com/ezequielito01/Launcher-pe-cause/main/versiones.json"
RELEASES_URL = "https://github.com/ezequielito01/Launcher-pe-cause/releases"
GITHUB_REPO_URL = "https://github.com/ezequielito01/Launcher-pe-cause"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    config_loaded = pyqtSignal(dict)
    status_updated = pyqtSignal(str)

class MinecraftLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.config_data = {}
        self.signals = WorkerSignals()
        self.signals.finished.connect(self.on_download_finished)
        self.signals.error.connect(self.on_download_error)
        self.signals.config_loaded.connect(self.on_config_loaded)
        self.signals.status_updated.connect(self.update_status_display)
        
        self.initUI()
        self.load_online_config()

    def initUI(self):
        self.setWindowTitle("Minecraft Launcher Pe")
        self.setMinimumSize(880, 540)
        self.resize(940, 580)

        icon_path = resource_path(os.path.join("assets", "logos", "logo.ico"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        dirt_bg_path = resource_path(os.path.join("assets", "images", "dirt.png"))
        if os.path.exists(dirt_bg_path):
            bg_style = f"background-image: url('{dirt_bg_path.replace(os.sep, '/')}'); background-repeat: repeat;"
        else:
            bg_style = "background-color: #241810;"

        self.setStyleSheet(f"""
            MinecraftLauncher {{
                {bg_style}
            }}
            QLabel {{
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                font-weight: bold;
                border: none;
                background: transparent;
            }}
            QLineEdit, QComboBox {{
                background-color: #1a120b;
                border: 2px solid #5c4028;
                border-radius: 4px;
                padding: 7px;
                color: #ffffff;
                font-size: 13px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 2px solid #6aa03e;
            }}
            QPushButton#btnPlay {{
                background-color: #486e29;
                color: #ffffff;
                font-weight: bold;
                border-radius: 4px;
                padding: 12px;
                font-size: 16px;
                border: 2px solid #6aa03e;
            }}
            QPushButton#btnPlay:hover {{
                background-color: #598833;
            }}
            QPushButton#btnPlay:disabled {{
                background-color: #28231e;
                border: 2px solid #1a1612;
                color: #666666;
            }}
            QScrollArea {{
                border: 2px solid #5c4028;
                background-color: #140f0b;
                border-radius: 6px;
            }}
            QScrollBar:vertical {{
                border: 1px solid #241810;
                background: #0a0705;
                width: 14px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: #486e29;
                min-height: 20px;
                border-radius: 2px;
                border: 1px solid #6aa03e;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #598833;
            }}
        """)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Panel Izquierdo
        left_panel = QFrame()
        left_panel.setFixedWidth(290)
        left_panel.setStyleSheet("""
            QFrame {
                background-color: #140f0b;
                border-radius: 6px;
                border: 2px solid #5c4028;
            }
        """)
        
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(15, 15, 15, 15)

        logo_path = resource_path(os.path.join("assets", "logos", "logo.png"))
        if os.path.exists(logo_path):
            label_logo = QLabel()
            pixmap = QPixmap(logo_path)
            pixmap_scaled = pixmap.scaled(240, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label_logo.setPixmap(pixmap_scaled)
            label_logo.setAlignment(Qt.AlignCenter)
            left_layout.addWidget(label_logo)
        else:
            title = QLabel("LAUNCHER PE")
            title.setFont(QFont("Segoe UI", 16, QFont.Bold))
            title.setStyleSheet("color: #6aa03e;")
            title.setAlignment(Qt.AlignCenter)
            left_layout.addWidget(title)

        left_layout.addSpacing(10)

        left_layout.addWidget(QLabel("Nombre del Jugador:"))
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Tu nickname aquí...")
        left_layout.addWidget(self.input_user)

        left_layout.addWidget(QLabel("Versión disponible:"))
        self.combo_version = QComboBox()
        self.combo_version.addItem("Cargando versiones...")
        left_layout.addWidget(self.combo_version)

        left_layout.addWidget(QLabel("Memoria RAM:"))
        self.combo_ram = QComboBox()
        self.combo_ram.addItems(["2 GB (PC Gama Baja)", "4 GB (Recomendado)", "6 GB (PC Gama Media)", "8 GB (PC Gama Alta)"])
        self.combo_ram.setCurrentIndex(1)
        left_layout.addWidget(self.combo_ram)

        left_layout.addStretch(1)

        self.btn_play = QPushButton("¡JUGAR!")
        self.btn_play.setObjectName("btnPlay")
        self.btn_play.clicked.connect(self.start_game_thread)
        left_layout.addWidget(self.btn_play)

        self.label_slogan = QLabel("Te queremos maicra <3")
        self.label_slogan.setStyleSheet("color: #a09386; font-size: 11px; font-style: italic;")
        self.label_slogan.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.label_slogan)

        left_panel.setLayout(left_layout)
        main_layout.addWidget(left_panel)

        # Contenedor Derecho
        right_container = QWidget()
        right_container.setStyleSheet("background: transparent;")
        right_container_layout = QVBoxLayout()
        right_container_layout.setContentsMargins(0, 0, 0, 0)
        right_container_layout.setSpacing(10)

        # Panel 2: Novedades con Scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 2px solid #5c4028;
                background-color: #140f0b;
                border-radius: 6px;
            }
            QWidget#scrollContent {
                background-color: #140f0b;
            }
        """)

        scroll_content = QWidget()
        scroll_content.setObjectName("scrollContent")
        scroll_layout = QVBoxLayout()
        scroll_layout.setContentsMargins(15, 15, 15, 15)
        scroll_layout.setSpacing(14)

        header_box = QFrame()
        header_box.setStyleSheet("background-color: #24160d; border: 2px solid #84b84b; border-radius: 6px;")
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        news_title = QLabel("⚡ NOVEDADES Y COMUNIDAD ⚡")
        news_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        news_title.setStyleSheet("color: #a3e46b;")
        news_title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(news_title)

        header_box.setLayout(header_layout)
        scroll_layout.addWidget(header_box)

        for i in range(1, 6):
            photo_path = resource_path(os.path.join("assets", "news", f"foto{i}.png"))
            if os.path.exists(photo_path):
                lbl_photo = QLabel()
                pix = QPixmap(photo_path)
                pix_scaled = pix.scaled(540, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                lbl_photo.setPixmap(pix_scaled)
                lbl_photo.setStyleSheet("border: 2px solid #5c4028; border-radius: 6px; background-color: #0b0806;")
                lbl_photo.setAlignment(Qt.AlignCenter)
                scroll_layout.addWidget(lbl_photo)

        scroll_layout.addWidget(QLabel("Repositorio Oficial:"))
        btn_github = QPushButton("Abrir GitHub del Launcher")
        btn_github.setStyleSheet("""
            QPushButton {
                background-color: #1d2836;
                color: #89b4fa;
                border: 2px solid #3b5270;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #28374a;
            }
        """)
        btn_github.clicked.connect(lambda: webbrowser.open(GITHUB_REPO_URL))
        scroll_layout.addWidget(btn_github)

        social_box = QLabel("Próximamente: Integración con Discord y servidores propios.")
        social_box.setStyleSheet("color: #d2a84e; font-style: italic; font-size: 11px;")
        scroll_layout.addWidget(social_box)

        scroll_layout.addStretch(1)
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        right_container_layout.addWidget(scroll_area)

        # Panel 3: Barra de Estado Inferior
        status_panel = QFrame()
        status_panel.setStyleSheet("""
            QFrame {
                background-color: #140f0b;
                border: 2px solid #5c4028;
                border-radius: 6px;
            }
        """)
        status_layout = QVBoxLayout()
        status_layout.setContentsMargins(10, 8, 10, 8)

        self.label_status = QLabel("Estado: Conectando con el servidor...")
        self.label_status.setStyleSheet("color: #e2c08d; font-size: 11px; background: transparent;")
        self.label_status.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.label_status)

        status_panel.setLayout(status_layout)
        right_container_layout.addWidget(status_panel)

        right_container.setLayout(right_container_layout)
        main_layout.addWidget(right_container)

        self.setLayout(main_layout)

    def load_online_config(self):
        def fetch():
            try:
                req = urllib.request.Request(CONFIG_URL, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    self.signals.config_loaded.emit(data)
            except Exception:
                default_data = {
                    "latest_launcher_version": CURRENT_VERSION,
                    "versions": [
                        {"name": "1.20.1 (Optimizado - Fabric/Sodium)", "type": "fabric", "version": "1.20.1", "sodium_url": "https://cdn.modrinth.com/data/AANobbA5/versions/4m1Q3fX8/sodium-fabric-0.5.11%2Bmc1.20.1.jar", "sodium_file": "sodium-fabric-0.5.11+mc1.20.1.jar"},
                        {"name": "1.20.1 (Vanilla)", "type": "vanilla", "version": "1.20.1"},
                        {"name": "1.19.4 (Vanilla)", "type": "vanilla", "version": "1.19.4"},
                        {"name": "1.16.5 (Vanilla)", "type": "vanilla", "version": "1.16.5"}
                    ]
                }
                self.signals.config_loaded.emit(default_data)

        threading.Thread(target=fetch, daemon=True).start()

    def on_config_loaded(self, data):
        self.config_data = data
        self.combo_version.clear()

        for v in data.get("versions", []):
            self.combo_version.addItem(v["name"])

        remote_ver = data.get("latest_launcher_version", CURRENT_VERSION)
        if remote_ver != CURRENT_VERSION:
            self.signals.status_updated.emit(f"¡Nueva versión {remote_ver} disponible en GitHub!")
            reply = QMessageBox.question(
                self, "Actualización",
                f"Hay una nueva versión del launcher ({remote_ver}). ¿Querés descargarla ahora?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                webbrowser.open(RELEASES_URL)
        else:
            self.signals.status_updated.emit("Listo para jugar - Actualizado")

    def update_status_display(self, text):
        self.label_status.setText(str(text))

    def start_game_thread(self):
        raw_username = self.input_user.text().strip()
        username = raw_username.replace(" ", "_")

        if not username:
            QMessageBox.warning(self, "Atención", "Por favor, ingresá un nombre de usuario.")
            return

        self.btn_play.setEnabled(False)
        self.signals.status_updated.emit("Verificando archivos y dependencias...")
        threading.Thread(target=self.launch_game, args=(username,)).start()

    def launch_game(self, username):
        try:
            minecraft_directory = os.path.join(os.getenv('APPDATA'), '.milauncher_custom')
            selected_name = self.combo_version.currentText()

            selected_config = None
            for v in self.config_data.get("versions", []):
                if v["name"] == selected_name:
                    selected_config = v
                    break

            ram_text = self.combo_ram.currentText()
            ram_amount = ram_text.split(" ")[0] + "G"
            jvm_arguments = [f"-Xmx{ram_amount}", "-XX:+UnlockExperimentalVMOptions", "-XX:+UseG1GC"]

            options = {
                "username": username,
                "uuid": "",
                "token": "",
                "jvmArguments": jvm_arguments
            }

            if selected_config and selected_config.get("type") == "fabric":
                version_id = selected_config["version"]
                self.signals.status_updated.emit(f"Instalando base Minecraft {version_id}...")
                minecraft_launcher_lib.install.install_minecraft_version(version_id, minecraft_directory)
                
                self.signals.status_updated.emit("Configurando entorno Fabric...")
                try:
                    minecraft_launcher_lib.fabric.install_fabric(version_id, minecraft_directory)
                except Exception:
                    pass

                if "sodium_url" in selected_config:
                    mods_dir = os.path.join(minecraft_directory, "mods")
                    os.makedirs(mods_dir, exist_ok=True)
                    sodium_file = os.path.join(mods_dir, selected_config["sodium_file"])
                    if not os.path.exists(sodium_file):
                        self.signals.status_updated.emit("Descargando mod Sodium...")
                        try:
                            urllib.request.urlretrieve(selected_config["sodium_url"], sodium_file)
                        except Exception:
                            pass

                installed = minecraft_launcher_lib.utils.get_installed_versions(minecraft_directory)
                target_version = next((v["id"] for v in installed if "fabric" in v["id"].lower() and version_id in v["id"]), version_id)
            else:
                target_version = selected_config["version"] if selected_config else selected_name.split(" ")[0]
                self.signals.status_updated.emit(f"Verificando versión {target_version}...")
                minecraft_launcher_lib.install.install_minecraft_version(target_version, minecraft_directory)

            self.signals.status_updated.emit("¡Lanzando Minecraft con éxito!")
            command = minecraft_launcher_lib.command.get_minecraft_command(target_version, minecraft_directory, options)
            self.signals.finished.emit()
            
            # Oculta definitivamente la ventana del CMD en Windows
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.call(command, creationflags=creationflags)

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.signals.error.emit(error_msg)

    def on_download_finished(self):
        self.signals.status_updated.emit("Listo para jugar - Actualizado")
        self.btn_play.setEnabled(True)

    def on_download_error(self, error_msg):
        QMessageBox.critical(self, "Error al iniciar", f"Ocurrió un error al iniciar:\n\n{error_msg}")
        self.signals.status_updated.emit("Error al iniciar el juego")
        self.btn_play.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = MinecraftLauncher()
    launcher.show()
    sys.exit(app.exec_())