# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Fakrul Islam
"""Scholia - lecture PDF on one side, your own notes for each page on the other.

Run:       python3 Scholia.py
Build app: pyinstaller --windowed --noconfirm --name "Scholia" --icon assets/Scholia.icns Scholia.py

Notes are saved automatically in a folder next to each PDF: <pdfname>_notes/
"""
import json
import math
import sys
import uuid
from collections import OrderedDict
from pathlib import Path
from string import Template

from PySide6.QtCore import QByteArray, QPointF, QRect, QRectF, QSettings, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import (
    QAction, QBrush, QColor, QDesktopServices, QFont, QFontMetrics, QIcon, QImage,
    QIntValidator, QKeySequence, QPainter, QPalette, QPixmap, QShortcut, QTextBlockFormat,
    QTextCharFormat, QTextCursor, QTextImageFormat, QTextListFormat,
)
from PySide6.QtPdf import QPdfDocument
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox, QPushButton,
    QScrollArea, QSizePolicy, QSplitter, QStackedWidget, QStyle, QStyledItemDelegate,
    QTextEdit, QToolBar, QToolButton, QVBoxLayout, QWidget,
)

__version__ = "1.0.0"

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
BODY_SIZE, HEADING_SIZE, TITLE_SIZE = 14, 18, 24
HIGHLIGHT = QColor(250, 204, 21, 110)  # semi-transparent: readable in light and dark

# ---------------------------------------------------------------- icons ----
ICONS = {
    "plus": '<path d="M5 12h14"/><path d="M12 5v14"/>',
    "trash": '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>'
             '<path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    "left": '<path d="m15 18-6-6 6-6"/>',
    "right": '<path d="m9 18 6-6-6-6"/>',
    "zoom-in": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/><path d="M11 8v6"/><path d="M8 11h6"/>',
    "zoom-out": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/><path d="M8 11h6"/>',
    "fit": '<path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/>'
           '<path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/>',
    "sidebar": '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18"/>',
    "undo": '<path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11"/>',
    "redo": '<path d="m15 14 5-5-5-5"/><path d="M20 9H9.5A5.5 5.5 0 0 0 4 14.5A5.5 5.5 0 0 0 9.5 20H13"/>',
    "bold": '<path d="M6 12h9a4 4 0 0 1 0 8H7a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h7a4 4 0 0 1 0 8"/>',
    "highlight": '<path d="m9 11-6 6v3h9l3-3"/><path d="m22 12-4.6 4.6a2 2 0 0 1-2.8 0l-5.2-5.2a2 2 0 0 1 0-2.8L14 4"/>',
    "list": '<path d="M8 6h13"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M3 6h.01"/>'
            '<path d="M3 12h.01"/><path d="M3 18h.01"/>',
    "list-ordered": '<path d="M10 6h11"/><path d="M10 12h11"/><path d="M10 18h11"/><path d="M4 6h1v4"/>'
                    '<path d="M4 10h2"/><path d="M6 18H4c0-1 2-2 2-3s-1-1.5-2-1"/>',
    "h1": '<path d="M4 12h8"/><path d="M4 18V6"/><path d="M12 18V6"/><path d="m17 12 3-2v8"/>',
    "h2": '<path d="M4 12h8"/><path d="M4 18V6"/><path d="M12 18V6"/><path d="M21 18h-4c0-4 4-3 4-6 0-1.5-2-2.5-4-1"/>',
    "text": '<path d="M12 4v16"/><path d="M4 7V5a1 1 0 0 1 1-1h14a1 1 0 0 1 1 1v2"/><path d="M9 20h6"/>',
    "image": '<path d="M16 5h6"/><path d="M19 2v6"/><path d="M21 11.5V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7.5"/>'
             '<path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/><circle cx="9" cy="9" r="2"/>',
    "book": '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    "copy": '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>'
            '<path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
    "quote": '<path d="M16 3a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2 1 1 0 0 1 1 1v1a2 2 0 0 1-2 2 1 1 0 0 0-1 1v2a1 1 0 0 0 1 1 6 6 0 0 0 6-6V5a2 2 0 0 0-2-2z"/>'
             '<path d="M5 3a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2 1 1 0 0 1 1 1v1a2 2 0 0 1-2 2 1 1 0 0 0-1 1v2a1 1 0 0 0 1 1 6 6 0 0 0 6-6V5a2 2 0 0 0-2-2z"/>',
    "moon": '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/>'
           '<path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/>'
           '<path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
}


def make_pixmap(name, color, size=20, width=2.0):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
           f'fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" '
           f'stroke-linejoin="round">{ICONS[name]}</svg>')
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    ratio = 3
    pm = QPixmap(size * ratio, size * ratio)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    renderer.render(painter)
    painter.end()
    pm.setDevicePixelRatio(ratio)
    return pm


def make_icon(name, color, size=20):
    return QIcon(make_pixmap(name, color, size))


# --------------------------------------------------------------- themes ----
LIGHT = dict(
    bg="#f3f4f7", panel="#ffffff", border="#e4e7ec", text="#1f2328", muted="#6b7280",
    accent="#4f6bed", accent_hover="#3f58d4", accent_soft="#e6ebfd", hover="#eceef2",
    pdf_bg="#e7e9ee", scroll="#c5cad3", icon="#4b5563",
)
DARK = dict(
    bg="#15171b", panel="#1c1f24", border="#2b3037", text="#e6e8eb", muted="#98a0ab",
    accent="#7b93ff", accent_hover="#93a6ff", accent_soft="#29325a", hover="#272b32",
    pdf_bg="#101215", scroll="#3a404a", icon="#c3c9d2",
)

