from collections import defaultdict
import graphviz
import copy
import pydot
import os
import sys


def clean_files():
    os.remove("Resources/PDA.svg")
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
        self.productionRules = defaultdict(lambda: list(list()))
        self.allSymbols = set()
        self.variables = set()
        self.terminals = set()
        self.startingSymbol = ""
        self.graphvizGraph = graphviz.Digraph()

    def init_grammar(self, rules, starting_symbol: str = None):
        for ruleInput in rules:
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

        if starting_symbol:
            self.startingSymbol = starting_symbol
        else:
            for variable in self.variables:
                check = True
                for prod in self.productionRules.values():
                    if variable in prod:
                        check = False
                if check:
                    self.startingSymbol = variable

    def construct_pda(self):
        self.graphvizGraph.attr(rankdir="LR")
        self.graphvizGraph.node("qStart", color="red", fontcolor="red")
        self.graphvizGraph.node("qAccept", color="darkgreen", fontcolor="darkgreen", shape="doublecircle")
        self.graphvizGraph.node("qLoop", color="blue", fontcolor="blue")

        self.graphvizGraph.edge("qStart", "q1", label=" (ε, ε -> $)")
        self.graphvizGraph.edge("q1", "qLoop", label=f" (ε, ε -> {grammar.startingSymbol})")
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

        self.graphvizGraph.save(filename="Resources/PDA.dot")
        dotGraph = pydot.graph_from_dot_file("Resources/PDA.dot")[0]
        dotGraph.write_svg("Resources/PDA.svg")

    def __str__(self):
        out_str = ""
        out_str += f"Starting Symbol: {self.startingSymbol}\n"
        out_str += f"Variables: {self.variables}\n"
        out_str += f"Terminals: {self.terminals}\n"
        out_str += f"Production List: {self.productionRules}\n"
        return out_str


if __name__ == "__main__":

    # atexit.register(clean_files)
    os.environ["PATH"] += os.pathsep + resource_path('bin')

    # rules = ["S -> Aaa", "A -> Bbb", "B -> c"]
    rules = ["S -> aSb", "S -> A", "A -> aA", "A -> ε"]
    grammar = CFG()
    grammar.init_grammar(rules, "S")

    grammar.construct_pda()
