import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QFileDialog, QPushButton, QHBoxLayout, 
    QVBoxLayout, QWidget, QListWidget, QDockWidget, QSpinBox, QColorDialog
)
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QIcon
from PySide6.QtCore import Qt, QPoint

class Layer:
    def __init__(self, pixmap, name="Layer"):
        self.pixmap = pixmap
        self.name = name
        self.visible = True

class GMPhotoEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GM-PHOTO-EDITOR")
        self.setWindowIcon(QIcon("logo.ico"))  # Set the program icon
        self.resize(1200, 700)

        # Canvas
        self.image_label = QLabel("No image loaded")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #555;")
        self.setCentralWidget(self.image_label)

        # Layers
        self.layers = []
        self.current_layer_index = -1
        self.undo_stack = []

        # Tools
        self.current_tool = "brush"
        self.brush_color = QColor("red")
        self.brush_size = 5
        self.drawing = False
        self.last_point = QPoint()

        self.init_ui()

    def init_ui(self):
        # Top toolbar
        toolbar_layout = QHBoxLayout()
        
        open_btn = QPushButton("Open Image")
        open_btn.clicked.connect(self.open_image)
        save_btn = QPushButton("Save Image")
        save_btn.clicked.connect(self.save_image)
        brush_btn = QPushButton("Brush")
        brush_btn.clicked.connect(lambda: self.select_tool("brush"))
        eraser_btn = QPushButton("Eraser")
        eraser_btn.clicked.connect(lambda: self.select_tool("eraser"))
        color_btn = QPushButton("Color")
        color_btn.clicked.connect(self.choose_color)
        size_spin = QSpinBox()
        size_spin.setValue(5)
        size_spin.setRange(1,100)
        size_spin.valueChanged.connect(lambda v: setattr(self, "brush_size", v))
        new_layer_btn = QPushButton("New Layer")
        new_layer_btn.clicked.connect(self.new_layer)

        for w in [open_btn, save_btn, brush_btn, eraser_btn, color_btn, size_spin, new_layer_btn]:
            toolbar_layout.addWidget(w)

        toolbar_widget = QWidget()
        toolbar_widget.setLayout(toolbar_layout)
        self.addToolBar(Qt.TopToolBarArea, self.create_toolbar(toolbar_widget))

        # Layers panel
        self.layer_list = QListWidget()
        self.layer_list.currentRowChanged.connect(self.change_layer)
        layer_dock = QDockWidget("Layers", self)
        layer_dock.setWidget(self.layer_list)
        self.addDockWidget(Qt.RightDockWidgetArea, layer_dock)

    def create_toolbar(self, widget):
        from PySide6.QtWidgets import QToolBar
        toolbar = QToolBar()
        toolbar.addWidget(widget)
        return toolbar

    # Open image
    def open_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.bmp)")
        if file_name:
            pix = QPixmap(file_name)
            self.layers = [Layer(pix, "Background")]
            self.current_layer_index = 0
            self.layer_list.clear()
            self.layer_list.addItem("Background")
            self.update_canvas()

    # Add new layer
    def new_layer(self):
        if not self.layers:
            return
        size = self.layers[0].pixmap.size()
        pix = QPixmap(size)
        pix.fill(Qt.transparent)
        layer = Layer(pix, f"Layer {len(self.layers)}")
        self.layers.append(layer)
        self.current_layer_index = len(self.layers)-1
        self.layer_list.addItem(layer.name)
        self.update_canvas()

    def change_layer(self, index):
        if 0 <= index < len(self.layers):
            self.current_layer_index = index

    def select_tool(self, tool):
        self.current_tool = tool

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.brush_color = color

    # Save image
    def save_image(self):
        if not self.layers:
            return
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG (*.png);;JPEG (*.jpg)")
        if file_name:
            merged = self.merge_layers()
            merged.save(file_name)

    def merge_layers(self):
        if not self.layers:
            return QPixmap()
        merged = QPixmap(self.layers[0].pixmap.size())
        merged.fill(Qt.transparent)
        painter = QPainter(merged)
        for layer in self.layers:
            if layer.visible:
                painter.drawPixmap(0,0,layer.pixmap)
        painter.end()
        return merged

    def update_canvas(self):
        merged = self.merge_layers()
        if not merged.isNull():
            scaled = merged.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)

    # Draw on layer
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.current_layer_index >= 0:
            pos = self.image_label.mapFromParent(event.pos())
            if self.image_label.rect().contains(pos):
                self.drawing = True
                self.last_point = pos

    def mouseMoveEvent(self, event):
        if self.drawing and self.current_layer_index >= 0:
            pos = self.image_label.mapFromParent(event.pos())
            layer = self.layers[self.current_layer_index].pixmap
            scale_x = layer.width() / self.image_label.width()
            scale_y = layer.height() / self.image_label.height()
            p1 = QPoint(int(self.last_point.x()*scale_x), int(self.last_point.y()*scale_y))
            p2 = QPoint(int(pos.x()*scale_x), int(pos.y()*scale_y))
            painter = QPainter(layer)
            if self.current_tool == "brush":
                pen = QPen(self.brush_color, self.brush_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            elif self.current_tool == "eraser":
                pen = QPen(Qt.transparent, self.brush_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.setPen(pen)
            painter.drawLine(p1,p2)
            painter.end()
            self.last_point = pos
            self.update_canvas()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_canvas()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GMPhotoEditor()
    window.show()
    sys.exit(app.exec())
