APP_STYLESHEET = """
QWidget {
    background-color: #eef4f3;
    color: #102a2c;
    font-family: "Segoe UI";
    font-size: 12pt;
}

/* Etiketler bulunduklari kartin rengini alsin; aksi halde arkalarinda gri kutu cikar. */
QLabel {
    background: transparent;
}

QLabel#BrandLabel {
    color: #0f766e;
    font-size: 15pt;
    font-weight: 700;
}

QLabel#BrandSubtitle {
    color: #6c8481;
    font-size: 9pt;
}

QWidget#RootPanel {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #f8fbfb,
        stop: 1 #e4efee
    );
    border: 1px solid #d3e3e1;
    border-radius: 22px;
}

QTextEdit {
    background-color: #ffffff;
    border: 1px solid #c4d7d5;
    border-radius: 18px;
    padding: 16px;
    selection-background-color: #0f766e;
    selection-color: #ffffff;
}

QTextEdit:focus {
    border: 2px solid #0f766e;
}

QPushButton {
    background-color: #ffffff;
    border: 1px solid #c4d7d5;
    border-radius: 14px;
    min-height: 44px;
    min-width: 132px;
    padding: 0 18px;
}

QPushButton:hover {
    background-color: #f4fbfa;
}

QPushButton:pressed {
    background-color: #e0f0ed;
}

QPushButton#PrimaryButton {
    background-color: #0f766e;
    border-color: #0f766e;
    color: #ffffff;
    font-weight: 600;
}

QPushButton#PrimaryButton:hover {
    background-color: #115e59;
}

QPushButton#PrimaryButton:pressed {
    background-color: #134e4a;
}

QPushButton:disabled {
    background-color: #d7e6e4;
    color: #6c8481;
    border-color: #d7e6e4;
}

QPushButton#UpdateButton {
    background-color: #fff7ed;
    border: 1px solid #f59e0b;
    color: #9a3412;
    min-height: 32px;
    min-width: 0;
    border-radius: 12px;
    font-size: 10pt;
    font-weight: 600;
    padding: 0 14px;
}

QPushButton#UpdateButton:hover {
    background-color: #ffedd5;
}

QPushButton#UpdateButton:disabled {
    background-color: #fef3c7;
    color: #92400e;
    border-color: #fcd34d;
}

QLabel#StatusLabel {
    color: #486463;
    font-size: 10pt;
}

QFrame#SpeedCard {
    background-color: rgba(255, 255, 255, 0.82);
    border: 1px solid #d6e5e3;
    border-radius: 18px;
}

QLabel#SectionLabel {
    color: #234244;
    font-size: 11pt;
    font-weight: 600;
    background: transparent;
}

QLabel#SpeedValueLabel {
    color: #0f766e;
    font-size: 10pt;
    font-weight: 600;
    background: transparent;
}

QPushButton#IconButton {
    background-color: #ffffff;
    border: 1px solid #c4d7d5;
    border-radius: 17px;
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
    padding: 0;
}

QPushButton#IconButton:hover {
    background-color: #e0f0ed;
    border-color: #0f766e;
}

QPushButton#IconButton:disabled {
    background-color: #eef4f3;
    border-color: #d7e6e4;
}

QLabel#UpdateStatusLabel {
    color: #6c8481;
    font-size: 9pt;
}

QLabel#UpdateStatusLabel[state="up_to_date"] {
    color: #0f766e;
    font-weight: 600;
}

QLabel#UpdateStatusLabel[state="failed"] {
    color: #b45309;
}

QLabel#FieldLabel {
    color: #486463;
    font-size: 9pt;
    font-weight: 600;
    background: transparent;
}

QLabel#HintLabel {
    color: #6c8481;
    font-size: 9pt;
    background: transparent;
}

QFrame#Divider {
    background-color: #dbe8e6;
    border: none;
}

QComboBox {
    background-color: #ffffff;
    border: 1px solid #c4d7d5;
    border-radius: 10px;
    padding: 4px 10px;
    min-height: 26px;
    font-size: 10pt;
}

QComboBox:disabled {
    color: #6c8481;
    background-color: #eef4f3;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    selection-background-color: #0f766e;
    selection-color: #ffffff;
}

QCheckBox {
    spacing: 10px;
    font-size: 10pt;
    background: transparent;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #93b6b1;
    border-radius: 5px;
    background: #ffffff;
}

QCheckBox::indicator:checked {
    background: #0f766e;
    border-color: #0f766e;
}

QSlider::groove:horizontal {
    border: none;
    height: 8px;
    background: #d5e5e3;
    border-radius: 4px;
}

QSlider::sub-page:horizontal {
    background: #0f766e;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 2px solid #0f766e;
    width: 18px;
    margin: -6px 0;
    border-radius: 9px;
}

QWidget#CountdownCard {
    background-color: rgba(15, 23, 42, 230);
    border: 1px solid rgba(148, 163, 184, 80);
    border-radius: 22px;
}

QLabel#CountdownTitle {
    background: transparent;
    color: #e2e8f0;
    font-size: 11pt;
    font-weight: 600;
}

QLabel#CountdownNumber {
    background: transparent;
    color: #ffffff;
    font-size: 32pt;
    font-weight: 700;
}
"""

