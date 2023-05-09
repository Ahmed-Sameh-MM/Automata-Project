from collections import defaultdict
import graphviz
import copy
import pydot
import os
import atexit
import sys


def cleanFiles():
    os.remove("Resources/PDA.png")
    os.remove("Resources/PDA.dot")


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class CFG:
    def __init__(self):
        self.productionRules = defaultdict(lambda: list())
        self.allSymbols = set()
        self.variables = set()
        self.terminals = set()
        self.startingSymbol = ""

    def init_grammar(self, rules):
        for ruleInput in rules:
            decompose = ruleInput.split("->")
            variable = decompose[0].strip()
            self.variables.add(variable)
            production_list = [prod.strip() for prod in decompose[1] if prod.strip() != '']
            production_list.reverse()
            self.allSymbols.add(variable)
            for prod in production_list:
                self.allSymbols.add(prod)
            self.productionRules[variable] = production_list

        for symbol in self.allSymbols:
            if symbol not in self.variables:
                self.terminals.add(symbol)

        for variable in self.variables:
            check = True
            for prod in self.productionRules.values():
                if variable in prod:
                    check = False
            if check:
                self.startingSymbol = variable

    def __str__(self):
        out_str = ""
        out_str += f"Starting Symbol: {self.startingSymbol}\n"
        out_str += f"Variables: {self.variables}\n"
        out_str += f"Terminals: {self.terminals}\n"
        out_str += f"Production List: {self.productionRules}\n"
        return out_str


if __name__ == "__main__":

    # atexit.register(cleanFiles)
    os.environ["PATH"] += os.pathsep + resource_path('bin')

    rules = ["S -> Aaa", "A -> Bbb", "B -> c"]
    # rules = ["S -> aSb", "S -> A", "A -> aA", "A -> ε"]
    grammar = CFG()
    grammar.init_grammar(rules)
    # grammar.startingSymbol = "S"

    graphvizGraph = graphviz.Digraph()
    graphvizGraph.edge("qStart", "q1", label=" (ε, ε -> $)")
    graphvizGraph.edge("q1", "qLoop", label=f" (ε, ε -> {grammar.startingSymbol})")
    currMaxNode = 2
    for variable, productions in grammar.productionRules.items():
        tempProduction = copy.deepcopy(productions)
        popped = False
        nextNode = "qLoop"
        while tempProduction:
            currNode = nextNode
            prod = tempProduction.pop(0)
            if len(tempProduction)+1 > 1:
                if not popped:
                    graphvizGraph.edge(currNode, f"q{currMaxNode}", label=f" (ε, {variable} -> {prod})")
                    nextNode = "q"+str(currMaxNode)
                    currMaxNode += 1
                    popped = True
                else:
                    graphvizGraph.edge(currNode, f"q{currMaxNode}", label=f" (ε, ε -> {prod})")
                    nextNode = "q"+str(currMaxNode)
                    currMaxNode += 1

            elif len(tempProduction)+1 == 1:
                if popped:
                    graphvizGraph.edge(currNode, "qLoop", label=f" (ε, ε -> {prod})")
                else:
                    graphvizGraph.edge(currNode, "qLoop", label=f" (ε, {variable} -> {prod})")

        for terminal in grammar.terminals:
            graphvizGraph.edge("qLoop", "qLoop", label=f" ({terminal}, {terminal} -> ε)")

    graphvizGraph.edge("qLoop", "qAccept", label=" (ε, $ -> ε)")

    graphvizGraph.save(filename="Resources/PDA.dot")
    dotGraph = pydot.graph_from_dot_file("Resources/PDA.dot")[0]
    dotGraph.write_png("Resources/PDA.png")
