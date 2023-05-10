from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.uic import loadUi
import pydot
import os
from collections import defaultdict
import graphviz
import atexit
import copy
import re


def cleanFiles():
    try:
        os.remove("Resources/graph.svg")
        os.remove("Resources/graph.dot")
        os.remove("Resources/PDA.svg")
        os.remove("Resources/PDA.dot")
    except Exception:
        pass


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
        self.pushButton_2.clicked.connect(self.switchWindow2)

    def switchWindow(self):
        MainWidget.setCurrentIndex(1)

    def switchWindow2(self):
        MainWidget.setCurrentIndex(2)


class GraphInputWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(GraphInputWindow, self).__init__()
        loadUi(resource_path("UI Files/GraphInput.ui"), self)
        self.addEdgeBtn.clicked.connect(self.addEdge_click)
        self.addNodeBtn.clicked.connect(self.addNode_click)
        self.resetBtn.clicked.connect(self.reset_click)
        self.convertBtn.clicked.connect(self.convert_click)
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
        self.downloadBtn.clicked.connect(self.download_click)
        self.graphEdges = {}
        self.graphEdges = defaultdict(lambda: list(), self.graphEdges)
        self.startNode = ""
        self.finalNodes = []
        self.nodes = []
        lay = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.frame)
        self.scrollArea.setWidgetResizable(True)
        self.frame.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.scale = 1.0
        self.transitionTable = defaultdict(lambda: defaultdict(lambda: list()))
        self.dfaTable = defaultdict(lambda: defaultdict(lambda: ""))
        self.transitions = set()
        self.convertCheck = True

    def back_click(self):
        MainWidget.setCurrentIndex(0)

    def reset_click(self):
        self.graphEdges = {}
        self.graphEdges = defaultdict(lambda: list(), self.graphEdges)
        self.startNode = ""
        self.finalNodes = []
        self.nodes = []
        self.scale = 1.0
        self.transitionTable = defaultdict(lambda: defaultdict(lambda: list()))
        self.dfaTable = defaultdict(lambda: defaultdict(lambda: ""))
        self.transitions = set()
        self.draw_graph()
        self.graphvizGraph.clear()
        self.graphEdges.clear()
        cleanFiles()

    def draw_graph(self):
        self.graphvizGraph.save(filename="Resources/graph.dot")
        dotGraph = pydot.graph_from_dot_file("Resources/graph.dot")[0]
        self.graphEdges.clear()
        if len(dotGraph.get_edges()) > 0:
            for edge in dotGraph.get_edges():
                if edge.get_source() == '""': continue
                self.graphEdges[(edge.get_source(), edge.get_destination())].append(edge.get('label').replace('"', "").replace(' ', ""))
        dotGraph.write_svg("Resources/graph.svg")
        self.frame.setPixmap(QtGui.QPixmap("Resources/graph.svg"))

    def addEdge_click(self):
        if self.convertCheck:
            self.convertCheck = False
            self.reset_click()
        try:
            inputs = self.inputEdge.text()
            decompose = inputs.split(",")
            if len(decompose) > 3: raise Exception
            if str(decompose[2]) in self.graphEdges[(str(decompose[0]), str(decompose[1]))]:
                self.error_popup("Edge Already Added!!")
                return
            self.graphvizGraph.edge(str(decompose[0]), str(decompose[1]), label=str(" "+decompose[2]))
            self.transitions.add(decompose[2])
            self.draw_graph()
        except Exception as e:
            print(e)
            self.error_popup("Please Enter Edge In Correct Format", "Format Example: 1,2,A or 2,5,B")

    def addNode_click(self):
        if self.convertCheck:
            self.convertCheck = False
            self.reset_click()
        try:
            node = self.inputNode.text()
            if node.find(" ") != -1: raise Exception
            if node in self.nodes:
                self.error_popup("Node Already Added!!")
                return
            if self.nodeType.currentText() == "Starting":
                if self.startNode != "": raise Exception
                self.graphvizGraph.node(str(node), color="red", fontcolor="red")
                self.graphvizGraph.node("", width="0.01", height="0.01")
                self.graphvizGraph.edge("", str(node), label="")
                self.startNode = node
            elif self.nodeType.currentText() == "Final":
                self.graphvizGraph.node(node, color="darkgreen", fontcolor="darkgreen", shape="doublecircle")
                self.finalNodes.append(node)
            else: self.graphvizGraph.node(node)
            self.nodes.append(node)
            self.draw_graph()
        except Exception as e:
            print(e)
            self.error_popup("Please Enter Node In Correct Format", "Format Example: 1 or 2\n\nNotes:\n"
                                                                    "1) No spaces are allowed\n"
                                                                    "2) No more than 1 starting node")

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
        pixmap = QtGui.QPixmap("Resources/graph.svg")
        pixmapSize = pixmap.size()
        newpixmap = pixmap.scaled(self.scale * pixmapSize, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.frame.setPixmap(newpixmap)

    def convert_click(self, v=False):
        self.convertCheck = True
        if len(self.finalNodes) == 0 or not(self.startNode):
            self.error_popup("Please Make Sure there is One Starting state and At least One Final State!")
            return
        try:
            self.constructTransitionTable()
            visitedNodes = []
            nonVisitedNodes = [[self.startNode]]
            while nonVisitedNodes:
                currNode = nonVisitedNodes.pop()
                if currNode in visitedNodes: continue
                if v:print(f"Curr Node is {currNode}")
                visitedNodes.append(currNode)
                if v:print(f"{currNode} added to visited\n")
                if v:print(f"Curr Visited Nodes {visitedNodes}")
                if v:print(f"Curr Non Visited Nodes {nonVisitedNodes}\n")
                miniTrans = defaultdict(lambda: list())
                for node in currNode:
                    for transition, nodes in self.transitionTable[node].items():
                        miniTrans[transition].extend(nodes)
                        miniTrans[transition] = [*set(miniTrans[transition])]
                for transition, nodes in miniTrans.items():
                    self.dfaTable[str(currNode)][str(transition)] = str(nodes)
                    if v:print(f"Adding Rule to table {currNode}\n\t{transition} -> {nodes}\n")
                    if self.finalNodes[0] in nodes: self.finalNodes.append(nodes)
                    if (nodes in visitedNodes) or (nodes == currNode) or (nodes in nonVisitedNodes):continue
                    if v:print(f"Appending {nodes} to Non Visited Nodes\n")
                    nonVisitedNodes.append(nodes)
                    if v:print(f"Curr Visited Nodes {visitedNodes}")
                    if v:print(f"Curr Non Visited Nodes {nonVisitedNodes}\n")
            self.displayDFA()
        except Exception as e:
            print(e)
            self.reset_click()
            self.error_popup("Make Sure you entered the NFA Correctly!")

    def constructTransitionTable(self):
        for (node1, node2), transitions in self.graphEdges.items():
            for transition in transitions:
                self.transitionTable[str(node1)][str(transition)].append(str(node2))

    def displayDFA(self):
        self.graphEdges = {}
        self.graphEdges = defaultdict(lambda: list(), self.graphEdges)
        self.nodes = []
        self.scale = 1.0
        self.transitionTable = defaultdict(lambda: defaultdict(lambda: list()))
        self.graphvizGraph.clear()
        self.graphEdges.clear()
        for node, transitionDict in self.dfaTable.items():
            for transition in self.transitions:
                if self.dfaTable[node][transition]:
                    self.graphvizGraph.edge(str(node), str(self.dfaTable[node][transition]), label=str(" "+transition))
                else:
                    self.graphvizGraph.edge(str(node), "Failed", label=str(" " + transition))
        self.graphvizGraph.node(str([self.startNode]), color="red", fontcolor="red")
        self.graphvizGraph.node("", width="0.01", height="0.01")
        self.graphvizGraph.edge("", str([self.startNode]), label="")
        if self.startNode in self.finalNodes: self.finalNodes.append([self.startNode])
        for finNode in self.finalNodes[1:]:
            self.graphvizGraph.node(str(finNode), color="darkgreen", fontcolor="darkgreen", shape="doublecircle")
        self.startNode = ""
        self.finalNodes = []
        self.draw_graph()

    def download_click(self):
        try:
            options = QtWidgets.QFileDialog.Options()
            options |= QtWidgets.QFileDialog.DontUseNativeDialog
            fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save Image", r"H:\Image", "All Files (*)", options=options
            )
            QtGui.QPixmap("Resources/graph.svg").save(fileName+".svg", "SVG")
        except Exception as e:
            print(e)
            self.error_popup("You should input a graph first!")


class CFGInputWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(CFGInputWindow, self).__init__()
        loadUi(resource_path("UI Files/CFGInput.ui"), self)
        self.backBtn.clicked.connect(self.back_click)

        self.zoomInBtn.clicked.connect(lambda: self.zoom(True))
        self.zoomOutBtn.clicked.connect(lambda: self.zoom(False))
        self.downloadBtn.clicked.connect(self.download_click)
        self.doneBtn.clicked.connect(self.done_click)
        self.addRuleBtn.clicked.connect(self.addRule_click)
        self.convertBtn.clicked.connect(self.convert_click)
        self.addRulesBtn.clicked.connect(self.addRules_click)
        self.resetBtn.clicked.connect(self.reset_click)

        lay = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.frame)
        self.scrollArea.setWidgetResizable(True)
        self.frame.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.scale = 1.0

        self.productionRules = defaultdict(lambda: list(list()))
        self.allSymbols = set()
        self.variables = set()
        self.terminals = set()
        self.startingSymbol = ""
        self.graphvizGraph = graphviz.Digraph()
        self.rules = []
        self.ruleText = ""

    def back_click(self):
        MainWidget.setCurrentIndex(0)

    def reset_click(self):
        self.scale = 1.0
        self.productionRules = defaultdict(lambda: list(list()))
        self.allSymbols = set()
        self.variables = set()
        self.terminals = set()
        self.startingSymbol = ""
        self.graphvizGraph = graphviz.Digraph()
        self.rules = []
        self.ruleText = ""
        cleanFiles()
        self.draw_graph()

    def draw_graph(self):
        self.graphvizGraph.save(filename="Resources/PDA.dot")
        dotGraph = pydot.graph_from_dot_file("Resources/PDA.dot")[0]
        dotGraph.write_svg("Resources/PDA.svg")
        self.frame.setPixmap(QtGui.QPixmap("Resources/PDA.svg"))

    def done_click(self):
        self.inputMenu.setCurrentIndex(1)

    def addRules_click(self):
        self.inputMenu.setCurrentIndex(0)

    def initGrammar(self):

        for ruleInput in self.rules:
            decompose = ruleInput.split("->")
            variable = decompose[0].strip()
            self.variables.add(variable)
            production_list = [prod.strip() for prod in decompose[1] if prod.strip() != '' and prod.strip() != 'ε']
            production_list.reverse()
            self.allSymbols.add(variable)
            for prod in production_list:
                self.allSymbols.add(prod)

            self.productionRules[variable].append(production_list)

        for symbol in self.allSymbols:
            if symbol not in self.variables:
                self.terminals.add(symbol)

        self.startingSymbol = QtWidgets.QInputDialog.getText(MainWindow, "Starting Symbol", f"Enter The starting Symbol for the CFG:")[0]

        if (self.startingSymbol not in self.allSymbols) or (len(self.rules) == 0):
            self.startingSymbol = ""
            self.error_popup("Please Make Sure Symbol Exists in CFG!")
            return False
        return True

    def printCFG(self):
        out_str = ""
        out_str += f"Starting Symbol: {self.startingSymbol}\n"
        out_str += f"Variables: {self.variables}\n"
        out_str += f"Terminals: {self.terminals}\n"
        out_str += f"Production List: {self.productionRules}\n"
        print(out_str)

    def convert_click(self):
        if not self.initGrammar():
            self.error_popup("Please Make sure you have entered a valid CFG")
            return
        self.graphvizGraph.attr(rankdir="LR")
        self.graphvizGraph.node("qStart", color="red", fontcolor="red")
        self.graphvizGraph.node("qAccept", color="darkgreen", fontcolor="darkgreen", shape="doublecircle")
        self.graphvizGraph.node("qLoop", color="blue", fontcolor="blue")

        self.graphvizGraph.edge("qStart", "q1", label=" (ε, ε -> $)")
        self.graphvizGraph.edge("q1", "qLoop", label=f" (ε, ε -> {self.startingSymbol})")
        currMaxNode = 2

        for variable, productions in self.productionRules.items():
            for prod_list in productions:
                tempProduction = copy.deepcopy(prod_list)
                popped = False
                nextNode = "qLoop"
                while tempProduction:
                    currNode = nextNode
                    prod = tempProduction.pop(0)
                    if len(tempProduction) > 0:
                        if not popped:
                            self.graphvizGraph.edge(currNode, f"q{currMaxNode}", label=f" (ε, {variable} -> {prod})")
                            popped = True
                        else:
                            self.graphvizGraph.edge(currNode, f"q{currMaxNode}", label=f" (ε, ε -> {prod})")

                        nextNode = "q" + str(currMaxNode)
                        currMaxNode += 1

                    elif len(tempProduction) == 0:
                        if popped:
                            self.graphvizGraph.edge(currNode, "qLoop", label=f" (ε, ε -> {prod})")
                        else:
                            self.graphvizGraph.edge(currNode, "qLoop", label=f" (ε, {variable} -> {prod})")

        for terminal in self.terminals:
            self.graphvizGraph.edge("qLoop", "qLoop", label=f" ({terminal}, {terminal} -> ε)")

        self.graphvizGraph.edge("qLoop", "qAccept", label=" (ε, $ -> ε)")
        self.draw_graph()

    def addRule_click(self):
        rule = self.inputRules.text()
        if not re.match(r"[A-Za-z] -> [A-Za-z]+", rule):
            self.error_popup("Please Enter Rule in Correct Format!!", "Variable -> Productions\nEx: S -> aAa")
            return
        if rule in self.rules:
            self.error_popup("Rule has already been added")
            return
        self.rules.append(rule)
        self.ruleText += f"{rule}\n"
        self.graphvizGraph.attr(label=self.ruleText)
        self.draw_graph()

    def error_popup(self, err_msg, extra=""):
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
        pixmap = QtGui.QPixmap("Resources/PDA.svg")
        pixmapSize = pixmap.size()
        newpixmap = pixmap.scaled(self.scale * pixmapSize, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.frame.setPixmap(newpixmap)

    def download_click(self):
        try:
            options = QtWidgets.QFileDialog.Options()
            options |= QtWidgets.QFileDialog.DontUseNativeDialog
            fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save Image", r"H:\Image", "All Files (*)", options=options
            )
            QtGui.QPixmap("Resources/PDA.svg").save(fileName+".svg", "SVG")
        except Exception as e:
            print(e)
            self.error_popup("You should input a graph first!")


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWidget = QtWidgets.QStackedWidget()
    MainWindow = MainWindow()
    GraphInputWindow = GraphInputWindow()
    CFGInputWindow = CFGInputWindow()
    MainWidget.addWidget(MainWindow)
    MainWidget.addWidget(GraphInputWindow)
    MainWidget.addWidget(CFGInputWindow)
    MainWidget.setFixedSize(1000, 700)
    MainWidget.setWindowTitle("MrAutoMaton")
    MainWidget.setWindowIcon(QtGui.QIcon(resource_path("Resources/logo.png")))
    MainWidget.show()
    atexit.register(cleanFiles)
    os.environ["PATH"] += os.pathsep + resource_path('bin')
    sys.exit(app.exec_())
