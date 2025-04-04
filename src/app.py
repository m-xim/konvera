import random
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog,
    QComboBox, QProgressBar, QGraphicsColorizeEffect
)
from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent, QColor, QIcon
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QEvent
import qasync

import sys
import os
import asyncio

from src.config import config
from src.tools.converter import FileConverter
from src.tools.optimize import FileOptimizer
from src.utils.exception_handler import exception_handler
from src.utils.resource_path import resource_path


class Konvera(QWidget):
    def __init__(self):
        super().__init__()

        self.config = config

        self.optimizer: Optional[FileOptimizer] = None
        self.converter: Optional[FileConverter] = None
        self.setWindowTitle(self.config.main.title)
        self.setWindowIcon(QIcon(resource_path("resource/icon.ico")))
        self.setFixedSize(400, 440)
        self.setAcceptDrops(True)
        self.file_path = None
        self.drag_effect = None
        self.drag_animation = None
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1f1f2e;
                color: #d0d0d0;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            QLabel#DropLabel {
                border: 2px dashed #555;
                border-radius: 12px;
                padding: 30px;
                background-color: #2b2b3c;
                color: #aaa;
                transition: all 0.3s ease;
            }
            QPushButton {
                background-color: #2491eb;
                color: white;
                padding: 10px;
                font-weight: bold;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #197cc1;
            }
            QComboBox {
                background-color: #2b2b3c;
                padding: 8px;
                border-radius: 8px;
                color: white;
                border: 1px solid #444;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 0px solid #444;
            }
            QProgressBar {
                border: none;
                border-radius: 10px;
                text-align: center;
                background-color: #2b2b3c;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #29abe2;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout()

        self.label = QLabel("Перетащите файл сюда\nили нажмите на кнопку ниже")
        self.label.setObjectName("DropLabel")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.drag_effect = QGraphicsColorizeEffect()
        self.drag_effect.setColor(QColor("#2b2b3c"))
        self.drag_effect.setStrength(0.0)
        self.label.setGraphicsEffect(self.drag_effect)

        self.choose_button = QPushButton("Выбрать файл")
        self.choose_button.clicked.connect(lambda: asyncio.ensure_future(self.choose_file()))

        self.format_combo = QComboBox()
        self.format_combo.addItems(["Формат конвертации"])
        self.format_combo.setDisabled(True)

        self.convert_button = QPushButton("Конвертировать")
        self.convert_button.clicked.connect(lambda: asyncio.ensure_future(self.convert_file()))

        btn_line = QHBoxLayout()

        self.compress_button = QPushButton("Сжать файл")
        self.compress_button.clicked.connect(lambda: asyncio.ensure_future(self.compress_file()))
        self.compress_button.setVisible(False)
        btn_line.addWidget(self.compress_button)

        # self.link_button = QPushButton("Получить ссылку")
        # self.link_button.clicked.connect(lambda: asyncio.ensure_future(self.get_file_link()))
        # btn_line.addWidget(self.link_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        layout.addWidget(self.label)
        layout.addWidget(self.choose_button)
        layout.addWidget(self.format_combo)
        layout.addWidget(self.convert_button)
        layout.addLayout(btn_line)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)
        self.installEventFilter(self)

    async def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл")
        if path:
            await self.set_file(path)

    async def set_file(self, path):
        self.file_path = path
        self.label.setText(f"Выбран файл:\n{os.path.basename(path)}")

        self.converter = FileConverter(self.file_path)
        formats = await self.converter.get_available_formats()
        if not formats:
            self.format_combo.clear()
            self.format_combo.addItems(["Не поддерживаемый формат"])
            return

        self.format_combo.setDisabled(False)
        self.format_combo.clear()
        self.format_combo.addItems(formats)

        self.optimizer = FileOptimizer()
        if self.optimizer.is_format_supported(self.converter.extension):
            self.compress_button.setVisible(True)

    async def convert_file(self):
        if not self.file_path:
            self.label.setText("Выберите файл")
            return

        format_selected = self.format_combo.currentText()
        self.label.setText(f"Конвертация в {format_selected}...")

        progress_task = asyncio.create_task(self.simulate_progress(max_value=random.randint(80, 90)))
        try:
            await self.converter.convert_to_format(format_selected)
        except Exception as e:
            self.label.setText(f"❌ Произошла ошибка: {e}")
        finally:
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass

        await self.complete_progress("✅ Конвертация завершена!")

    async def simulate_progress(self, max_value: int = 90):
        """
        Симулирует заполнение прогресс-бара до max_value
        """
        self.progress_bar.setValue(0)
        for i in range(1, max_value + 1):
            await asyncio.sleep(0.008)
            self.progress_bar.setValue(i)

    async def complete_progress(self, done_message):
        """
        Доводит прогресс-бар с текущего значения до 100% и выводит финальное сообщение.
        """
        current = self.progress_bar.value()
        for i in range(current + 1, 101):
            await asyncio.sleep(0.005)
            self.progress_bar.setValue(i)
        self.label.setText(done_message)

    async def get_file_link(self):
        if not self.file_path:
            self.label.setText("Выберите первый файл")
            return

        self.label.setText("Загрузка и генерация ссылки...")
        self.progress_bar.setValue(0)

        try:
            pass
        except Exception as e:
            self.label.setText(f"❌ Error: {e}")

    async def compress_file(self):
        if not self.file_path:
            self.label.setText("Выберите файл")
            return

        progress_task = asyncio.create_task(self.simulate_progress(max_value=random.randint(80, 90)))
        try:
            await self.optimizer.optimize_file(self.file_path)
        except Exception as e:
            self.label.setText(f"❌ Произошла ошибка: {e}")
        finally:
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass

        # После завершения конвертации доводим прогресс до 100%
        await self.complete_progress("✅ Сжатие завершено!")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.animate_drag_enter()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.animate_drag_leave()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            path = event.mimeData().urls()[0].toLocalFile()
            asyncio.ensure_future(self.set_file(path))
            self.animate_drag_leave()

    def animate_drag_enter(self):
        self.drag_animation = QPropertyAnimation(self.drag_effect, b"strength")
        self.drag_animation.setDuration(300)
        self.drag_animation.setStartValue(self.drag_effect.strength())
        self.drag_animation.setEndValue(1.0)
        self.drag_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.drag_animation.start()

    def animate_drag_leave(self):
        self.drag_animation = QPropertyAnimation(self.drag_effect, b"strength")
        self.drag_animation.setDuration(300)
        self.drag_animation.setStartValue(self.drag_effect.strength())
        self.drag_animation.setEndValue(0.0)
        self.drag_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.drag_animation.start()

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.DragLeave:
            self.animate_drag_leave()
        return super().eventFilter(source, event)


if __name__ == '__main__':
    sys.excepthook = exception_handler

    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = Konvera()
    window.show()
    with loop:
        loop.run_forever()
