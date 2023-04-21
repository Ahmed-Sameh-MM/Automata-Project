from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.uic import loadUi
import pydot
import os
from collections import defaultdict
import graphviz
import atexit


def cleanFiles():
    os.remove(resource_path("Resources/graph.png"))
    os.remove(resource_path("Resources/graph.dot"))


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi(resource_path("UI Files/MainScreen.ui"), self)
        self.label_2.setPixmap(QtGui.QPixmap(resource_path("Resources/logo.png")))
        self.pushButton.clicked.connect(self.switchWindow)

    def switchWindow(self):
        MainWidget.setCurrentIndex(1)


class GraphInputWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(GraphInputWindow, self).__init__()
        loadUi(resource_path("UI Files/GraphInput.ui"), self)
        self.addEdgeBtn.clicked.connect(self.addEdge_click)
        self.addNodeBtn.clicked.connect(self.addNode_click)
        self.resetBtn.clicked.connect(self.reset_click)
        self.convertBtn.clicked.connect(lambda: print("Done"))
        self.backBtn.clicked.connect(self.back_click)
        self.graphvizGraph = graphviz.Digraph()
        self.inputEdge.returnPressed.connect(self.addEdge_click)
        self.inputNode.returnPressed.connect(self.addNode_click)
        self.nodeDoneBtn.clicked.connect(self.done_click)
        self.edgeDoneBtn.clicked.connect(self.done_click)
        self.addNodesBtn.clicked.connect(lambda: self.addChoose_click(1))
        self.addEdgesBtn.clicked.connect(lambda: self.addChoose_click(2))
        self.zoomInBtn.clicked.connect(lambda: self.zoom(True))
        self.zoomOutBtn.clicked.connect(lambda: self.zoom(False))
        self.graphEdges = {}
        self.graphEdges = defaultdict(lambda: list(), self.graphEdges)
        self.startNode = ""
        self.finalNodes = []
        lay = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.frame)
        self.scrollArea.setWidgetResizable(True)
        self.frame.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.scale = 1.0

    def back_click(self):
        MainWidget.setCurrentIndex(0)

    def reset_click(self):
        self.graphvizGraph.clear()
        self.graphEdges.clear()
        self.draw_graph()
        self.scale = 1.0
        cleanFiles()

    def draw_graph(self):
        self.graphvizGraph.save(filename="Resources/graph.dot")
        dotGraph = pydot.graph_from_dot_file("Resources/graph.dot")[0]
        self.graphEdges.clear()
        if len(dotGraph.get_edges()) > 0:
            for edge in dotGraph.get_edges():
                if edge.get_source() == "": continue
                self.graphEdges[(edge.get_source(), edge.get_destination())].append(edge.get('label').replace('"', "").replace(' ', ""))
        dotGraph.write_png(resource_path("Resources/graph.png"))
        self.frame.setPixmap(QtGui.QPixmap(resource_path("Resources/graph.png")))

    def addEdge_click(self):
        try:
            inputs = self.inputEdge.text()
            decompose = inputs.split(",")
            if len(decompose) > 3: raise Exception
            self.graphvizGraph.edge(str(decompose[0]), str(decompose[1]), label=str(" "+decompose[2]))
            self.draw_graph()
        except Exception as e:
            print(e)
            self.error_popup("Please Enter Edge In Correct Format", "Format Example: 1,2,A or 2,5,B")

    def addNode_click(self):
        try:
            node = self.inputNode.text()
            if node.find(" ") != -1: raise Exception
            if self.nodeType.currentText() == "Starting":
                if self.startNode != "": raise Exception
                self.graphvizGraph.node(str(node), color="red", fontcolor="red")
                self.graphvizGraph.node("", width="0.01", height="0.01")
                self.graphvizGraph.edge("", str(node), label="")
                self.startNode = node
            elif self.nodeType.currentText() == "Final":
                self.graphvizGraph.node(node, color="green", fontcolor="green")
                self.finalNodes.append(node)
            else: self.graphvizGraph.node(node)
            self.draw_graph()
        except Exception as e:
            print(e)
            self.error_popup("Please Enter Node In Correct Format", "Format Example: 1 or 2\n\nNotes:\n\t"
                                                                    "1)No spaces are allowed\n\t"
                                                                    "2)No more than 1 starting node")

    def done_click(self):
        self.inputMenu.setCurrentIndex(0)

    def addChoose_click(self, choice):
        if choice == 1: self.inputMenu.setCurrentIndex(1)
        else: self.inputMenu.setCurrentIndex(2)

    def error_popup(self,err_msg,extra=""):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("Error")
        msg.setWindowIcon(QtGui.QIcon(resource_path("Resources/logo.png")))
        msg.setText("An Error Occurred!")
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setInformativeText(err_msg)
        if extra != "": msg.setDetailedText(extra)
        x = msg.exec_()

    def zoom(self, check):
        if check:self.scale += 0.1
        else:self.scale -= 0.1
        pixmap = QtGui.QPixmap(resource_path("Resources/graph.png"))
        pixmapSize = pixmap.size()
        newpixmap = pixmap.scaled(self.scale * pixmapSize, QtCore.Qt.KeepAspectRatio)
        self.frame.setPixmap(newpixmap)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWidget = QtWidgets.QStackedWidget()
    MainWindow = MainWindow()
    GraphInputWindow = GraphInputWindow()
    MainWidget.addWidget(MainWindow)
    MainWidget.addWidget(GraphInputWindow)
    MainWidget.setFixedSize(1000, 700)
    MainWidget.setWindowTitle("MrAutoMaton")
    MainWidget.setWindowIcon(QtGui.QIcon(resource_path("Resources/logo.png")))
    MainWidget.show()
    atexit.register(cleanFiles)
    sys.exit(app.exec_())