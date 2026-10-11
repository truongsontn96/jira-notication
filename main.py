"""
Jira Alert Monitor
==================
Ứng dụng giám sát Jira tickets và phát cảnh báo qua loa.

Features:
- Kết nối Jira Cloud/Server
- Thiết lập rules theo JQL
- Text-to-Speech với template tùy chỉnh
- Chạy background với system tray
- Build thành .exe
"""

import sys
import json
import logging
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QGroupBox, QTabWidget, QComboBox, QSpinBox, QCheckBox, QSystemTrayIcon,
    QMenu, QAction, QMessageBox, QHeaderView
)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QIcon
import requests
from gtts import gTTS
import tempfile
import os
from datetime import datetime
import subprocess
import platform

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Config file path
CONFIG_FILE = Path('config/settings.json')


class JiraMonitorThread(QThread):
    """Thread giám sát Jira tickets."""
    alert_triggered = pyqtSignal(dict)  # Phát tín hiệu khi có alert
    status_update = pyqtSignal(str)     # Update trạng thái

    def __init__(self):
        super().__init__()
        self.running = False
        self.config = {}
        self.seen_tickets = set()  # Track tickets đã alert

    def set_config(self, config):
        self.config = config

    def run(self):
        """Main monitoring loop."""
        self.running = True
        logger.info("Jira monitor thread started")

        while self.running:
            try:
                if self.config.get('jira_enabled'):
                    self.check_jira()
                # Sleep theo interval (giây)
                interval = self.config.get('check_interval', 60)
                for _ in range(interval):
                    if not self.running:
                        break
                    self.msleep(1000)  # Sleep 1s
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                self.msleep(5000)

    def check_jira(self):
        """Kiểm tra Jira tickets theo rules."""
        try:
            jira_url = self.config.get('jira_url', '').rstrip('/')
            email = self.config.get('jira_email')
            api_token = self.config.get('jira_api_token')

            if not all([jira_url, email, api_token]):
                return

            # Lấy rules
            rules = self.config.get('rules', [])
            if not rules:
                return

            for rule in rules:
                if not rule.get('enabled'):
                    continue

                jql = rule.get('jql', '')
                if not jql:
                    continue

                # Query Jira
                url = f"{jira_url}/rest/api/3/search"
                auth = (email, api_token)
                params = {
                    'jql': jql,
                    'maxResults': 50,
                    'fields': 'summary,status,priority,assignee,created,updated'
                }

                self.status_update.emit(f"Checking: {rule.get('name')}")
                response = requests.get(url, auth=auth, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    issues = data.get('issues', [])

                    # Kiểm tra tickets mới
                    for issue in issues:
                        ticket_key = issue.get('key')
                        if ticket_key not in self.seen_tickets:
                            self.seen_tickets.add(ticket_key)

                            # Trigger alert
                            fields = issue.get('fields', {})
                            alert_data = {
                                'rule_name': rule.get('name'),
                                'ticket_key': ticket_key,
                                'summary': fields.get('summary'),
                                'status': fields.get('status', {}).get('name'),
                                'priority': fields.get('priority', {}).get('name'),
                                'assignee': fields.get('assignee', {}).get('displayName', 'Unassigned'),
                                'tts_template': rule.get('tts_template'),
                                'url': f"{jira_url}/browse/{ticket_key}"
                            }
                            self.alert_triggered.emit(alert_data)
                            logger.info(f"Alert triggered: {ticket_key}")
                else:
                    logger.error(f"Jira API error: {response.status_code}")

        except Exception as e:
            logger.error(f"check_jira error: {e}")

    def stop(self):
        """Dừng monitoring."""
        self.running = False
        logger.info("Jira monitor thread stopped")


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jira Alert Monitor")
        self.setGeometry(100, 100, 900, 700)

        # Load config
        self.config = self.load_config()

        # Create monitor thread
        self.monitor_thread = JiraMonitorThread()
        self.monitor_thread.alert_triggered.connect(self.handle_alert)
        self.monitor_thread.status_update.connect(self.update_status)

        # Setup UI
        self.init_ui()

        # System tray
        self.setup_tray()

        # Load config vào UI
        self.load_ui_from_config()

    def init_ui(self):
        """Khởi tạo giao diện."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self.create_jira_tab(), "Jira Connection")
        tabs.addTab(self.create_rules_tab(), "Alert Rules")
        tabs.addTab(self.create_tts_tab(), "TTS Settings")
        tabs.addTab(self.create_log_tab(), "Activity Log")
        layout.addWidget(tabs)

        # Status bar
        self.status_label = QLabel("Status: Stopped")
        layout.addWidget(self.status_label)

        # Control buttons
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start Monitoring")
        self.btn_start.clicked.connect(self.start_monitoring)
        self.btn_stop = QPushButton("Stop Monitoring")
        self.btn_stop.clicked.connect(self.stop_monitoring)
        self.btn_stop.setEnabled(False)
        self.btn_test = QPushButton("Test Alert")
        self.btn_test.clicked.connect(self.test_alert)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addWidget(self.btn_test)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def create_jira_tab(self):
        """Tab cấu hình kết nối Jira."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Jira Connection Settings")
        form_layout = QVBoxLayout()

        # Jira URL
        form_layout.addWidget(QLabel("Jira URL (e.g., https://yourcompany.atlassian.net):"))
        self.jira_url_input = QLineEdit()
        self.jira_url_input.setPlaceholderText("https://yourcompany.atlassian.net")
        form_layout.addWidget(self.jira_url_input)

        # Email
        form_layout.addWidget(QLabel("Email:"))
        self.jira_email_input = QLineEdit()
        self.jira_email_input.setPlaceholderText("your.email@company.com")
        form_layout.addWidget(self.jira_email_input)

        # API Token
        form_layout.addWidget(QLabel("API Token:"))
        self.jira_token_input = QLineEdit()
        self.jira_token_input.setEchoMode(QLineEdit.Password)
        self.jira_token_input.setPlaceholderText("Get from: https://id.atlassian.com/manage-profile/security/api-tokens")
        form_layout.addWidget(self.jira_token_input)

        # Test connection button
        btn_test_conn = QPushButton("Test Connection")
        btn_test_conn.clicked.connect(self.test_jira_connection)
        form_layout.addWidget(btn_test_conn)

        # Check interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Check Interval (seconds):"))
        self.interval_input = QSpinBox()
        self.interval_input.setRange(10, 3600)
        self.interval_input.setValue(60)
        interval_layout.addWidget(self.interval_input)
        interval_layout.addStretch()
        form_layout.addLayout(interval_layout)

        group.setLayout(form_layout)
        layout.addWidget(group)
        layout.addStretch()

        # Save button
        btn_save = QPushButton("Save Settings")
        btn_save.clicked.connect(self.save_config)
        layout.addWidget(btn_save)

        return widget

    def create_rules_tab(self):
        """Tab cấu hình rules."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Rules table
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(4)
        self.rules_table.setHorizontalHeaderLabels(['Enabled', 'Rule Name', 'JQL', 'Actions'])
        self.rules_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.rules_table)

        # Add rule button
        btn_add = QPushButton("Add New Rule")
        btn_add.clicked.connect(self.add_rule_dialog)
        layout.addWidget(btn_add)

        # Examples
        examples = QGroupBox("JQL Examples")
        ex_layout = QVBoxLayout()
        ex_layout.addWidget(QLabel("• High priority unassigned: priority = High AND assignee is EMPTY"))
        ex_layout.addWidget(QLabel("• Project bugs: project = MYPROJ AND type = Bug AND status = Open"))
        ex_layout.addWidget(QLabel("• Assigned to me: assignee = currentUser() AND status != Done"))
        ex_layout.addWidget(QLabel("• Updated today: updated >= startOfDay()"))
        examples.setLayout(ex_layout)
        layout.addWidget(examples)

        return widget

    def create_tts_tab(self):
        """Tab cấu hình TTS."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Text-to-Speech Settings")
        form_layout = QVBoxLayout()

        # Language
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Language:"))
        self.tts_lang_combo = QComboBox()
        self.tts_lang_combo.addItems(['vi', 'en', 'ja', 'ko', 'zh-CN'])
        lang_layout.addWidget(self.tts_lang_combo)
        lang_layout.addStretch()
        form_layout.addLayout(lang_layout)

        # Speed
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed (1.0 = normal):"))
        self.tts_speed_input = QSpinBox()
        self.tts_speed_input.setRange(50, 300)
        self.tts_speed_input.setValue(150)
        self.tts_speed_input.setSuffix("%")
        speed_layout.addWidget(self.tts_speed_input)
        speed_layout.addStretch()
        form_layout.addLayout(speed_layout)

        # Template variables
        template_info = QGroupBox("Template Variables")
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel("{ticket_key} - Ticket ID (e.g., PROJ-123)"))
        info_layout.addWidget(QLabel("{summary} - Ticket summary"))
        info_layout.addWidget(QLabel("{priority} - Priority level"))
        info_layout.addWidget(QLabel("{status} - Current status"))
        info_layout.addWidget(QLabel("{assignee} - Assigned person"))
        template_info.setLayout(info_layout)
        form_layout.addWidget(template_info)

        group.setLayout(form_layout)
        layout.addWidget(group)
        layout.addStretch()

        btn_save = QPushButton("Save Settings")
        btn_save.clicked.connect(self.save_config)
        layout.addWidget(btn_save)

        return widget

    def create_log_tab(self):
        """Tab hiển thị logs."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)

        btn_clear = QPushButton("Clear Log")
        btn_clear.clicked.connect(lambda: self.log_display.clear())
        layout.addWidget(btn_clear)

        return widget

    def setup_tray(self):
        """Setup system tray icon."""
        self.tray_icon = QSystemTrayIcon(self)
        # self.tray_icon.setIcon(QIcon('icon.png'))  # Add icon if you have one

        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app)

        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def load_config(self):
        """Load config từ file."""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'jira_url': '',
            'jira_email': '',
            'jira_api_token': '',
            'check_interval': 60,
            'jira_enabled': False,
            'tts_lang': 'vi',
            'tts_speed': 1.5,
            'rules': []
        }

    def save_config(self):
        """Lưu config ra file."""
        self.config['jira_url'] = self.jira_url_input.text().strip()
        self.config['jira_email'] = self.jira_email_input.text().strip()
        self.config['jira_api_token'] = self.jira_token_input.text().strip()
        self.config['check_interval'] = self.interval_input.value()
        self.config['tts_lang'] = self.tts_lang_combo.currentText()
        self.config['tts_speed'] = self.tts_speed_input.value() / 100.0

        # Save rules from table
        rules = []
        for row in range(self.rules_table.rowCount()):
            enabled_widget = self.rules_table.cellWidget(row, 0)
            rule = {
                'enabled': enabled_widget.isChecked() if enabled_widget else False,
                'name': self.rules_table.item(row, 1).text() if self.rules_table.item(row, 1) else '',
                'jql': self.rules_table.item(row, 2).text() if self.rules_table.item(row, 2) else '',
                'tts_template': self.rules_table.item(row, 2).data(Qt.UserRole) or 'Cảnh báo: {ticket_key}, {summary}'
            }
            rules.append(rule)
        self.config['rules'] = rules

        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

        self.log("Settings saved")
        QMessageBox.information(self, "Success", "Settings saved successfully!")

    def load_ui_from_config(self):
        """Load config vào UI."""
        self.jira_url_input.setText(self.config.get('jira_url', ''))
        self.jira_email_input.setText(self.config.get('jira_email', ''))
        self.jira_token_input.setText(self.config.get('jira_api_token', ''))
        self.interval_input.setValue(self.config.get('check_interval', 60))

        # TTS settings
        lang_idx = self.tts_lang_combo.findText(self.config.get('tts_lang', 'vi'))
        if lang_idx >= 0:
            self.tts_lang_combo.setCurrentIndex(lang_idx)
        self.tts_speed_input.setValue(int(self.config.get('tts_speed', 1.5) * 100))

        # Load rules
        self.load_rules_to_table()

    def load_rules_to_table(self):
        """Load rules vào table."""
        rules = self.config.get('rules', [])
        self.rules_table.setRowCount(len(rules))

        for i, rule in enumerate(rules):
            # Enabled checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(rule.get('enabled', False))
            self.rules_table.setCellWidget(i, 0, checkbox)

            # Name
            self.rules_table.setItem(i, 1, QTableWidgetItem(rule.get('name', '')))

            # JQL
            jql_item = QTableWidgetItem(rule.get('jql', ''))
            jql_item.setData(Qt.UserRole, rule.get('tts_template'))  # Store template in UserRole
            self.rules_table.setItem(i, 2, jql_item)

            # Actions
            btn_edit = QPushButton("Edit")
            btn_edit.clicked.connect(lambda checked, row=i: self.edit_rule(row))
            self.rules_table.setCellWidget(i, 3, btn_edit)

    def add_rule_dialog(self):
        """Dialog thêm rule mới."""
        from PyQt5.QtWidgets import QDialog, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Rule")
        dialog.setGeometry(200, 200, 500, 400)

        layout = QVBoxLayout(dialog)

        # Rule name
        layout.addWidget(QLabel("Rule Name:"))
        name_input = QLineEdit()
        layout.addWidget(name_input)

        # JQL
        layout.addWidget(QLabel("JQL Query:"))
        jql_input = QTextEdit()
        jql_input.setPlaceholderText("e.g., project = MYPROJ AND status = Open")
        layout.addWidget(jql_input)

        # TTS Template
        layout.addWidget(QLabel("TTS Template:"))
        tts_input = QTextEdit()
        tts_input.setPlaceholderText("Cảnh báo: {ticket_key}, {summary}, priority {priority}")
        tts_input.setMaximumHeight(80)
        layout.addWidget(tts_input)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec_() == QDialog.Accepted:
            row = self.rules_table.rowCount()
            self.rules_table.insertRow(row)

            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.rules_table.setCellWidget(row, 0, checkbox)

            self.rules_table.setItem(row, 1, QTableWidgetItem(name_input.text()))

            jql_item = QTableWidgetItem(jql_input.toPlainText())
            jql_item.setData(Qt.UserRole, tts_input.toPlainText())
            self.rules_table.setItem(row, 2, jql_item)

            btn_edit = QPushButton("Edit")
            btn_edit.clicked.connect(lambda checked, r=row: self.edit_rule(r))
            self.rules_table.setCellWidget(row, 3, btn_edit)

            self.log(f"Rule added: {name_input.text()}")

    def edit_rule(self, row):
        """Edit existing rule."""
        # Similar to add_rule_dialog but pre-fill with existing data
        self.log(f"Edit rule at row {row}")

    def test_jira_connection(self):
        """Test kết nối Jira."""
        jira_url = self.jira_url_input.text().strip()
        email = self.jira_email_input.text().strip()
        token = self.jira_token_input.text().strip()

        if not all([jira_url, email, token]):
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return

        try:
            url = f"{jira_url}/rest/api/3/myself"
            auth = (email, token)
            response = requests.get(url, auth=auth, timeout=10)

            if response.status_code == 200:
                data = response.json()
                QMessageBox.information(
                    self, "Success",
                    f"Connected successfully!\nUser: {data.get('displayName')}"
                )
                self.log("Jira connection test: SUCCESS")
            else:
                QMessageBox.warning(
                    self, "Error",
                    f"Connection failed: {response.status_code}\n{response.text[:200]}"
                )
                self.log(f"Jira connection test: FAILED ({response.status_code})")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection error: {str(e)}")
            self.log(f"Jira connection test: ERROR - {e}")

    def start_monitoring(self):
        """Bắt đầu monitoring."""
        self.save_config()
        self.config['jira_enabled'] = True
        self.monitor_thread.set_config(self.config)
        self.monitor_thread.start()

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.status_label.setText("Status: Monitoring...")
        self.log("Monitoring started")

    def stop_monitoring(self):
        """Dừng monitoring."""
        self.config['jira_enabled'] = False
        self.monitor_thread.stop()
        self.monitor_thread.wait()

        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.status_label.setText("Status: Stopped")
        self.log("Monitoring stopped")

    def handle_alert(self, alert_data):
        """Xử lý alert: phát TTS."""
        try:
            # Build TTS text từ template
            template = alert_data.get('tts_template', 'Cảnh báo: {ticket_key}, {summary}')
            text = template.format(**alert_data)

            # Play TTS
            self.play_tts(text)

            # Log
            log_msg = f"ALERT: {alert_data['ticket_key']} - {alert_data['summary']}"
            self.log(log_msg)

            # Show notification
            self.tray_icon.showMessage(
                "Jira Alert",
                f"{alert_data['ticket_key']}: {alert_data['summary']}",
                QSystemTrayIcon.Warning,
                5000
            )

        except Exception as e:
            logger.error(f"handle_alert error: {e}")
            self.log(f"ERROR: {e}")

    def play_tts(self, text):
        """Phát TTS qua loa."""
        try:
            # Tạo file TTS tạm
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                audio_path = tmp.name

            lang = self.config.get('tts_lang', 'vi')
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(audio_path)

            # Play với system command
            system = platform.system()
            if system == 'Windows':
                # Windows: dùng built-in player
                os.startfile(audio_path)
            elif system == 'Darwin':  # macOS
                subprocess.call(['afplay', audio_path])
            else:  # Linux
                subprocess.call(['mpg123', audio_path])

            # Wait a bit then cleanup
            import time
            time.sleep(5)  # Đợi file phát xong
            try:
                os.remove(audio_path)
            except:
                pass  # File đang được dùng, bỏ qua

        except Exception as e:
            logger.error(f"play_tts error: {e}")

    def test_alert(self):
        """Test phát alert."""
        test_data = {
            'rule_name': 'Test Rule',
            'ticket_key': 'TEST-123',
            'summary': 'This is a test alert',
            'status': 'Open',
            'priority': 'High',
            'assignee': 'John Doe',
            'tts_template': 'Cảnh báo test: {ticket_key}, {summary}, priority {priority}',
            'url': 'https://jira.example.com/browse/TEST-123'
        }
        self.handle_alert(test_data)

    def update_status(self, status_text):
        """Update status label."""
        self.status_label.setText(f"Status: {status_text}")

    def log(self, message):
        """Thêm log vào display."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_display.append(f"[{timestamp}] {message}")
        logger.info(message)

    def tray_icon_activated(self, reason):
        """Xử lý click vào tray icon."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    def closeEvent(self, event):
        """Override close event để minimize to tray."""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Jira Alert Monitor",
            "Application minimized to tray",
            QSystemTrayIcon.Information,
            2000
        )

    def quit_app(self):
        """Thoát app."""
        self.stop_monitoring()
        QApplication.quit()


def main():
    """Main entry point."""
    # Tạo thư mục cần thiết
    Path('config').mkdir(exist_ok=True)
    Path('logs').mkdir(exist_ok=True)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Không thoát khi đóng window

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
