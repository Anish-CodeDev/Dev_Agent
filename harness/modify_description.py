import sys
from PySide6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from mongodb import DBOps
db = DBOps()

class ModifyAgentDialog(QDialog):
    """Modal form dialog for editing an agent's name and task."""

    def __init__(self, agent_name: str = "", agent_task: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modify Agent")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._apply_style()
        self._build_ui(agent_name, agent_task)

    # ------------------------------------------------------------------ #
    #  Theme                                                               #
    # ------------------------------------------------------------------ #
    def _apply_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0f1117;
                color: #e2e8f0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }

            /* ---- labels ---- */
            QLabel#form-title {
                font-size: 20px;
                font-weight: 700;
                color: #f1f5f9;
            }
            QLabel#form-subtitle {
                font-size: 12px;
                color: #64748b;
            }
            QLabel.field-label {
                font-size: 12px;
                font-weight: 600;
                color: #94a3b8;
                letter-spacing: 0.5px;
            }

            /* ---- inputs ---- */
            QLineEdit, QTextEdit {
                background-color: #141820;
                color: #e2e8f0;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
                selection-background-color: #2563eb;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #3b82f6;
                background-color: #1a2030;
            }
            QLineEdit::placeholder-text, QTextEdit::placeholder-text {
                color: #334155;
            }

            /* ---- separator ---- */
            QFrame#sep {
                background-color: #1e293b;
                max-height: 1px;
                min-height: 1px;
            }

            /* ---- buttons ---- */
            QPushButton#btn-save {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 600;
                padding: 10px 28px;
            }
            QPushButton#btn-save:hover {
                background-color: #3b82f6;
            }
            QPushButton#btn-save:pressed {
                background-color: #1d4ed8;
            }

            QPushButton#btn-cancel {
                background-color: transparent;
                color: #64748b;
                border: 1px solid #1e293b;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 600;
                padding: 10px 28px;
            }
            QPushButton#btn-cancel:hover {
                background-color: #1e293b;
                color: #e2e8f0;
            }
            QPushButton#btn-cancel:pressed {
                background-color: #0f172a;
            }
        """)

    # ------------------------------------------------------------------ #
    #  UI Construction                                                     #
    # ------------------------------------------------------------------ #
    def _build_ui(self, agent_name: str, agent_task: str):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(0)

        # --- Header ---
        title = QLabel("Modify Agent")
        title.setObjectName("form-title")

        subtitle = QLabel("Update the agent's name and task description below.")
        subtitle.setObjectName("form-subtitle")
        subtitle.setWordWrap(True)

        root.addWidget(title)
        root.addSpacing(4)
        root.addWidget(subtitle)
        root.addSpacing(22)

        # Separator
        sep = QFrame()
        sep.setObjectName("sep")
        root.addWidget(sep)
        root.addSpacing(22)

        # --- Name field ---
        name_label = QLabel("AGENT NAME")
        name_label.setProperty("class", "field-label")
        name_label.setStyleSheet("font-size:11px; font-weight:600; color:#64748b; letter-spacing:1px;")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. CodeAgent")
        self.name_input.setText(agent_name)
        self.name_input.setFixedHeight(44)

        root.addWidget(name_label)
        root.addSpacing(6)
        root.addWidget(self.name_input)
        root.addSpacing(18)

        # --- Task field ---
        task_label = QLabel("TASK")
        task_label.setStyleSheet("font-size:11px; font-weight:600; color:#64748b; letter-spacing:1px;")

        self.task_input = QTextEdit()
        self.task_input.setPlaceholderText("Describe what this agent should do…")
        self.task_input.setText(agent_task)
        self.task_input.setFixedHeight(110)
        self.task_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root.addWidget(task_label)
        root.addSpacing(6)
        root.addWidget(self.task_input)
        root.addSpacing(28)

        # --- Buttons ---
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("btn-cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Changes")
        save_btn.setObjectName("btn-save")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setFixedHeight(40)
        save_btn.clicked.connect(self._on_save)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        root.addLayout(btn_row)

    # ------------------------------------------------------------------ #
    #  Slots                                                               #
    # ------------------------------------------------------------------ #
    def _on_save(self):
        """Validate and accept the dialog."""
        name = self.name_input.text().strip()
        task = self.task_input.toPlainText().strip()

        # Basic validation — highlight empty fields
        if not name:
            self.name_input.setStyleSheet(
                self.name_input.styleSheet() +
                "QLineEdit { border: 1px solid #ef4444; }"
            )
            return
        if not task:
            self.task_input.setStyleSheet(
                self.task_input.styleSheet() +
                "QTextEdit { border: 1px solid #ef4444; }"
            )
            return

        self.accept()

    def get_values(self) -> dict:
        """Call after exec() returns Accepted to retrieve the form data."""
        return {
            "name": self.name_input.text().strip(),
            "task": self.task_input.toPlainText().strip(),
        }


# ------------------------------------------------------------------ #
#  Entry point (standalone preview)                                    #
# ------------------------------------------------------------------ #
def open_dialog(agent_name, agent_task):
    #app = QApplication(sys.argv)
    #app.setStyle("Fusion")

    dialog = ModifyAgentDialog(
        agent_name=agent_name,
        agent_task=agent_task,
    )
    if dialog.exec() == QDialog.Accepted:
        print("Saved:", dialog.get_values())
        res = dialog.get_values()
        task = res['task']
        db.update_document({'name':agent_name},{'$set':{'action':task}})
        return True
    else:
        print("Cancelled.")
        return False

    #sys.exit(0)


if __name__ == "__main__":
    open_dialog()
