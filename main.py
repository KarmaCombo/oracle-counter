#!/usr/bin/env python3
"""
Oracle Counter - Simplified Version
Clean, lightweight numpad counter for gaming
"""

import sys
import json
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from pynput import keyboard
from pynput.keyboard import Controller, Key
import webbrowser

# Numpad mapping
NUMPAD_MAPPING = {
    96: '0', 97: '1', 98: '2', 99: '3', 100: '4',
    101: '5', 102: '6', 103: '7', 104: '8', 105: '9'
}

# Default configuration
DEFAULT_CONFIG = {
    "overlay_color": "#ffff00",
    "overlay_x": None,
    "overlay_y": None,
    "overlay_locked": False
}

def load_config():
    try:
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config = json.load(f)
                # Ensure all keys exist
                for key, default_value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = default_value
                return config
    except:
        pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)
        return True
    except:
        return False


class OverlayWindow(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.drag_pos = None
        
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setup_ui()
        self.set_position()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.label = QLabel("")
        self.label.setAlignment(Qt.AlignCenter)
        # Initialize with empty text to prevent showing preview immediately
        self.update_text("")
        
        layout.addWidget(self.label)
        self.setLayout(layout)
        
    def update_overlay_style(self):
        """Update overlay appearance based on lock state and content"""
        has_content = bool(self.label.text().strip() and not self.label.text().startswith("Overlay"))
        is_locked = self.config.get('overlay_locked', False)
        
        if has_content:
            # Show text normally when there is actual number content
            if is_locked:
                border_style = "none"
                bg_color = "transparent"
            else:
                border_style = "2px dashed #ff4757"
                bg_color = "rgba(255, 71, 87, 0.15)"
            text_color = self.config['overlay_color']
        elif is_locked:
            # Locked: completely transparent
            border_style = "none"
            bg_color = "transparent"
            text_color = "transparent"
        else:
            # Unlocked: always show red preview box for positioning
            border_style = "2px dashed #ff4757"
            bg_color = "rgba(255, 71, 87, 0.15)"
            text_color = "#ff4757"
            
        # Adjust font size based on content
        has_actual_numbers = bool(self.label.text().strip() and not self.label.text().startswith("Overlay"))
        font_size = "36px" if has_actual_numbers else "16px"
        
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-family: 'Consolas', monospace;
                font-size: {font_size};
                font-weight: 700;
                background-color: {bg_color};
                border: {border_style};
                border-radius: 8px;
                padding: 12px 16px;
                min-width: 420px;
                min-height: 60px;
            }}
        """)
        
    def set_position(self):
        if self.config["overlay_x"] is not None and self.config["overlay_y"] is not None:
            self.move(self.config["overlay_x"], self.config["overlay_y"])
        else:
            # Center on screen
            screen = QApplication.primaryScreen().geometry()
            self.move((screen.width() - 480) // 2, 30)
    
    def update_text(self, text):
        # Limit to 7 numbers with spaces
        numbers = text.split()
        if len(numbers) > 7:
            numbers = numbers[:7]
            text = ' '.join(numbers)
        
        # Show appropriate text based on content and lock state
        if text.strip():
            # Show actual numbers
            self.label.setText(text)
        elif not self.config.get('overlay_locked', False):
            # Show positioning help when unlocked and empty
            self.label.setText("Overlay Position\n(max 7 numbers)")
        else:
            # Show nothing when locked and empty
            self.label.setText("")
            
        self.update_overlay_style()
        
    def update_color(self, color):
        self.config['overlay_color'] = color
        self.update_overlay_style()
    
    def set_click_through(self, enabled):
        if enabled:
            # Make window click-through
            self.setWindowFlags(
                Qt.FramelessWindowHint |
                Qt.WindowStaysOnTopHint |
                Qt.Tool |
                Qt.WindowTransparentForInput
            )
            self.setCursor(Qt.BlankCursor)
        else:
            # Normal window
            self.setWindowFlags(
                Qt.FramelessWindowHint |
                Qt.WindowStaysOnTopHint |
                Qt.Tool
            )
            self.setCursor(Qt.SizeAllCursor)
        
        self.show()  # Reapply flags
        self.update_overlay_style()  # Refresh appearance based on new lock state
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos:
            self.move(self.pos() + event.globalPos() - self.drag_pos)
            self.drag_pos = event.globalPos()
            
            # Save position and auto-save config
            self.config["overlay_x"] = self.x()
            self.config["overlay_y"] = self.y()
            save_config(self.config)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = Controller()
        self.logged_numbers = []
        self.config = load_config()
        self.overlay = None
        
        self.setWindowTitle("Oracle Counter")
        self.setFixedSize(500, 600)  # Optimized window size for readable buttons
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        self.setup_ui()
        self.start_keyboard_listener()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 12px;
                color: white;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #666666;
            }
            QPushButton:pressed {
                background-color: #363636;
            }
            QGroupBox {
                font-weight: 600;
                font-size: 12px;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #333333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                background-color: #2b2b2b;
            }
        """)
        
        # Title bar
        title_bar = QFrame()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-bottom: 1px solid #404040;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)
        
        title_label = QLabel("Oracle Counter")
        title_label.setStyleSheet("""
            font-weight: 600;
            font-size: 14px;
            color: #00d4aa;
            background: transparent;
            border: none;
        """)
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # Window controls
        close_btn = QPushButton("✖")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #f85149;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #da3633;
                color: white;
            }
        """)
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(close_btn)
        
        layout.addWidget(title_bar)
        
        # Main content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(18)
        
        # Settings Group
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(12)
        settings_layout.setContentsMargins(15, 20, 15, 15)
        
        # Settings controls row
        settings_row1 = QHBoxLayout()
        settings_row1.setSpacing(12)
        settings_row1.setContentsMargins(0, 0, 0, 0)
        
        # Color picker
        color_btn = QPushButton("Pick Color")
        color_btn.clicked.connect(self.pick_color)
        color_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 6px 8px;
                font-weight: 600;
                font-size: 10px;
                min-height: 26px;
                min-width: 65px;
            }
            QPushButton:hover { 
                background-color: #4a4a4a;
                border-color: #666666;
            }
        """)
        settings_row1.addWidget(color_btn)
        
        # Reset Default button
        reset_btn = QPushButton("Reset Default")
        reset_btn.clicked.connect(self.reset_default)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 6px 8px;
                font-weight: 600;
                font-size: 10px;
                min-height: 26px;
                min-width: 80px;
            }
            QPushButton:hover { 
                background-color: #4a4a4a;
                border-color: #666666;
            }
        """)
        settings_row1.addWidget(reset_btn)
        
        # Save button (will change to "Saved" when clicked)
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 6px 8px;
                font-weight: 600;
                font-size: 10px;
                min-height: 26px;
                min-width: 50px;
            }
            QPushButton:hover { 
                background-color: #4a4a4a;
                border-color: #666666;
            }
        """)
        settings_row1.addWidget(self.save_btn)
        
        # Lock toggle
        lock_status = "Locked" if self.config["overlay_locked"] else "Unlocked"
        self.lock_btn = QPushButton(f"🔒 {lock_status}")
        self.lock_btn.clicked.connect(self.toggle_lock)
        self.update_lock_button_style()
        settings_row1.addWidget(self.lock_btn)
        
        settings_layout.addLayout(settings_row1)
        content_layout.addWidget(settings_group)
        
        # Display Area
        display_frame = QFrame()
        display_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #555555;
                border-radius: 4px;
                min-height: 80px;
            }
        """)
        display_layout = QVBoxLayout(display_frame)
        display_layout.setContentsMargins(25, 25, 25, 25)
        
        self.display_label = QLabel("")
        self.display_label.setAlignment(Qt.AlignCenter)
        self.display_label.setStyleSheet(f"""
            color: {self.config['overlay_color']};
            font-family: 'Consolas', monospace;
            font-size: 36px;
            font-weight: 700;
            background: transparent;
            border: none;
            min-height: 60px;
        """)
        display_layout.addWidget(self.display_label)
        
        content_layout.addWidget(display_frame)
        
        # Info text
        info = QLabel("Enter → Send | Backspace → Clear | Use Numpad for Input")
        info.setStyleSheet("""
            color: #888888;
            font-size: 13px;
            background: transparent;
            border: none;
            margin: 10px 0;
            font-weight: 500;
        """)
        info.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(info)
        
        # Action buttons
        action_row = QHBoxLayout()
        action_row.setSpacing(15)
        action_row.setContentsMargins(0, 0, 0, 0)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_numbers)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 12px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        action_row.addWidget(clear_btn)
        
        # Overlay toggle button
        overlay_status = "OFF" if not self.overlay else "ON"
        self.overlay_btn = QPushButton(f"Overlay {overlay_status}")
        self.overlay_btn.clicked.connect(self.toggle_overlay)
        self.update_overlay_button_style()
        action_row.addWidget(self.overlay_btn)
        
        content_layout.addLayout(action_row)
        
        # Overlay Position Group
        position_group = QGroupBox("Overlay Position")
        pos_layout = QHBoxLayout(position_group)
        pos_layout.setSpacing(10)
        pos_layout.setContentsMargins(15, 20, 15, 15)
        
        for pos, text in [("left", "Left"), ("mid", "Middle"), ("right", "Right")]:
            pos_btn = QPushButton(text)
            pos_btn.clicked.connect(lambda checked, p=pos: self.set_position(p))
            pos_btn.setStyleSheet("""
                QPushButton {
                    background-color: #404040;
                    color: white;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    padding: 6px 12px;
                    font-weight: 600;
                    font-size: 10px;
                    min-height: 26px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                    border-color: #666666;
                }
            """)
            pos_layout.addWidget(pos_btn)
        
        content_layout.addWidget(position_group)
        
        content_layout.addStretch()
        
        # Footer
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(8)
        
        made_by = QLabel("Made by Kirito")
        made_by.setAlignment(Qt.AlignCenter)
        made_by.setStyleSheet("""
            color: #888888;
            font-size: 11px;
            background: transparent;
            border: none;
            font-weight: 500;
        """)
        footer_layout.addWidget(made_by)
        
        # Profile link button
        profile_btn = QPushButton("guns.lol/kirito8101")
        profile_btn.clicked.connect(lambda: webbrowser.open("https://guns.lol/kirito8101"))
        profile_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #007bff;
                border: 1px solid #007bff;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 500;
                font-size: 10px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: rgba(0, 123, 255, 0.1);
                color: #0056b3;
                border-color: #0056b3;
            }
        """)
        footer_layout.addWidget(profile_btn)
        
        content_layout.addLayout(footer_layout)
        
        layout.addWidget(content)
        self.setLayout(layout)
        
        # Make title bar draggable
        title_bar.mousePressEvent = self.title_mouse_press
        title_bar.mouseMoveEvent = self.title_mouse_move
        title_label.mousePressEvent = self.title_mouse_press
        title_label.mouseMoveEvent = self.title_mouse_move
        
    def title_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos()
    
    def title_mouse_move(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos'):
            self.move(self.pos() + event.globalPos() - self.drag_pos)
            self.drag_pos = event.globalPos()
    
    def update_lock_button_style(self):
        """Update lock button styling based on state"""
        if self.config["overlay_locked"]:
            self.lock_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: 1px solid #dc3545;
                    border-radius: 3px;
                    padding: 6px 8px;
                    font-weight: 600;
                    font-size: 10px;
                    min-height: 26px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                    border-color: #c82333;
                }
            """)
        else:
            self.lock_btn.setStyleSheet("""
                QPushButton {
                    background-color: #404040;
                    color: white;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    padding: 6px 8px;
                    font-weight: 600;
                    font-size: 10px;
                    min-height: 26px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                    border-color: #666666;
                }
            """)
    
    def update_overlay_button_style(self):
        """Update overlay button styling based on state"""
        if self.overlay:
            self.overlay_btn.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 10px 20px;
                    font-weight: 600;
                    font-size: 12px;
                    min-height: 35px;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)
        else:
            self.overlay_btn.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 10px 20px;
                    font-weight: 600;
                    font-size: 12px;
                    min-height: 35px;
                }
                QPushButton:hover {
                    background-color: #5a6268;
                }
            """)
    
    def start_keyboard_listener(self):
        def on_key_press(key):
            try:
                if hasattr(key, 'vk') and key.vk in NUMPAD_MAPPING:
                    # Limit to 7 numbers
                    if len(self.logged_numbers) < 7:
                        self.logged_numbers.append(NUMPAD_MAPPING[key.vk])
                        self.update_display()
            except:
                pass
            
            if key == Key.enter:
                self.send_numbers()
            elif key == Key.backspace:
                self.clear_numbers()
        
        listener = keyboard.Listener(on_press=on_key_press)
        listener.daemon = True
        listener.start()
    
    def update_display(self):
        text = ' '.join(self.logged_numbers)
        self.display_label.setText(text)
        if self.overlay:
            self.overlay.update_text(text)
    
    def send_numbers(self):
        if self.logged_numbers:
            text = ''.join(self.logged_numbers)
            self.controller.type(text)
            self.clear_numbers()
    
    def clear_numbers(self):
        self.logged_numbers.clear()
        self.update_display()
    
    def toggle_overlay(self):
        if self.overlay:
            self.overlay.close()
            self.overlay = None
            self.overlay_btn.setText("Overlay OFF")
        else:
            self.overlay = OverlayWindow(self.config)
            self.overlay.set_click_through(self.config["overlay_locked"])
            # Initialize overlay with current numbers (empty initially)
            current_text = ' '.join(self.logged_numbers)
            self.overlay.update_text(current_text)
            self.overlay.show()
            self.overlay_btn.setText("Overlay ON")
        
        self.update_overlay_button_style()
    
    def toggle_lock(self):
        self.config["overlay_locked"] = not self.config["overlay_locked"]
        
        # Update button text and styling
        lock_status = "Locked" if self.config["overlay_locked"] else "Unlocked"
        self.lock_btn.setText(f"🔒 {lock_status}")
        
        self.update_lock_button_style()
        
        if self.overlay:
            self.overlay.set_click_through(self.config["overlay_locked"])
            # Update overlay display to show/hide red preview box
            current_text = ' '.join(self.logged_numbers)
            self.overlay.update_text(current_text)
        
        # Auto-save the setting
        save_config(self.config)
    
    def set_position(self, pos):
        if not self.overlay:
            return
            
        screen = QApplication.primaryScreen().geometry()
        overlay_w, overlay_h = 480, 100  # Wider to accommodate 7 numbers
        
        if pos == "left":
            x = 20
        elif pos == "right":
            x = screen.width() - overlay_w - 20
        else:  # middle
            x = (screen.width() - overlay_w) // 2
        
        y = 30
        
        self.overlay.move(x, y)
        self.config["overlay_x"] = x
        self.config["overlay_y"] = y
        save_config(self.config)
    
    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name()
            self.config["overlay_color"] = hex_color
            
            # Update display label with new styling
            self.display_label.setStyleSheet(f"""
                color: {hex_color};
                font-family: 'Consolas', monospace;
                font-size: 36px;
                font-weight: 700;
                background: transparent;
                border: none;
                min-height: 60px;
            """)
            
            if self.overlay:
                self.overlay.update_color(hex_color)
            
            # Auto-save color change
            save_config(self.config)
    
    def reset_default(self):
        """Reset color to default"""
        self.config["overlay_color"] = DEFAULT_CONFIG["overlay_color"]
        
        # Update display with default color
        self.display_label.setStyleSheet(f"""
            color: {self.config['overlay_color']};
            font-family: 'Consolas', monospace;
            font-size: 36px;
            font-weight: 700;
            background: transparent;
            border: none;
            min-height: 60px;
        """)
        
        if self.overlay:
            self.overlay.update_color(self.config["overlay_color"])
        
        # Auto-save reset
        save_config(self.config)
        
        # Show feedback
        self.show_save_feedback("Reset to default!")
    
    def save_settings(self):
        """Save current settings"""
        if save_config(self.config):
            self.show_save_feedback("Saved!")
    
    def show_save_feedback(self, message="Saved!"):
        """Show temporary save confirmation"""
        original_text = self.save_btn.text()
        original_style = self.save_btn.styleSheet()
        
        # Show success feedback
        self.save_btn.setText(message)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: 1px solid #28a745;
                border-radius: 3px;
                padding: 6px 8px;
                font-weight: 600;
                font-size: 10px;
                min-height: 26px;
                min-width: 50px;
            }
            QPushButton:hover {
                background-color: #218838;
                border-color: #218838;
            }
        """)
        
        # Restore original state after delay
        QTimer.singleShot(2000, lambda: (
            self.save_btn.setText(original_text),
            self.save_btn.setStyleSheet(original_style)
        ))
    def closeEvent(self, event):
        if self.overlay:
            self.overlay.close()
        save_config(self.config)
        event.accept()

class OracleCounterApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(True)
        
    def run(self):
        # Show main window directly (no loading screen)
        self.main_window = MainWindow()
        self.main_window.show()
        return self.app.exec_()

if __name__ == "__main__":
    try:
        app = OracleCounterApp()
        sys.exit(app.run())
    except ImportError:
        print("PyQt5 is required but not installed.")
        print("Install it with: pip install PyQt5")
        input("Press Enter to exit...")