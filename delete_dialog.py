import sys
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from mongodb import DBOps

db = DBOps()


class DeleteAgentDialog(QDialog):
    """Modal confirmation dialog for deleting an agent."""

    def __init__(self, agent_name: str = "", parent=None):
        super().__init__(parent)
        self.agent_name = agent_name
        self.setWindowTitle("Delete Agent")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._apply_style()
        self._build_ui(agent_name)

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

            QLabel#icon-label {
                font-size: 40px;
            }

            QLabel#form-title {
                font-size: 20px;
                font-weight: 700;
                color: #f1f5f9;
            }

            QLabel#form-subtitle {
                font-size: 13px;
                color: #94a3b8;
                line-height: 1.5;
            }

            QLabel#agent-name-badge {
                font-size: 13px;
                font-weight: 700;
                color: #fca5a5;
                background-color: #7f1d1d33;
                border: 1px solid #dc262644;
                border-radius: 8px;
                padding: 8px 16px;
            }

            QLabel#warning-note {
                font-size: 11px;
                color: #64748b;
            }

            QFrame#sep {
                background-color: #1e293b;
                max-height: 1px;
                min-height: 1px;
            }

            QPushButton#btn-delete {
                background-color: #dc2626;
                color: #ffffff;
                border: none;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 600;
                padding: 10px 28px;
            }
            QPushButton#btn-delete:hover {
                background-color: #ef4444;
            }
            QPushButton#btn-delete:pressed {
                background-color: #b91c1c;
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
    def _build_ui(self, agent_name: str):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(0)

        # --- Warning icon ---
        icon_label = QLabel("⚠️")
        icon_label.setObjectName("icon-label")
        icon_label.setAlignment(Qt.AlignCenter)
        root.addWidget(icon_label)
        root.addSpacing(14)

        # --- Title ---
        title = QLabel("Delete Agent")
        title.setObjectName("form-title")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)
        root.addSpacing(8)

        # --- Subtitle ---
        subtitle = QLabel("You are about to permanently delete the following agent:")
        subtitle.setObjectName("form-subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)
        root.addSpacing(16)

        # --- Agent name badge ---
        name_badge = QLabel(agent_name)
        name_badge.setObjectName("agent-name-badge")
        name_badge.setAlignment(Qt.AlignCenter)
        root.addWidget(name_badge)
        root.addSpacing(14)

        # --- Warning note ---
        warning = QLabel("This action cannot be undone.")
        warning.setObjectName("warning-note")
        warning.setAlignment(Qt.AlignCenter)
        root.addWidget(warning)
        root.addSpacing(24)

        # --- Separator ---
        sep = QFrame()
        sep.setObjectName("sep")
        root.addWidget(sep)
        root.addSpacing(24)

        # --- Buttons ---
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("btn-cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(self.reject)

        delete_btn = QPushButton("Delete Agent")
        delete_btn.setObjectName("btn-delete")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setFixedHeight(40)
        delete_btn.clicked.connect(self.accept)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(delete_btn)
        root.addLayout(btn_row)


# ------------------------------------------------------------------ #
#  Public helper                                                       #
# ------------------------------------------------------------------ #
def open_delete_dialog(agent_name: str) -> bool:
    """
    Opens the delete confirmation dialog.
    Returns True if the user confirmed deletion, False otherwise.
    Deletion from DB is handled here.
    """
    dialog = DeleteAgentDialog(agent_name=agent_name)
    if dialog.exec() == QDialog.Accepted:
        db.delete_document({"name": agent_name})
        return True
    return False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    result = open_delete_dialog("TestAgent")
    print("Deleted:" if result else "Cancelled.")
    sys.exit(0)
