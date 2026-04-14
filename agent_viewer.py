import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QLabel, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from modify_description import open_dialog
from mongodb import DBOps
from delete_dialog import open_delete_dialog
import shutil
db = DBOps()
SAMPLE_AGENTS = []
STATUS_COLORS = {
    "Active":   "#4ade80",   # green
    "Inactive":      "#94a3b8",   # slate
}



class AgentViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agent Viewer")
        self.setMinimumSize(900, 580)
        self._apply_dark_theme()
        self._build_ui()

    # ------------------------------------------------------------------ #
    #  Theme                                                               #
    # ------------------------------------------------------------------ #
    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0f1117;
                color: #e2e8f0;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }

            QLabel#title {
                font-size: 22px;
                font-weight: 700;
                color: #f1f5f9;
                letter-spacing: 0.5px;
            }

            QLabel#subtitle {
                font-size: 13px;
                color: #64748b;
            }

            QFrame#header-separator {
                background-color: #1e293b;
                max-height: 1px;
                min-height: 1px;
            }

            QTableWidget {
                background-color: #141820;
                border: 1px solid #1e293b;
                border-radius: 10px;
                gridline-color: #1e293b;
                outline: none;
                font-size: 13px;
            }

            QTableWidget::item {
                padding: 10px 14px;
                border: none;
                color: #cbd5e1;
            }

            QTableWidget::item:selected {
                background-color: #1e3a5f;
                color: #e2e8f0;
            }

            QHeaderView::section {
                background-color: #1a2030;
                color: #64748b;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
                padding: 10px 14px;
                border: none;
                border-bottom: 1px solid #1e293b;
            }

            QScrollBar:vertical {
                background: #141820;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    # ------------------------------------------------------------------ #
    #  UI Construction                                                     #
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(30, 28, 30, 28)
        layout.setSpacing(0)

        # --- Header ---
        header_row = QHBoxLayout()
        header_row.setSpacing(0)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        title = QLabel("Agent Viewer")
        title.setObjectName("title")

        subtitle = QLabel("Monitor and manage all active agents")
        subtitle.setObjectName("subtitle")

        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_row.addLayout(title_col)
        header_row.addStretch()

        layout.addLayout(header_row)
        layout.addSpacing(18)

        # Separator
        sep = QFrame()
        sep.setObjectName("header-separator")
        layout.addWidget(sep)
        layout.addSpacing(20)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Agent Name", "Task", "Status", "Action"])
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setAlternatingRowColors(False)

        # Column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(2, 160)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 220)

        self._populate_table(SAMPLE_AGENTS)
        layout.addWidget(self.table)

        # --- Footer ---
        layout.addSpacing(16)
        footer = QLabel(f"{len(SAMPLE_AGENTS)} agents loaded")
        footer.setObjectName("subtitle")
        footer.setAlignment(Qt.AlignRight)
        layout.addWidget(footer)

    # ------------------------------------------------------------------ #
    #  Table population                                                    #
    # ------------------------------------------------------------------ #
    def _populate_table(self, agents: list[dict]):
        self.table.setRowCount(len(agents))
        self.table.verticalHeader().setDefaultSectionSize(65)

        for row, agent in enumerate(agents):
            # Name
            name_item = QTableWidgetItem(agent["name"])
            name_item.setFont(QFont("Segoe UI", 13, QFont.Medium))
            self.table.setItem(row, 0, name_item)

            # Task
            task_item = QTableWidgetItem(agent["task"])
            self.table.setItem(row, 1, task_item)

            # Status badge (widget inside a cell)
            status = agent["status"]
            status_label = QLabel(status)
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setMinimumWidth(120)
            color = STATUS_COLORS.get(status, "#94a3b8")
            status_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {color}22;
                    color: {color};
                    border: 1px solid {color}66;
                    border-radius: 6px;
                    padding: 3px 12px;
                    font-size: 12px;
                    font-weight: 600;
                }}
            """)
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.setContentsMargins(10, 6, 10, 6)
            cell_layout.addStretch()
            cell_layout.addWidget(status_label)
            cell_layout.addStretch()
            self.table.setCellWidget(row, 2, cell_widget)

            # Modify button
            modify_btn = QPushButton("Modify")
            modify_btn.setFixedHeight(34)
            modify_btn.setMinimumWidth(90)
            modify_btn.setCursor(Qt.PointingHandCursor)
            modify_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1e40af;
                    color: #bfdbfe;
                    border: 1px solid #2563eb;
                    border-radius: 17px;
                    font-size: 12px;
                    font-weight: 600;
                    padding: 0 16px;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                    color: #ffffff;
                    border-color: #60a5fa;
                }
                QPushButton:pressed {
                    background-color: #1d4ed8;
                }
            """)
            def on_modify_click(agent):
                if(open_dialog(agent["name"], agent["task"])):
                    agents = db.find_documents({})
                    SAMPLE_AGENTS = []
                    for agent in agents:
                        SAMPLE_AGENTS.append({"name": agent["name"], "task": agent["action"], "status": agent["status"]})
                    self.table.setRowCount(0)
                    self._populate_table(SAMPLE_AGENTS)

            modify_btn.clicked.connect(lambda checked, a=agent: on_modify_click(a))

            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.setFixedHeight(34)
            delete_btn.setMinimumWidth(90)
            delete_btn.setCursor(Qt.PointingHandCursor)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #7f1d1d;
                    color: #fca5a5;
                    border: 1px solid #dc2626;
                    border-radius: 17px;
                    font-size: 12px;
                    font-weight: 600;
                    padding: 0 16px;
                }
                QPushButton:hover {
                    background-color: #dc2626;
                    color: #ffffff;
                    border-color: #f87171;
                }
                QPushButton:pressed {
                    background-color: #b91c1c;
                }
            """)
            def on_delete_click(agent):
                if(open_delete_dialog(agent["name"])):
                    refreshed = db.find_documents({})
                    updated_agents = [
                        {"name": a["name"], "task": a["action"], "status": a["status"]}
                        for a in refreshed
                    ]
                    self.table.setRowCount(0)
                    self._populate_table(updated_agents)
                    shutil.rmtree(f"{agent['name']}")
                else:
                    print("Cancelled")

            delete_btn.clicked.connect(lambda checked, a=agent: on_delete_click(a))

            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(8, 8, 8, 8)
            btn_layout.setSpacing(16)
            btn_layout.addStretch()
            btn_layout.addWidget(modify_btn)
            btn_layout.addWidget(delete_btn)
            btn_layout.addStretch()
            self.table.setCellWidget(row, 3, btn_container)

    # ------------------------------------------------------------------ #
    #  Slot                                                                #
    # ------------------------------------------------------------------ #
    def _on_modify(self, row: int):
        # Placeholder – does nothing for now
        pass


# ------------------------------------------------------------------ #
#  Entry point                                                         #
# ------------------------------------------------------------------ #
def main():
    agents = db.find_documents({})
    global SAMPLE_AGENTS
    SAMPLE_AGENTS = []
    for agent in agents:
        SAMPLE_AGENTS.append({"name": agent["name"], "task": agent["action"], "status": agent["status"]})
    global STATUS_COLORS
    STATUS_COLORS = {
    "Active":   "#4ade80",   # green
    "Inactive":      "#94a3b8",   # slate
    }
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = AgentViewer()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
