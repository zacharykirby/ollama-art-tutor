import sys
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QTextEdit, QPushButton, QHBoxLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
import json
import requests
from PIL import ImageGrab
import io
import base64

class ScreenshotWorker(QThread):
    screenshot_taken = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
        
    def run(self):
        while self.running:
            # Take screenshot
            screenshot = ImageGrab.grab()
            # Convert to base64
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            self.screenshot_taken.emit(img_str)
            # Wait 5 seconds before next capture
            time.sleep(5)
            
    def stop(self):
        self.running = False

class OllamaInterface:
    def __init__(self):
        self.base_url = "http://localhost:11434/api/generate"
        self.model = "llama3.2-vision"
        
    def query_model(self, prompt, image=None):
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if image:
            data["images"] = [image]
            
        response = requests.post(self.base_url, json=data)
        if response.status_code == 200:
            return response.json()["response"]
        return "Error communicating with Ollama"

class ArtTutorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ollama = OllamaInterface()
        self.init_ui()
        self.setup_screenshot_worker()
        
    def init_ui(self):
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
        # Create input area
        input_layout = QHBoxLayout()
        self.text_input = QTextEdit()
        self.text_input.setMaximumHeight(50)
        input_layout.addWidget(self.text_input)
        
        # Create buttons
        button_layout = QVBoxLayout()
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.review_button = QPushButton("Review Drawing")
        self.review_button.clicked.connect(self.request_review)
        button_layout.addWidget(self.send_button)
        button_layout.addWidget(self.review_button)
        input_layout.addLayout(button_layout)
        
        layout.addLayout(input_layout)
        
        # Window properties
        self.setWindowTitle('AI Art Tutor')
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.resize(400, 600)
        
        # Initialize last_screenshot
        self.last_screenshot = None
        
    def setup_screenshot_worker(self):
        self.screenshot_worker = ScreenshotWorker()
        self.screenshot_worker.screenshot_taken.connect(self.update_screenshot)
        self.screenshot_worker.start()
        
    def update_screenshot(self, screenshot):
        self.last_screenshot = screenshot
        
    def send_message(self):
        message = self.text_input.toPlainText()
        if message:
            self.chat_display.append(f"You: {message}\n")
            response = self.ollama.query_model(message, self.last_screenshot)
            self.chat_display.append(f"Tutor: {response}\n")
            self.text_input.clear()
            
    def request_review(self):
        if self.last_screenshot:
            prompt = """Please review my current drawing progress. Focus on:
            1. Shape accuracy and proportions
            2. Line quality
            3. Shading technique and consistency
            4. Light source positioning
            Provide specific feedback and suggestions for improvement."""
            
            response = self.ollama.query_model(prompt, self.last_screenshot)
            self.chat_display.append(f"Tutor Review: {response}\n")
            
    def closeEvent(self, event):
        self.screenshot_worker.stop()
        self.screenshot_worker.wait()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ArtTutorWindow()
    window.show()
    sys.exit(app.exec())