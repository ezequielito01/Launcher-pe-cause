import sys
import os
import subprocess
import threading
import urllib.request
import minecraft_launcher_lib
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, 
    QLineEdit, QComboBox, QPushButton, QMessageBox
)
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import pyqtSignal, QObject, Qt

def resource_path(relative_path):
    """ Obtiene la ruta absoluta para recursos empaquetados por PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

class MinecraftLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Minecraft Launcher Pe")
        self.setFixedSize(380, 480)

        # 1. Icono de la ventana (.ico)
        icon_path = resource_path("logo.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                font-size: 13px;
                font-weight: bold;
            }
            QLineEdit, QComboBox {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px;
                color: #f5e0dc;
                font-size: 13px;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                font-weight: bold;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
            QPushButton:disabled {
                background-color: #585b70;
                color: #a6adc8;
            }
        """)

        layout = QVBoxLayout()

        # Título
        title = QLabel("MINECRAFT LAUNCHER Pe")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #89b4fa; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 2. Imagen/Logo dentro de la interfaz (.png)
        img_path = resource_path("logo.png")
        if os.path.exists(img_path):
            label_logo = QLabel()
            pixmap = QPixmap(img_path)
            pixmap = pixmap.scaled(110, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label_logo.setPixmap(pixmap)
            label_logo.setAlignment(Qt.AlignCenter)
            layout.addWidget(label_logo)

        # Usuario
        self.label_user = QLabel("Nombre de usuario (sin espacios):")
        layout.addWidget(self.label_user)
        
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Ej: Jugador1")
        layout.addWidget(self.input_user)

        # Versión (Optimizadas y Vanilla)
        self.label_version = QLabel("Selecciona la versión:")
        layout.addWidget(self.label_version)

        self.combo_version = QComboBox()
        self.combo_version.addItems([
            "1.20.1 (Optimizado - Fabric/Sodium)",
            "1.20.1 (Vanilla)",
            "1.19.4 (Optimizado - Fabric/Sodium)",
            "1.19.4 (Vanilla)",
            "1.16.5 (Optimizado - Fabric/Sodium)",
            "1.16.5 (Vanilla)",
            "1.12.2 (Vanilla)",
            "1.8.9 (Vanilla)"
        ])
        layout.addWidget(self.combo_version)

        # Selector de RAM
        self.label_ram = QLabel("Memoria RAM asignada:")
        layout.addWidget(self.label_ram)

        self.combo_ram = QComboBox()
        self.combo_ram.addItems(["2 GB (PC Gama Baja)", "4 GB (Recomendado)", "6 GB (PC Gama Media)", "8 GB (PC Gama Alta)"])
        self.combo_ram.setCurrentIndex(1)
        layout.addWidget(self.combo_ram)

        # Botón
        self.btn_play = QPushButton("¡Jugar!")
        self.btn_play.clicked.connect(self.start_game_thread)
        layout.addWidget(self.btn_play)

        # Estado
        self.label_status = QLabel("Estado: Listo para jugar")
        self.label_status.setStyleSheet("color: #a6adc8; font-size: 11px;")
        layout.addWidget(self.label_status)

        self.setLayout(layout)

        self.signals = WorkerSignals()
        self.signals.finished.connect(self.on_download_finished)
        self.signals.error.connect(self.on_download_error)

    def start_game_thread(self):
        raw_username = self.input_user.text().strip()
        username = raw_username.replace(" ", "_")

        if not username:
            QMessageBox.warning(self, "Error", "Por favor, ingresá un nombre de usuario.")
            return

        self.btn_play.setEnabled(False)
        self.label_status.setText("Descargando/Verificando archivos...")

        threading.Thread(target=self.launch_game, args=(username,)).start()

    def launch_game(self, username):
        try:
            minecraft_directory = os.path.join(os.getenv('APPDATA'), '.milauncher_custom')
            selected_option = self.combo_version.currentText()

            ram_text = self.combo_ram.currentText()
            ram_amount = ram_text.split(" ")[0] + "G"

            jvm_arguments = [
                f"-Xmx{ram_amount}",
                "-XX:+UnlockExperimentalVMOptions",
                "-XX:+UseG1GC"
            ]

            options = {
                "username": username,
                "uuid": "",
                "token": "",
                "jvmArguments": jvm_arguments
            }

            # Lógica para versiones optimizadas con Fabric/Sodium
            if "Optimizado" in selected_option:
                if "1.20.1" in selected_option:
                    version_id = "1.20.1"
                    sodium_url = "https://cdn.modrinth.com/data/AANobbA5/versions/4m1Q3fX8/sodium-fabric-0.5.11%2Bmc1.20.1.jar"
                    sodium_filename = "sodium-fabric-0.5.11+mc1.20.1.jar"
                elif "1.19.4" in selected_option:
                    version_id = "1.19.4"
                    sodium_url = "https://cdn.modrinth.com/data/AANobbA5/versions/2I93sX1D/sodium-fabric-0.4.10%2Bmc1.19.4.jar"
                    sodium_filename = "sodium-fabric-0.4.10+mc1.19.4.jar"
                elif "1.16.5" in selected_option:
                    version_id = "1.16.5"
                    sodium_url = "https://cdn.modrinth.com/data/AANobbA5/versions/2I22x5Xk/sodium-fabric-0.2.0%2Bbuild.4.jar"
                    sodium_filename = "sodium-fabric-0.2.0+build.4.jar"

                # Instalar versión base y Fabric
                minecraft_launcher_lib.install.install_minecraft_version(version_id, minecraft_directory)
                minecraft_launcher_lib.fabric.install_fabric(version_id, minecraft_directory)
                
                # Descargar Sodium en la carpeta mods
                mods_dir = os.path.join(minecraft_directory, "mods")
                os.makedirs(mods_dir, exist_ok=True)
                sodium_file = os.path.join(mods_dir, sodium_filename)
                
                if not os.path.exists(sodium_file):
                    urllib.request.urlretrieve(sodium_url, sodium_file)

                # Seleccionar el perfil instalado de Fabric
                installed_versions = minecraft_launcher_lib.utils.get_installed_versions(minecraft_directory)
                target_version = next((v["id"] for v in installed_versions if "fabric" in v["id"].lower() and version_id in v["id"]), version_id)
            else:
                target_version = selected_option.split(" ")[0]
                minecraft_launcher_lib.install.install_minecraft_version(target_version, minecraft_directory)

            command = minecraft_launcher_lib.command.get_minecraft_command(target_version, minecraft_directory, options)

            self.signals.finished.emit()
            subprocess.call(command)

        except Exception as e:
            self.signals.error.emit(str(e))

    def on_download_finished(self):
        self.label_status.setText("Iniciando Minecraft...")
        self.btn_play.setEnabled(True)

    def on_download_error(self, error_msg):
        QMessageBox.critical(self, "Error", f"Ocurrió un error: {error_msg}")
        self.label_status.setText("Estado: Error al iniciar")
        self.btn_play.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = MinecraftLauncher()
    launcher.show()
    sys.exit(app.exec_())