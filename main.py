import clingoext
import networkx as nx
import sys


class Rule(object):
    def __init__(self, head, body):
        self.head = head
        self.body = body

    def __repr__(self):
        return "; ".join([str(a) for a in self.head]) + ":- " + ", ".join([("not " if b < 0 else "") + str(abs(b)) for b in self.body])

class Program(object):
    def __init__(self, clingo_control):
        # the variable counter
        self._max = 0
        self._nameMap = {}
        # store the clauses here
        self._clauses = []
        # remember which variables are guesses and which are derived
        self._guess = set()
        self._deriv = set()
        self._copies = {}
        self._normalize(clingo_control)

    def remove_tautologies(self, clingo_control):
        tmp = []
        for o in clingo_control.ground_program.objects:
            if isinstance(o, clingoext.ClingoRule) and set(o.head).intersection(set(o.body)) == set():
                tmp.append(o)
        return tmp

    def _normalize(self, clingo_control):
        program = self.remove_tautologies(clingo_control)
        self._program = []
        _atomToVertex = {}  # htd wants succinct numbering of vertices / no holes
        _vertexToAtom = {}  # inverse mapping of _atomToVertex
        unary = []

        symbol_map = {}
        for sym in clingo_control.symbolic_atoms:
            symbol_map[sym.literal] = str(sym.symbol)
        for o in program:
            if isinstance(o, clingoext.ClingoRule):
                o.atoms = set(o.head)
                o.atoms.update(tuple(map(abs, o.body)))
                if len(o.body) > 0:
                    self._program.append(o)
                    # add mapping for atom not yet mapped
                    for a in o.atoms.difference(_atomToVertex):
                        if a in symbol_map:
                            _atomToVertex[a] = self.new_var(symbol_map[a])
                        else:
                            _atomToVertex[a] = self.new_var(
                                f"projected_away({a})")
                        _vertexToAtom[self._max] = a
                else:
                    if o.choice:
                        unary.append(o)
        for o in unary:
            self._program.append(o)
            # add mapping for atom not yet mapped
            for a in o.atoms.difference(_atomToVertex):
                _atomToVertex[a] = self.new_var(symbol_map[a])
                _vertexToAtom[self._max] = a

        trans_prog = set()
        for r in self._program:
            if r.choice:
                self._guess.add(_atomToVertex[r.head[0]])
            else:
                head = list(map(lambda x: _atomToVertex[x], r.head))
                body = list(
                    map(lambda x: _atomToVertex[abs(x)]*(1 if x > 0 else -1), r.body))
                trans_prog.add(Rule(head, body))
        self._program = trans_prog
        self._deriv = set(range(1, self._max + 1)).difference(self._guess)

    def new_var(self, name):
        self._max += 1
        self._nameMap[self._max] = name if name != "" else str(self._max)
        return self._max

    def _computeComponents(self):
        self.dep = nx.DiGraph()
        # print(self._program)
        for r in self._program:
            print(r)
            for a in r.head:
                print(a)
                for b in r.body:
                    if b > 0:
                        self.dep.add_edge(b, a)
        comp = nx.algorithms.strongly_connected_components(self.dep)
        self._components = list(comp)
        self._condensation = nx.algorithms.condensation(
            self.dep, self._components)

    def compute_components(self):
        self.dep = nx.DiGraph()

        for r in self._program:
            for a in r.head:
                for b in r.body:
                    self.dep.add_edge(b, a)
        comp = nx.algorithms.strongly_connected_components(self.dep)
        self._components = list(comp)
        self._condensation = nx.algorithms.condensation(self.dep, self._components)

   # def _computeComponents_hack(self):
   #     self.dep = nx.DiGraph()
   #     for r in self._program:
   #         for a in r.head:
   #             for b in r.body:  # all body atoms of form: not not atom
   #                 self.dep.add_edge(b, a)
   #     comp = nx.algorithms.strongly_connected_components(self.dep)
   #     self._components = list(comp)
   #     self._condensation = nx.algorithms.condensation(
   #         self.dep, self._components)

    def clark_completion(self):
        perAtom = {}
        for a in self._deriv:
            perAtom[a] = []

        for r in self._program:
            for a in r.head:
                perAtom[a].append(r)

        for head in self._deriv:
            ors = []
            for r in perAtom[head]:
                ors.append(self.new_var(f"{r}"))
                ands = [-x for x in r.body]
                self._clauses.append([ors[-1]] + ands)
                for at in ands:
                    self._clauses.append([-ors[-1], -at])
            self._clauses.append([-head] + [o for o in ors])
            for o in ors:
                self._clauses.append([head, -o])

        constraints = [r for r in self._program if len(r.head) == 0]
        for r in constraints:
            self._clauses.append([-x for x in r.body])


if __name__ == "__main__":
    ctl = clingoext.Control()
    with open(sys.argv[1], 'r') as f:
        ctl.add("base", [], f.read())
        ctl.ground([('base', [])])

    program = Program(ctl)
    program.compute_components()
    deps = program.dep

    simple_cycles = list(map(frozenset, nx.simple_cycles(deps)))
    components = set(map(frozenset, deps.edges()))
    cycle_free_components = components.difference(simple_cycles)
                    

    for (i,a) in program._nameMap.items():
        print(f"c {i} {a}")
    opt = sys.argv[2]
    if opt == "-sc": 
        # external_supports = dict()
        for cycle in simple_cycles:
            for node in cycle: 
                print(node, end=" ")
            for edge in cycle_free_components:
                if set(edge).intersection(cycle):
                    for lit in set(edge).difference(cycle):
                        # external_supports.append(-lit)
                        print(-lit, end=" ")
            print()
    elif opt == "-ac":
        pass
    else:
        print(f"unknown option: {opt}")


    #print(deps.nodes)
    #sscs = program._components
    #cycles = nx.simple_cycles(deps)
    #print(find_all_cycles(deps))
    # components = set(map(frozenset,deps.edges()))

    