QSS = Template("""
QMainWindow, QDialog { background: $bg; }
QWidget#sidebar, QWidget#notesPane { background: $panel; }
QWidget#pdfPane, QWidget#emptyState { background: $bg; }
QLabel { color: $text; background: transparent; }
QLabel#brand { font-size: 17px; font-weight: 700; }
QLabel#pageTitle { font-size: 15px; font-weight: 600; }
QLabel#status, QLabel#muted { color: $muted; font-size: 12px; }
QLabel#emptyTitle { font-size: 22px; font-weight: 700; }
QLabel#emptySub { color: $muted; font-size: 14px; }
QToolBar { background: transparent; border: none; spacing: 2px; padding: 4px 8px; }
QToolBar::separator { background: $border; width: 1px; margin: 7px 6px; }
QToolButton { background: transparent; border: none; border-radius: 7px; padding: 6px; }
QToolButton:hover { background: $hover; }
QToolButton:checked { background: $accent_soft; }
QToolButton:pressed { background: $border; }
QPushButton#primary { background: $accent; color: white; border: none; border-radius: 9px;
                      padding: 9px 16px; font-weight: 600; font-size: 13px; }
QPushButton#primary:hover { background: $accent_hover; }
QListWidget { background: transparent; border: none; outline: none; }
QTextEdit { background: $panel; color: $text; border: none; padding: 14px 26px;
            selection-background-color: $accent_soft; selection-color: $text; }
QLineEdit { background: $panel; color: $text; border: 1px solid $border; border-radius: 7px;
            padding: 3px 4px; }
QLineEdit:focus { border: 1px solid $accent; }
QSplitter::handle { background: $border; }
QSplitter::handle:hover { background: $accent; }
QScrollBar:vertical { background: transparent; width: 11px; margin: 0; }
QScrollBar::handle:vertical { background: $scroll; border-radius: 4px; min-height: 36px; margin: 2px; }
QScrollBar:horizontal { background: transparent; height: 11px; margin: 0; }
QScrollBar::handle:horizontal { background: $scroll; border-radius: 4px; min-width: 36px; margin: 2px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: none; }
QMenu { background: $panel; color: $text; border: 1px solid $border; border-radius: 8px; padding: 5px; }
QMenu::item { padding: 6px 18px; border-radius: 5px; }
QMenu::item:selected { background: $accent_soft; }
QFrame#selBar { background: $panel; border: 1px solid $border; border-radius: 12px; }
QToolTip { background: $panel; color: $text; border: 1px solid $border; padding: 4px 7px; }
""")


def make_palette(t):
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(t["bg"]))
    p.setColor(QPalette.ColorRole.WindowText, QColor(t["text"]))
    p.setColor(QPalette.ColorRole.Base, QColor(t["panel"]))
    p.setColor(QPalette.ColorRole.AlternateBase, QColor(t["bg"]))
    p.setColor(QPalette.ColorRole.Text, QColor(t["text"]))
    p.setColor(QPalette.ColorRole.Button, QColor(t["panel"]))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(t["text"]))
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(t["panel"]))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor(t["text"]))
    p.setColor(QPalette.ColorRole.Highlight, QColor(t["accent"]))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor(t["muted"]))
    return p


# ------------------------------------------------------ library list item ----
ROLE_PATH = Qt.ItemDataRole.UserRole
ROLE_SUB = Qt.ItemDataRole.UserRole + 1
ROLE_MISSING = Qt.ItemDataRole.UserRole + 2


class LibraryDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = LIGHT

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 56)

    def paint(self, painter, option, index):
        t = self.theme
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = option.rect.adjusted(8, 2, -8, -2)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hover = bool(option.state & QStyle.StateFlag.State_MouseOver)
        if selected or hover:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(t["accent_soft"] if selected else t["hover"]))
            painter.drawRoundedRect(rect, 9, 9)
        if selected:
            painter.setBrush(QColor(t["accent"]))
            painter.drawRoundedRect(QRect(rect.left(), rect.top() + 10, 3, rect.height() - 20), 1.5, 1.5)

        missing = bool(index.data(ROLE_MISSING))
        width = rect.width() - 28
        title_font = QFont(option.font)
        title_font.setPixelSize(14)
        title_font.setWeight(QFont.Weight.DemiBold if selected else QFont.Weight.Medium)
        painter.setFont(title_font)
        painter.setPen(QColor(t["muted"] if missing else (t["accent"] if selected else t["text"])))
        title = QFontMetrics(title_font).elidedText(index.data(Qt.ItemDataRole.DisplayRole) or "",
                                                    Qt.TextElideMode.ElideRight, width)
        painter.drawText(QRect(rect.left() + 14, rect.top() + 8, width, 20),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title)

        sub_font = QFont(option.font)
        sub_font.setPixelSize(12)
        painter.setFont(sub_font)
        painter.setPen(QColor(t["muted"]))
        sub = QFontMetrics(sub_font).elidedText(index.data(ROLE_SUB) or "",
                                                Qt.TextElideMode.ElideRight, width)
        painter.drawText(QRect(rect.left() + 14, rect.top() + 28, width, 18),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, sub)
        painter.restore()


HIGHLIGHT_COLORS = ["#fde047", "#86efac", "#f9a8d4", "#93c5fd"]  # yellow, green, pink, blue


class SelectionBar(QFrame):
    """Floating toolbar shown after selecting PDF text or clicking a highlight."""

    colorChosen = Signal(str)
    copyRequested = Signal()
    quoteRequested = Signal()
    deleteRequested = Signal()

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("selBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(5)
        for color in HIGHLIGHT_COLORS:
            btn = QToolButton()
            btn.setFixedSize(22, 22)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip("Highlight")
            btn.setStyleSheet(
                f"QToolButton {{ background: {color}; border: 2px solid rgba(0,0,0,45);"
                f" border-radius: 11px; padding: 0; }}"
                f" QToolButton:hover {{ border: 2px solid rgba(0,0,0,140); }}")
            btn.clicked.connect(lambda _=False, c=color: self.colorChosen.emit(c))
            layout.addWidget(btn)
        layout.addSpacing(4)
        self.buttons = {}
        for name, tip, signal in (("copy", "Copy text", self.copyRequested),
                                  ("quote", "Add to notes", self.quoteRequested),
                                  ("trash", "Remove highlight", self.deleteRequested)):
            btn = QToolButton()
            btn.setToolTip(tip)
            btn.setIconSize(QSize(18, 18))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, sig=signal: sig.emit())
            layout.addWidget(btn)
            self.buttons[name] = btn
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 90))
        self.setGraphicsEffect(shadow)
        self.hide()

    def set_mode(self, on_highlight):
        self.buttons["trash"].setVisible(on_highlight)

    def apply_theme(self, color):
        for name, btn in self.buttons.items():
            btn.setIcon(make_icon(name, color))


