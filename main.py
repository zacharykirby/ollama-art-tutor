import sys
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QTextEdit, QPushButton, QHBoxLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QEvent
from PyQt6 import QtGui
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
            # Take a screenshot every 5 seconds
            screenshot = ImageGrab.grab()
            buffered = io.BytesIO()
            screenshot.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            self.screenshot_taken.emit(img_str)
            time.sleep(5)
            
    def stop(self):
        self.running = False

class OllamaInterface:
    def __init__(self):
        self.base_url = "http://localhost:11434/api/generate"
        self.model = "art-tutor"

    # simulate streaming by yielding chunks
    def query_model(self, prompt, image=None):
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": True  # enable streaming at the endpoint
        }
        
        if image:
            data["images"] = [image]

        response = requests.post(self.base_url, json=data, stream=True)
        
        # check if the request was successful
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    # convert response line to json and yield the chunk of text
                    yield json.loads(line)["response"]
        else:
            yield "Error communicating with Ollama"

class ChatWorker(QThread):
    # Signal to update the UI with each text chunk and to notify when done
    chunk_received = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, message, screenshot, ollama):
        super().__init__()
        self.message = message
        self.screenshot = screenshot
        self.ollama = ollama

    def run(self):
        # use the OllamaInterface's query_model generator for streaming
        self.chunk_received.emit('Assistant: ')
        for chunk in self.ollama.query_model(self.message, self.screenshot):
            self.chunk_received.emit(chunk)
        self.chunk_received.emit('\n')
        self.finished.emit()

class ArtTutorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ollama = OllamaInterface()
        self.init_ui()
        self.setup_screenshot_worker()
        
    def init_ui(self):
        # Set up the main interface layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Chat display area, read-only
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
        # Input area with a text box and send button
        input_layout = QHBoxLayout()
        self.text_input = QTextEdit()
        self.text_input.setMaximumHeight(50)
        self.text_input.installEventFilter(self)
        input_layout.addWidget(self.text_input)
        
        # Button layout for "Send" and "Review Drawing"
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
        
        # Initialize screenshot placeholder
        self.last_screenshot = None
        
    def setup_screenshot_worker(self):
        # Start a background worker to take periodic screenshots
        self.screenshot_worker = ScreenshotWorker()
        self.screenshot_worker.screenshot_taken.connect(self.update_screenshot)
        self.screenshot_worker.start()
        
    def update_screenshot(self, screenshot):
        # Store the latest screenshot as a base64 string
        self.last_screenshot = screenshot

    def send_message(self):
        # Grab the input text
        message = self.text_input.toPlainText()
        if not message:
            return
        
        # Display the user's message
        self.chat_display.append(f"You: {message}\n\n")
        self.text_input.clear()

        # Start the background worker for streaming response
        self.worker = ChatWorker(message, self.last_screenshot, self.ollama)
        self.worker.chunk_received.connect(self.display_chunk)  # handle each chunk
        self.worker.finished.connect(self.finish_response)
        self.worker.start()

    def display_chunk(self, chunk):
        # Append each chunk as it arrives to the chat display
        self.chat_display.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.chat_display.insertPlainText(chunk)

    def finish_response(self):
        # Add a newline for readability after the response completes
        self.chat_display.append("\n")

    def request_review(self):
        # Standard prompt for review when "Review Drawing" button is clicked
        if self.last_screenshot:
            prompt = """Please review my current drawing progress. Focus on:
            1. Shape accuracy and proportions
            2. Line quality
            3. Shading technique and consistency
            4. Light source positioning
            Provide specific feedback and suggestions for improvement."""
            
            self.send_message_with_prompt(prompt)
            
    def send_message_with_prompt(self, prompt):
        # Helper function for sending a pre-defined prompt, like review requests
        self.chat_display.append(f"You: {prompt}\n")
        self.worker = ChatWorker(prompt, self.last_screenshot, self.ollama)
        self.worker.chunk_received.connect(self.display_chunk)
        self.worker.finished.connect(self.finish_response)
        self.worker.start()

    def closeEvent(self, event):
        # Cleanly stop the screenshot worker
        self.screenshot_worker.stop()
        self.screenshot_worker.wait()
        event.accept()

    def eventFilter(self, obj, event):
        # Check for the Enter key to trigger sending the message
        if obj == self.text_input and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.send_message()
                return True
        return super().eventFilter(obj, event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ArtTutorWindow()
    window.show()
    sys.exit(app.exec())