class PdfCanvas(QWidget):
    """Draws every PDF page, the text selection and the saved highlights."""

    MARGIN, GAP = 16, 14

    def __init__(self, view):
        super().__init__(view)
        self.view = view
        self.doc = view.doc
        self.sizes = []
        self.rects = []
        self.scale = 1.0
        self.cache = OrderedDict()
        self.char_cache = {}
        self.highlights = {}   # page -> [{"rects": [[x, y, w, h]], "color": "#rrggbb", "text": "..."}]
        self.selection = None  # {"page", "start", "end", "rects", "text"}
        self.active = None     # (page, index) of the highlight that was clicked
        self.anchor = None
        self.press_pos = None
        self.dragging = False
        self.bg = QColor("#e7e9ee")
        self.bar = SelectionBar(self)
        self.bar.colorChosen.connect(self.apply_color)
        self.bar.copyRequested.connect(self.copy_text)
        self.bar.quoteRequested.connect(lambda: self.view.quoteRequested.emit(self.current_text()))
        self.bar.deleteRequested.connect(self.delete_active)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.IBeamCursor)

    # ----- document / layout -----
    def reset(self):
        self.sizes = [self.doc.pagePointSize(i) for i in range(self.doc.pageCount())]
        self.rects = []
        self.cache.clear()
        self.char_cache.clear()
        self.highlights = {}
        self.clear_selection()

    def layout_pages(self, vp_w, vp_h, scale):
        self.scale = scale
        widest = max((s.width() for s in self.sizes), default=0) * scale
        width = max(vp_w, widest + 2 * self.MARGIN)
        y = self.MARGIN
        rects = []
        for size in self.sizes:
            w, h = size.width() * scale, size.height() * scale
            rects.append(QRectF((width - w) / 2, y, w, h))
            y += h + self.GAP
        self.rects = rects
        height = max(vp_h, y - self.GAP + self.MARGIN)
        self.resize(int(math.ceil(width)), int(math.ceil(height)))
        self.update()

    def to_widget(self, page, x, y, w, h):
        r, s = self.rects[page], self.scale
        return QRectF(r.left() + x * s, r.top() + y * s, w * s, h * s)

    def point_on(self, page, pos):
        r = self.rects[page]
        return QPointF((pos.x() - r.left()) / self.scale, (pos.y() - r.top()) / self.scale)

    def locate(self, pos):
        for i, r in enumerate(self.rects):
            if r.top() - self.GAP / 2 <= pos.y() <= r.bottom() + self.GAP / 2:
                return i, self.point_on(i, pos)
        return None

    # ----- text geometry -----
    def chars(self, page):
        if page not in self.char_cache:
            text = self.doc.getAllText(page).text()
            items = []
            for i in range(len(text)):
                bounds = self.doc.getSelectionAtIndex(page, i, 1).bounds()
                if bounds:
                    r = bounds[0].boundingRect()
                    if r.width() > 0.2 and r.height() > 0.5:
                        items.append((i, r))
            self.char_cache[page] = (text, items)
        return self.char_cache[page]

    def nearest_char(self, page, pt):
        best, best_d = None, None
        for i, r in self.chars(page)[1]:
            dx = max(r.left() - pt.x(), 0, pt.x() - r.right())
            dy = max(r.top() - pt.y(), 0, pt.y() - r.bottom())
            d = dx * dx + (dy * 2) ** 2
            if best_d is None or d < best_d:
                best, best_d = i, d
        return best

    def select_range(self, page, a, b):
        if a is None or b is None:
            return None
        lo, hi = min(a, b), max(a, b)
        sel = self.doc.getSelectionAtIndex(page, lo, hi - lo + 1)
        rects = []
        for poly in sel.bounds():
            r = poly.boundingRect()
            if r.width() > 0 and r.height() > 0:
                rects.append([r.x(), r.y(), r.width(), r.height()])
        text = " ".join(sel.text().split())
        if not rects or not text:
            return None
        return {"page": page, "start": lo, "end": hi, "rects": rects, "text": text}

    # ----- painting -----
    def page_image(self, page, size, dpr):
        key = (page, round(size.width() * dpr), round(size.height() * dpr))
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        img = self.doc.render(page, QSize(key[1], key[2]))
        img.setDevicePixelRatio(dpr)
        self.cache[key] = img
        while len(self.cache) > 14:
            self.cache.popitem(last=False)
        return img

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(event.rect(), self.bg)
        dpr = self.devicePixelRatioF()
        visible = QRectF(event.rect())
        for i, r in enumerate(self.rects):
            if not r.intersects(visible):
                continue
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, 26))
            p.drawRect(r.adjusted(-1, 1, 1, 3))
            p.fillRect(r, QColor("white"))
            p.drawImage(r.topLeft(), self.page_image(i, r.size(), dpr))
            highlights = self.highlights.get(i, [])
            if highlights:
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
                for hl in highlights:
                    color = QColor(hl["color"])
                    for x, y, w, h in hl["rects"]:
                        p.fillRect(self.to_widget(i, x, y, w, h).adjusted(-1, 0, 1, 0), color)
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            if self.selection and self.selection["page"] == i:
                for x, y, w, h in self.selection["rects"]:
                    p.fillRect(self.to_widget(i, x, y, w, h).adjusted(-1, 0, 1, 0),
                               QColor(79, 107, 237, 95))
        p.end()

    # ----- mouse -----
    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self.view.setFocus()
        self.bar.hide()
        self.active = None
        self.selection = None
        self.anchor = None
        self.dragging = False
        hit = self.locate(event.position())
        if hit:
            self.anchor = (hit[0], self.nearest_char(hit[0], hit[1]))
            self.press_pos = event.position()
        self.update()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton) or not self.anchor:
            return
        if not self.dragging and (event.position() - self.press_pos).manhattanLength() < 4:
            return
        self.dragging = True
        page, start = self.anchor
        end = self.nearest_char(page, self.point_on(page, event.position()))
        self.selection = self.select_range(page, start, end)
        bar = self.view.verticalScrollBar()
        y = event.position().y() - bar.value()
        if y < 20:
            bar.setValue(bar.value() - 24)
        elif y > self.view.viewport().height() - 20:
            bar.setValue(bar.value() + 24)
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self.dragging:
            if self.selection:
                self.show_bar(self.selection["page"], self.selection["rects"], False)
        else:
            hit = self.locate(event.position())
            found = self.highlight_at(*hit) if hit else None
            if found:
                self.active = found
                page, idx = found
                self.show_bar(page, self.highlights[page][idx]["rects"], True)
        self.dragging = False

    def mouseDoubleClickEvent(self, event):
        hit = self.locate(event.position())
        if not hit:
            return
        page, pt = hit
        text = self.chars(page)[0]
        i = self.nearest_char(page, pt)
        if i is None:
            return
        lo = hi = i
        while lo > 0 and not text[lo - 1].isspace():
            lo -= 1
        while hi < len(text) - 1 and not text[hi + 1].isspace():
            hi += 1
        self.active = None
        self.selection = self.select_range(page, lo, hi)
        if self.selection:
            self.show_bar(page, self.selection["rects"], False)
        self.update()

    def highlight_at(self, page, pt):
        for idx in range(len(self.highlights.get(page, [])) - 1, -1, -1):
            for x, y, w, h in self.highlights[page][idx]["rects"]:
                if QRectF(x, y, w, h).adjusted(-1, -1, 1, 1).contains(pt):
                    return page, idx
        return None

    # ----- floating bar and actions -----
    def show_bar(self, page, rects, on_highlight):
        self.bar.set_mode(on_highlight)
        self.bar.adjustSize()
        box = QRectF()
        for x, y, w, h in rects:
            box = box.united(self.to_widget(page, x, y, w, h))
        bw, bh = self.bar.width(), self.bar.height()
        x = box.center().x() - bw / 2
        y = box.top() - bh - 10
        if y < self.view.verticalScrollBar().value() + 6:
            y = box.bottom() + 10
        x = max(6, min(x, self.width() - bw - 6))
        self.bar.move(int(x), int(y))
        self.bar.show()
        self.bar.raise_()

    def current_text(self):
        if self.active:
            page, idx = self.active
            return self.highlights[page][idx]["text"]
        return self.selection["text"] if self.selection else ""

    def copy_text(self):
        text = self.current_text()
        if text:
            QApplication.clipboard().setText(text)

    def apply_color(self, color):
        if self.active:
            page, idx = self.active
            self.highlights[page][idx]["color"] = color
        elif self.selection:
            sel = self.selection
            self.highlights.setdefault(sel["page"], []).append(
                {"rects": sel["rects"], "color": color, "text": sel["text"]})
        else:
            return
        self.clear_selection()
        self.view.highlightsChanged.emit()

    def delete_active(self):
        if self.active:
            page, idx = self.active
            del self.highlights[page][idx]
            self.clear_selection()
            self.view.highlightsChanged.emit()

    def clear_selection(self):
        self.selection = None
        self.active = None
        self.anchor = None
        self.bar.hide()
        self.update()


class PdfView(QScrollArea):
    """Scrollable PDF viewer with zoom, text selection and highlights."""

    pageChanged = Signal(int)
    highlightsChanged = Signal()
    quoteRequested = Signal(str)

    def __init__(self, doc):
        super().__init__()
        self.doc = doc
        self.fit_width = True
        self.scale = 96 / 72
        self._current = -1
        self._jumping = False
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setWidgetResizable(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.canvas = PdfCanvas(self)
        self.setWidget(self.canvas)
        self.verticalScrollBar().valueChanged.connect(self.update_current)
        copy = QShortcut(QKeySequence.StandardKey.Copy, self)
        copy.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        copy.activated.connect(self.canvas.copy_text)

    def document_changed(self):
        self.canvas.reset()
        self._current = -1
        self.relayout()

    # ----- layout / navigation -----
    def top_of(self, page):
        return max(0, int(self.canvas.rects[page].top() - 10))

    def relayout(self):
        rects = self.canvas.rects
        page, frac = 0, 0.0
        if rects and self._current >= 0:
            page = min(self._current, len(rects) - 1)
            frac = (self.verticalScrollBar().value() - (rects[page].top() - 10)) / rects[page].height()
        vp = self.viewport().size()
        if self.fit_width and self.canvas.sizes:
            widest = max(s.width() for s in self.canvas.sizes)
            self.scale = max(0.2, (vp.width() - 2 * PdfCanvas.MARGIN) / widest)
        self.canvas.layout_pages(vp.width(), vp.height(), self.scale)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff if self.fit_width
                                          else Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        if self.canvas.rects:
            self._jumping = True
            r = self.canvas.rects[page]
            self.verticalScrollBar().setValue(max(0, int(r.top() - 10 + frac * r.height())))
            self._jumping = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.canvas.sizes:
            self.relayout()

    def jump(self, page):
        if not self.canvas.rects:
            return
        page = max(0, min(page, len(self.canvas.rects) - 1))
        self._jumping = True
        self.verticalScrollBar().setValue(self.top_of(page))
        self._jumping = False
        self.set_current(page)

    def set_current(self, page):
        if page != self._current:
            self._current = page
            self.pageChanged.emit(page)

    def update_current(self):
        if self._jumping or not self.canvas.rects:
            return
        top = self.verticalScrollBar().value()
        bottom = top + self.viewport().height()
        best, best_area = 0, -1
        for i, r in enumerate(self.canvas.rects):
            area = min(r.bottom(), bottom) - max(r.top(), top)
            if area > best_area:
                best, best_area = i, area
        self.set_current(best)

    # ----- zoom -----
    def set_scale(self, scale):
        self.fit_width = False
        self.scale = max(0.25, min(6.0, scale))
        self.relayout()

    def zoom_in(self):
        self.set_scale(self.scale * 1.15)

    def zoom_out(self):
        self.set_scale(self.scale / 1.15)

    def zoom_fit(self):
        self.fit_width = True
        self.relayout()

    # ----- highlights / theme -----
    def import_highlights(self, data):
        clean = {}
        try:
            for key, items in data.items():
                clean[int(key)] = [h for h in items if h.get("rects") and h.get("color")]
        except Exception:
            clean = {}
        self.canvas.highlights = clean
        self.canvas.update()

    def export_highlights(self):
        return {str(k): v for k, v in self.canvas.highlights.items() if v}

    def apply_theme(self, t):
        self.canvas.bg = QColor(t["pdf_bg"])
        self.canvas.bar.apply_theme(t["icon"])
        self.canvas.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.canvas.clear_selection()
        else:
            super().keyPressEvent(event)


class PageBox(QLineEdit):
    """Small page-number box: type a number and press Enter."""

    valueChanged = Signal(int)

    def __init__(self):
        super().__init__("1")
        self._min, self._max, self._value = 1, 1, 1
        self.setValidator(QIntValidator(1, 99999, self))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedWidth(52)
        self.editingFinished.connect(self._commit)

    def setRange(self, lo, hi):
        self._min, self._max = lo, hi

    def value(self):
        return self._value

    def setValue(self, v):
        v = max(self._min, min(self._max, int(v)))
        self.setText(str(v))
        if v != self._value:
            self._value = v
            self.valueChanged.emit(v)

    def _commit(self):
        try:
            self.setValue(int(self.text()))
        except ValueError:
            pass
        self.setText(str(self._value))


# ------------------------------------------------------------ note editor ----
class NoteEditor(QTextEdit):
    """Rich text editor: screenshot paste, markdown-style shortcuts, list indenting."""

    pdfs_dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.images_dir = None
        self.setAcceptRichText(False)
        self.setPlaceholderText("Write your notes for this page…\n\n"
                                "Tips:  “- ” bullet list   “1. ” numbered list   “# ” title   “## ” heading\n"
                                "Paste a screenshot with Cmd+V   ·   Tab / Shift+Tab to indent lists")
        self.document().setDefaultFont(QFont(self.font().family(), BODY_SIZE))
        self.document().setDocumentMargin(4)

    # ----- formatting helpers (used by toolbar and shortcuts) -----
    def apply_block_style(self, size, bold):
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        fmt.setFontWeight(700 if bold else 400)
        cursor = self.textCursor()
        cursor.beginEditBlock()
        if not cursor.hasSelection():
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        cursor.mergeCharFormat(fmt)
        cursor.endEditBlock()
        self.mergeCurrentCharFormat(fmt)
        self.setFocus()

    def toggle_bold(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(400 if self.currentCharFormat().fontWeight() > 400 else 700)
        self.mergeCurrentCharFormat(fmt)
        self.setFocus()

    def toggle_highlight(self):
        brush = self.currentCharFormat().background()
        on = brush.style() != Qt.BrushStyle.NoBrush and brush.color().alpha() > 0
        fmt = QTextCharFormat()
        fmt.setBackground(QColor(0, 0, 0, 0) if on else HIGHLIGHT)
        self.mergeCurrentCharFormat(fmt)
        self.setFocus()

    def toggle_list(self, style):
        cursor = self.textCursor()
        current = cursor.currentList()
        if current is not None and current.format().style() == style:
            cursor.beginEditBlock()
            current.remove(cursor.block())
            block_fmt = cursor.blockFormat()
            block_fmt.setIndent(0)
            cursor.setBlockFormat(block_fmt)
            cursor.endEditBlock()
        else:
            list_fmt = QTextListFormat()
            list_fmt.setStyle(style)
            list_fmt.setIndent(1)
            cursor.createList(list_fmt)
        self.setFocus()

    def indent_list(self, delta):
        cursor = self.textCursor()
        current = cursor.currentList()
        if current is None:
            return False
        fmt = current.format()
        level = max(1, min(6, fmt.indent() + delta))
        if level == fmt.indent():
            return True
        fmt.setIndent(level)
        if fmt.style() in (QTextListFormat.Style.ListDisc, QTextListFormat.Style.ListCircle,
                           QTextListFormat.Style.ListSquare):
            fmt.setStyle((QTextListFormat.Style.ListDisc, QTextListFormat.Style.ListCircle,
                          QTextListFormat.Style.ListSquare)[(level - 1) % 3])
        cursor.createList(fmt)
        return True

    def insert_quote(self, text):
        """Insert text copied from the PDF as an italic quote and continue on a normal line."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        if cursor.block().text().strip():
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
            cursor.insertBlock()
        block_fmt = QTextBlockFormat()
        block_fmt.setLeftMargin(14)
        char_fmt = QTextCharFormat()
        char_fmt.setFontItalic(True)
        char_fmt.setFontPointSize(BODY_SIZE)
        char_fmt.setFontWeight(400)
        cursor.setBlockFormat(block_fmt)
        cursor.insertText("\u201c" + text + "\u201d", char_fmt)
        cursor.insertBlock(QTextBlockFormat(), QTextCharFormat())
        cursor.endEditBlock()
        self.setTextCursor(cursor)
        self.reset_to_body()
        self.setFocus()

    # ----- keyboard -----
    def keyPressEvent(self, event):
        key = event.key()
        no_mods = not (event.modifiers() & (Qt.KeyboardModifier.ControlModifier
                                            | Qt.KeyboardModifier.AltModifier
                                            | Qt.KeyboardModifier.MetaModifier))
        if key == Qt.Key.Key_Space and no_mods and self.try_markdown():
            return
        if key == Qt.Key.Key_Tab and no_mods and self.indent_list(+1):
            return
        if key == Qt.Key.Key_Backtab and self.indent_list(-1):
            return
        super().keyPressEvent(event)
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.reset_after_heading()

    def try_markdown(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            return False
        block = cursor.block()
        text = block.text()
        if cursor.positionInBlock() != len(text) or text not in ("-", "*", "1.", "#", "##"):
            return False
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        self.setTextCursor(cursor)
        if text in ("-", "*"):
            self.reset_to_body()
            self.toggle_list(QTextListFormat.Style.ListDisc)
        elif text == "1.":
            self.reset_to_body()
            self.toggle_list(QTextListFormat.Style.ListDecimal)
        elif text == "#":
            self.apply_block_style(TITLE_SIZE, True)
        else:
            self.apply_block_style(HEADING_SIZE, True)
        return True

    def reset_to_body(self):
        """Make the (empty) current line normal body text, also for its list marker."""
        fmt = QTextCharFormat()
        fmt.setFontPointSize(BODY_SIZE)
        fmt.setFontWeight(400)
        cursor = self.textCursor()
        cursor.mergeBlockCharFormat(fmt)
        self.mergeCurrentCharFormat(fmt)

    def reset_after_heading(self):
        cursor = self.textCursor()
        prev = cursor.block().previous()
        if not prev.isValid() or cursor.block().text():
            return
        probe = QTextCursor(prev)
        probe.movePosition(QTextCursor.MoveOperation.EndOfBlock)
        if probe.charFormat().fontPointSize() > BODY_SIZE + 0.5:
            self.reset_to_body()

    # ----- images / dropped files -----
    def canInsertFromMimeData(self, source):
        if self._pdf_urls(source) or (self.images_dir is not None
                                      and (source.hasImage() or self._image_urls(source))):
            return True
        return super().canInsertFromMimeData(source)

    def insertFromMimeData(self, source):
        pdfs = self._pdf_urls(source)
        if pdfs:
            self.pdfs_dropped.emit(pdfs)
            return
        if self.images_dir is not None:
            if source.hasImage():
                img = QImage(source.imageData())
                if not img.isNull():
                    self.add_image(img)
                    return
            urls = self._image_urls(source)
            if urls:
                for path in urls:
                    self.add_image_file(path)
                return
        super().insertFromMimeData(source)

    @staticmethod
    def _urls_with(source, exts):
        if not source.hasUrls():
            return []
        return [u.toLocalFile() for u in source.urls()
                if u.isLocalFile() and Path(u.toLocalFile()).suffix.lower() in exts]

    def _image_urls(self, source):
        return self._urls_with(source, IMAGE_EXT)

    def _pdf_urls(self, source):
        return self._urls_with(source, {".pdf"})

    def add_image_file(self, path):
        img = QImage(path)
        if not img.isNull():
            self.add_image(img)

    def add_image(self, img: QImage):
        if self.images_dir is None:
            return
        self.images_dir.mkdir(parents=True, exist_ok=True)
        name = f"{uuid.uuid4().hex[:12]}.png"
        img.save(str(self.images_dir / name))
        width = min(img.width(), 420)
        fmt = QTextImageFormat()
        fmt.setName(f"images/{name}")  # relative to the notes folder
        fmt.setWidth(width)
        fmt.setHeight(img.height() * width / img.width())
        cursor = self.textCursor()
        cursor.insertImage(fmt)
        cursor.insertText("\n")


# ------------------------------------------------------------ main window ----
class ScholiaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scholia")
        self.resize(1480, 900)
        self.setAcceptDrops(True)

        self.settings = QSettings("Scholia", "Scholia")
        self.migrate_old_settings()
        self.doc = QPdfDocument(self)
        self.pdf_path = None
        self.notes_dir = None
        self.notes = {}
        self.current_page = 0
        self.loading = False
        self.restoring = False
        self.library = self.load_library()
        self.icon_actions = []  # [action, icon name] - recoloured when the theme changes
        self.theme = self.initial_theme()

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.build_sidebar())
        self.splitter.addWidget(self.build_pdf_pane())
        self.splitter.addWidget(self.build_notes_pane())
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 1)
        self.splitter.setSizes([250, 640, 640])
        self.setCentralWidget(self.splitter)

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(700)
        self.save_timer.timeout.connect(self.save_current)

        self.restore_window_state()
        self.apply_theme()
        self.refresh_library()
        self.editor.setEnabled(False)

    def migrate_old_settings(self):
        """Carry over the PDF list and layout from development builds (earlier working name)."""
        if self.settings.contains("library"):
            return
        old = QSettings("PDFNotes", "PDFNotes")
        if not old.contains("library"):
            return
        for key in ("library", "last_pdf", "theme", "geometry", "splitter"):
            if old.contains(key):
                self.settings.setValue(key, old.value(key))

    # ---------------------------------------------------------- building UI ----
    def add_action(self, bar, icon, tip, fn, shortcut=None, checkable=False):
        act = QAction(self)
        act.setCheckable(checkable)
        if shortcut is not None:
            seq = QKeySequence(shortcut)
            act.setShortcut(seq)
            tip = f"{tip}  ({seq.toString(QKeySequence.SequenceFormat.NativeText)})"
        act.setToolTip(tip)
        act.triggered.connect(lambda checked=False: fn())
        bar.addAction(act)
        self.icon_actions.append([act, icon])
        return act

    @staticmethod
    def new_bar():
        bar = QToolBar()
        bar.setMovable(False)
        bar.setIconSize(QSize(18, 18))
        bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        return bar

    @staticmethod
    def spacer(bar):
        sp = QWidget()
        sp.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        bar.addWidget(sp)

    def build_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setMinimumWidth(190)
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setContentsMargins(16, 4, 6, 0)
        self.brand_icon = QLabel()
        brand = QLabel("Scholia")
        brand.setObjectName("brand")
        header.addWidget(self.brand_icon)
        header.addSpacing(6)
        header.addWidget(brand)
        header.addStretch()
        bar = self.new_bar()
        self.theme_action = self.add_action(bar, "moon", "Switch light / dark theme", self.toggle_theme)
        header.addWidget(bar)
        layout.addLayout(header)

        self.add_button = QPushButton("  Add PDF")
        self.add_button.setObjectName("primary")
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_button.setShortcut(QKeySequence.StandardKey.Open)
        self.add_button.clicked.connect(self.add_pdfs_dialog)
        btn_wrap = QHBoxLayout()
        btn_wrap.setContentsMargins(14, 4, 14, 4)
        btn_wrap.addWidget(self.add_button)
        layout.addLayout(btn_wrap)

        label = QLabel("YOUR PDFs")
        label.setObjectName("muted")
        label.setContentsMargins(18, 6, 0, 0)
        layout.addWidget(label)

        self.lib_list = QListWidget()
        self.lib_delegate = LibraryDelegate(self.lib_list)
        self.lib_list.setItemDelegate(self.lib_delegate)
        self.lib_list.setMouseTracking(True)
        self.lib_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.lib_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lib_list.customContextMenuRequested.connect(self.library_menu)
        self.lib_list.itemClicked.connect(self.on_lib_clicked)
        for key in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            sc = QShortcut(QKeySequence(key), self.lib_list)
            sc.setContext(Qt.ShortcutContext.WidgetShortcut)
            sc.activated.connect(self.remove_selected)
        layout.addWidget(self.lib_list, 1)
        return self.sidebar

    def build_pdf_pane(self):
        pane = QWidget()
        pane.setObjectName("pdfPane")
        pane.setMinimumWidth(300)
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        bar = self.new_bar()
        self.add_action(bar, "sidebar", "Show / hide PDF list", self.toggle_sidebar, "Ctrl+\\")
        bar.addSeparator()
        self.add_action(bar, "left", "Previous page", self.prev_page, "Ctrl+[")
        self.page_spin = PageBox()
        self.page_spin.setToolTip("Type a page number and press Enter")
        self.page_spin.valueChanged.connect(self.go_to_page)
        bar.addWidget(self.page_spin)
        self.total_label = QLabel("  / 0  ")
        self.total_label.setObjectName("muted")
        bar.addWidget(self.total_label)
        self.add_action(bar, "right", "Next page", self.next_page, "Ctrl+]")
        self.spacer(bar)
        self.add_action(bar, "zoom-out", "Zoom out", self.zoom_out)
        self.add_action(bar, "zoom-in", "Zoom in", self.zoom_in)
        self.add_action(bar, "fit", "Fit to width", self.zoom_fit)
        layout.addWidget(bar)

        self.pdf_view = PdfView(self.doc)
        self.pdf_view.pageChanged.connect(self.on_pdf_page_changed)
        self.pdf_view.highlightsChanged.connect(self.on_highlights_changed)
        self.pdf_view.quoteRequested.connect(self.add_quote)
        for key, fn in ((Qt.Key.Key_Left, self.prev_page), (Qt.Key.Key_Right, self.next_page)):
            sc = QShortcut(QKeySequence(key), self.pdf_view)
            sc.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            sc.activated.connect(fn)

        empty = QWidget()
        empty.setObjectName("emptyState")
        e_layout = QVBoxLayout(empty)
        e_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_icon = QLabel()
        self.empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Add your lecture PDFs")
        title.setObjectName("emptyTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel("Drag & drop PDF files here, or click the button.\nYour notes are saved automatically.")
        sub.setObjectName("emptySub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn = QPushButton("Add PDF")
        btn.setObjectName("primary")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedWidth(160)
        btn.clicked.connect(self.add_pdfs_dialog)
        for w in (self.empty_icon, title, sub):
            e_layout.addWidget(w)
            e_layout.addSpacing(6)
        e_layout.addSpacing(10)
        e_layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)

        self.stack = QStackedWidget()
        self.stack.addWidget(empty)
        self.stack.addWidget(self.pdf_view)
        layout.addWidget(self.stack, 1)
        return pane

    def build_notes_pane(self):
        pane = QWidget()
        pane.setObjectName("notesPane")
        pane.setMinimumWidth(300)
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        head = QHBoxLayout()
        head.setContentsMargins(22, 14, 18, 0)
        self.notes_title = QLabel("Notes")
        self.notes_title.setObjectName("pageTitle")
        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        head.addWidget(self.notes_title)
        head.addStretch()
        head.addWidget(self.status_label)
        layout.addLayout(head)

        self.editor = NoteEditor()
        self.editor.textChanged.connect(self.on_text_changed)
        self.editor.pdfs_dropped.connect(self.add_pdfs)
        self.editor.currentCharFormatChanged.connect(lambda *_: self.update_format_state())
        self.editor.cursorPositionChanged.connect(self.update_format_state)

        bar = self.new_bar()
        ed = self.editor
        self.add_action(bar, "h1", "Title", lambda: ed.apply_block_style(TITLE_SIZE, True), "Ctrl+Alt+1")
        self.add_action(bar, "h2", "Heading", lambda: ed.apply_block_style(HEADING_SIZE, True), "Ctrl+Alt+2")
        self.add_action(bar, "text", "Normal text", lambda: ed.apply_block_style(BODY_SIZE, False), "Ctrl+Alt+0")
        bar.addSeparator()
        self.act_bold = self.add_action(bar, "bold", "Bold", ed.toggle_bold, QKeySequence.StandardKey.Bold, True)
        self.act_hl = self.add_action(bar, "highlight", "Highlight", ed.toggle_highlight, "Ctrl+Shift+H", True)
        bar.addSeparator()
        self.act_bullet = self.add_action(bar, "list", "Bullet list  (type “- ”)",
                                          lambda: ed.toggle_list(QTextListFormat.Style.ListDisc), None, True)
        self.act_number = self.add_action(bar, "list-ordered", "Numbered list  (type “1. ”)",
                                          lambda: ed.toggle_list(QTextListFormat.Style.ListDecimal), None, True)
        bar.addSeparator()
        self.add_action(bar, "image", "Insert image from file  (or paste a screenshot)", self.insert_image_dialog)
        self.spacer(bar)
        self.add_action(bar, "undo", "Undo", ed.undo)
        self.add_action(bar, "redo", "Redo", ed.redo)
        layout.addWidget(bar)
        layout.addWidget(self.editor, 1)
        return pane

    # ---------------------------------------------------------------- theme ----
    def initial_theme(self):
        saved = self.settings.value("theme", "")
        if saved in ("light", "dark"):
            return DARK if saved == "dark" else LIGHT
        try:
            if QApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark:
                return DARK
        except Exception:
            pass
        return LIGHT

    def toggle_theme(self):
        self.theme = LIGHT if self.theme is DARK else DARK
        self.settings.setValue("theme", "dark" if self.theme is DARK else "light")
        self.apply_theme()

    def apply_theme(self):
        t = self.theme
        app = QApplication.instance()
        app.setPalette(make_palette(t))
        app.setStyleSheet(QSS.substitute(t))
        self.theme_action.setToolTip("Switch to light theme" if t is DARK else "Switch to dark theme")
        for entry in self.icon_actions:
            if entry[0] is self.theme_action:
                entry[1] = "sun" if t is DARK else "moon"
            entry[0].setIcon(make_icon(entry[1], t["icon"]))
        self.brand_icon.setPixmap(make_pixmap("book", t["accent"], 22, 2.2))
        self.empty_icon.setPixmap(make_pixmap("book", t["accent"], 56, 1.6))
        self.add_button.setIcon(make_icon("plus", "#ffffff", 16))
        self.pdf_view.apply_theme(t)
        self.lib_delegate.theme = t
        self.lib_list.viewport().update()

    # -------------------------------------------------- window state / misc ----
    def restore_window_state(self):
        geo = self.settings.value("geometry")
        if geo:
            self.restoreGeometry(geo)
        try:
            sizes = json.loads(self.settings.value("splitter", "[]"))
            if len(sizes) == 3 and all(s > 0 for s in sizes):
                self.splitter.setSizes(sizes)
        except Exception:
            pass

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def update_format_state(self):
        fmt = self.editor.currentCharFormat()
        self.act_bold.setChecked(fmt.fontWeight() > 400)
        brush = fmt.background()
        self.act_hl.setChecked(brush.style() != Qt.BrushStyle.NoBrush and brush.color().alpha() > 0)
        lst = self.editor.textCursor().currentList()
        style = lst.format().style() if lst is not None else None
        self.act_bullet.setChecked(style in (QTextListFormat.Style.ListDisc, QTextListFormat.Style.ListCircle,
                                             QTextListFormat.Style.ListSquare))
        self.act_number.setChecked(style == QTextListFormat.Style.ListDecimal)

    def insert_image_dialog(self):
        if self.notes_dir is None:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Insert image", "",
                                              "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp)")
        if path:
            self.editor.add_image_file(path)
            self.editor.setFocus()

    # ----------------------------------------------------- drag & drop PDFs ----
    def dragEnterEvent(self, event):
        if any(u.isLocalFile() and u.toLocalFile().lower().endswith(".pdf")
               for u in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls()
                 if u.isLocalFile() and u.toLocalFile().lower().endswith(".pdf")]
        if paths:
            event.acceptProposedAction()
            self.add_pdfs(paths)

    # ---------------------------------------------------------- PDF library ----
    def startup(self):
        last = self.settings.value("last_pdf", "")
        if last in self.library and Path(last).exists():
            self.open_pdf(last)
            return
        for path in self.library:
            if Path(path).exists():
                self.open_pdf(path)
                return

    def load_library(self):
        try:
            data = json.loads(self.settings.value("library", "[]"))
            return [p for p in data if isinstance(p, str)]
        except Exception:
            return []

    def save_library(self):
        self.settings.setValue("library", json.dumps(self.library))

    @staticmethod
    def notes_dir_for(path):
        p = Path(path)
        return p.parent / f"{p.stem}_notes"

    def progress_text(self, path):
        if not Path(path).exists():
            return "File not found"
        data_file = self.notes_dir_for(path) / "notes.json"
        if data_file.exists():
            try:
                data = json.loads(data_file.read_text(encoding="utf-8"))
                text = f"Page {int(data.get('last_page', 0)) + 1}"
                if data.get("total_pages"):
                    text += f" of {data['total_pages']}"
                if data.get("pages"):
                    text += f"  ·  {len(data['pages'])} with notes"
                return text
            except Exception:
                pass
        return "Not opened yet"

    def refresh_library(self, select=None):
        select = select or (str(self.pdf_path) if self.pdf_path else None)
        self.lib_list.blockSignals(True)
        self.lib_list.clear()
        for path in self.library:
            exists = Path(path).exists()
            item = QListWidgetItem(Path(path).stem)
            item.setToolTip(path)
            item.setData(ROLE_PATH, path)
            item.setData(ROLE_SUB, self.progress_text(path))
            item.setData(ROLE_MISSING, not exists)
            self.lib_list.addItem(item)
            if path == select:
                self.lib_list.setCurrentItem(item)
        self.lib_list.blockSignals(False)

    def update_current_subtitle(self):
        if self.pdf_path is None:
            return
        for i in range(self.lib_list.count()):
            item = self.lib_list.item(i)
            if item.data(ROLE_PATH) == str(self.pdf_path):
                item.setData(ROLE_SUB, self.progress_text(str(self.pdf_path)))

    def add_pdfs_dialog(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Add PDFs", "", "PDF files (*.pdf)")
        self.add_pdfs(paths)

    def add_pdfs(self, paths):
        if not paths:
            return
        for path in paths:
            if path not in self.library:
                self.library.append(path)
        self.save_library()
        self.refresh_library()
        self.open_pdf(paths[0])

    def on_lib_clicked(self, item):
        path = item.data(ROLE_PATH)
        if not Path(path).exists():
            QMessageBox.information(
                self, "Scholia",
                "This PDF was not found. It may have been moved or deleted.\n"
                "Remove it from the list and add it again from its new location.")
            return
        if self.pdf_path is not None and str(self.pdf_path) == path:
            return
        self.open_pdf(path)

    def library_menu(self, pos):
        item = self.lib_list.itemAt(pos)
        if item is None:
            return
        path = item.data(ROLE_PATH)
        menu = QMenu(self)
        reveal = menu.addAction("Show in Finder")
        remove = menu.addAction("Remove from list")
        chosen = menu.exec(self.lib_list.viewport().mapToGlobal(pos))
        if chosen == reveal:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(path).parent)))
        elif chosen == remove:
            self.remove_path(path)

    def remove_selected(self):
        item = self.lib_list.currentItem()
        if item is not None:
            self.remove_path(item.data(ROLE_PATH))

    def remove_path(self, path):
        if path in self.library:
            self.library.remove(path)
            self.save_library()
        if self.pdf_path is not None and str(self.pdf_path) == path:
            self.close_pdf()
            for other in self.library:
                if Path(other).exists():
                    self.open_pdf(other)
                    break
        self.refresh_library()

    # ------------------------------------------------------- open / close PDF ----
    def open_pdf(self, path):
        self.save_current()
        if self.doc.load(path) != QPdfDocument.Error.None_:
            QMessageBox.warning(self, "Scholia", f"Could not open:\n{path}")
            return
        self.pdf_path = Path(path)
        self.notes_dir = self.notes_dir_for(path)
        self.editor.images_dir = self.notes_dir / "images"
        self.notes = {}
        last_page = 0
        highlights = {}
        data_file = self.notes_dir / "notes.json"
        if data_file.exists():
            try:
                data = json.loads(data_file.read_text(encoding="utf-8"))
                self.notes = data.get("pages", {})
                last_page = int(data.get("last_page", 0))
                highlights = data.get("highlights", {})
            except Exception:
                pass
        total = self.doc.pageCount()
        self.pdf_view.document_changed()
        self.pdf_view.import_highlights(highlights)
        last_page = max(0, min(last_page, total - 1))
        self.page_spin.blockSignals(True)
        self.page_spin.setRange(1, total)
        self.page_spin.setValue(last_page + 1)
        self.page_spin.blockSignals(False)
        self.total_label.setText(f"  / {total}  ")
        self.setWindowTitle(f"Scholia — {self.pdf_path.name}")
        self.settings.setValue("last_pdf", str(self.pdf_path))
        self.stack.setCurrentIndex(1)
        self.editor.setEnabled(True)

        self.restoring = True  # ignore the viewer's startup page events
        self.current_page = last_page
        self.load_page_notes()
        self.pdf_view.jump(last_page)
        QTimer.singleShot(400, self.finish_restore)
        self.refresh_library(str(self.pdf_path))

    def finish_restore(self):
        self.pdf_view.relayout()
        self.pdf_view.jump(self.current_page)
        QTimer.singleShot(200, lambda: setattr(self, "restoring", False))

    def close_pdf(self):
        self.save_current()
        self.doc.close()
        self.pdf_view.document_changed()
        self.pdf_path = None
        self.notes_dir = None
        self.notes = {}
        self.current_page = 0
        self.editor.images_dir = None
        self.loading = True
        self.editor.clear()
        self.loading = False
        self.editor.setEnabled(False)
        self.stack.setCurrentIndex(0)
        self.notes_title.setText("Notes")
        self.status_label.setText("")
        self.total_label.setText("  / 0  ")
        self.setWindowTitle("Scholia")

    # ------------------------------------------------------ page navigation ----
    def go_to_page(self, number):
        self.change_page(number - 1)
        self.pdf_view.jump(number - 1)

    def prev_page(self):
        if self.doc.pageCount():
            self.page_spin.setValue(max(1, self.page_spin.value() - 1))

    def next_page(self):
        if self.doc.pageCount():
            self.page_spin.setValue(min(self.doc.pageCount(), self.page_spin.value() + 1))

    def on_pdf_page_changed(self, page):
        if self.restoring:
            return
        self.change_page(page)
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(page + 1)
        self.page_spin.blockSignals(False)

    def change_page(self, page):
        if page == self.current_page or self.notes_dir is None:
            return
        self.save_current()
        self.current_page = page
        self.load_page_notes()
        self.write_notes()
        self.update_current_subtitle()

    # ----------------------------------------------------------------- zoom ----
    def zoom_in(self):
        self.pdf_view.zoom_in()

    def zoom_out(self):
        self.pdf_view.zoom_out()

    def zoom_fit(self):
        self.pdf_view.zoom_fit()

    # ---------------------------------------------------- notes load / save ----
    def load_page_notes(self):
        self.loading = True
        self.editor.document().setBaseUrl(QUrl.fromLocalFile(str(self.notes_dir) + "/"))
        html = self.notes.get(str(self.current_page + 1))
        if html:
            self.editor.setHtml(html)
        else:
            self.editor.clear()
        self.loading = False
        self.notes_title.setText(f"Notes · Page {self.current_page + 1}")
        self.status_label.setText("")
        self.update_format_state()

    def on_text_changed(self):
        if not self.loading and self.notes_dir is not None:
            self.status_label.setText("Editing…")
            self.save_timer.start()

    def save_current(self):
        self.save_timer.stop()
        if self.loading or self.notes_dir is None:
            return
        html = self.editor.toHtml()
        empty = not self.editor.toPlainText().strip() and "<img" not in html
        key = str(self.current_page + 1)
        if empty:
            self.notes.pop(key, None)
        else:
            self.notes[key] = html
        self.write_notes()
        self.status_label.setText("Saved ✓")
        self.update_current_subtitle()

    def on_highlights_changed(self):
        self.write_notes()
        self.status_label.setText("Saved ✓")
        self.update_current_subtitle()

    def add_quote(self, text):
        if text and self.notes_dir is not None:
            self.editor.insert_quote(text)

    def write_notes(self):
        if self.notes_dir is None:
            return
        highlights = self.pdf_view.export_highlights()
        if self.notes or highlights or self.notes_dir.exists():
            self.notes_dir.mkdir(parents=True, exist_ok=True)
            data = {"version": 1, "last_page": self.current_page,
                    "total_pages": self.doc.pageCount(), "pages": self.notes,
                    "highlights": highlights}
            (self.notes_dir / "notes.json").write_text(
                json.dumps(data, ensure_ascii=False), encoding="utf-8")

    # -------------------------------------------------------------- closing ----
    def closeEvent(self, event):
        self.save_current()
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("splitter", json.dumps(self.splitter.sizes()))
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Scholia")
    app.setApplicationVersion(__version__)
    icon_file = Path(__file__).resolve().parent / "assets" / "Scholia.png"
    if icon_file.exists():
        app.setWindowIcon(QIcon(str(icon_file)))
    window = ScholiaWindow()
    window.show()
    QTimer.singleShot(0, window.startup)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
