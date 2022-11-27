import clingoext
import networkx as nx
import sys


class Rule(object):
    def __init__(self, head, body):
        self.head = head
        self.body = body

    def __repr__(self):
        return (
            "; ".join([str(a) for a in self.head])
            + ":- "
            + ", ".join([("not " if b < 0 else "") + str(abs(b)) for b in self.body])
        )


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
            if (
                isinstance(o, clingoext.ClingoRule)
                and set(o.head).intersection(set(o.body)) == set()
            ):
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
                            _atomToVertex[a] = self.new_var(f"projected_away({a})")
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
                    map(lambda x: _atomToVertex[abs(x)] * (1 if x > 0 else -1), r.body)
                )
                trans_prog.add(Rule(head, body))
        self._program = trans_prog
        self._deriv = set(range(1, self._max + 1)).difference(self._guess)

    def new_var(self, name):
        self._max += 1
        self._nameMap[self._max] = name if name != "" else str(self._max)
        return self._max

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

    def _computeComponents(self):
        self.dep = nx.DiGraph()
        # print(self._program)
        for r in self._program:
            # print(r)
            for a in r.head:
                # print(a)
                for b in r.body:
                    if b > 0:
                        self.dep.add_edge(b, a)
        comp = nx.algorithms.strongly_connected_components(self.dep)
        self._components = list(comp)
        self._condensation = nx.algorithms.condensation(self.dep, self._components)

    def compute_components(self):
        self.dep = nx.DiGraph()

        for r in self._program:
            for a in r.head:
                for b in r.body:
                    self.dep.add_edge(b, a)
            #print(r,"|||",*list(map(lambda i: self._nameMap[i], r.head))," :- ",*list(map(lambda i: "not " +self._nameMap[abs(i)] if i < 0 else self._nameMap[i], r.body)))
        comp = nx.algorithms.strongly_connected_components(self.dep)
        self._components = list(comp)
        self._condensation = nx.algorithms.condensation(self.dep, self._components)


####################################

    def dp_supps_sccs(self):
        supps = dict()
        self.dep = nx.DiGraph()
        for r in self._program:
            for a in r.head:
                if supps.get(a,None):
                    supps[a].extend(r.body)
                else: 
                    supps[a] = r.body
                for b in r.body:
                    if b > 0:
                        self.dep.add_edge(b, a)
        #comp = nx.algorithms.strongly_connected_components(self.dep)
        #self._components = list(comp)
        #self._condensation = nx.algorithms.condensation(self.dep, self._components)
        #return (self.dep,supps,self._components)
        return (self.dep,supps)




if __name__ == "__main__":
    ctl = clingoext.Control()
    with open(sys.argv[1], "r") as f:
        ctl.add("base", [], f.read())
        ctl.ground([("base", [])])
    with open(sys.argv[2], "r") as f:
        ls = [l.split(" ") for l in f.readlines() if l.startswith("c ")]
        CCG_MAPPINGS = {l[2].strip(): int(l[1]) for l in ls}

    #lp = Program(ctl)
    #lp.compute_components()
    ##lp._computeComponents()
    #dependency_graph = lp.dep
    #LP_MAPPINGS = lp._nameMap

    #simple_cycles = list(map(frozenset, nx.simple_cycles(dependency_graph)))
    #components = set(map(frozenset, dependency_graph.edges()))
    #cycle_free_components = components.difference(simple_cycles)

    lp = Program(ctl)
    LP_MAPPINGS = lp._nameMap
    #dependency_graph, supports, sccs = lp.dp_supps_sccs()
    dependency_graph, supports = lp.dp_supps_sccs()


    def atomify(node: int) -> str:
        if node < 0:
            return "-"+lp._nameMap[abs(node)]
        return lp._nameMap[node]

    def write(loop):
        print(*map(lambda a: CCG_MAPPINGS[LP_MAPPINGS[a]], loop), end=" ") # write cyclic atoms
        #print(*map(lambda a: atomify(a), loop), end=" ") # write cyclic atoms
        external_supports = set().union(*map(set, [list(filter(lambda l: not abs(l) in loop, supports[a])) for a in loop]))
        print(*map(lambda l: -CCG_MAPPINGS[LP_MAPPINGS[l]] if l > 0 else CCG_MAPPINGS[LP_MAPPINGS[-l]], external_supports))
        #print(*map(lambda l: "-"+atomify(l) if l > 0 else atomify(-l), external_supports))

        #for atom_ in cycle:  # write cyclic atoms
        #    atom = CCG_MAPPINGS[LP_MAPPINGS[atom_]]
        #    print(atom, end=" ")
        #    print(*map(lambda l: -CCG_MAPPINGS[LP_MAPPINGS[l]] if l > 0 else CCG_MAPPINGS[LP_MAPPINGS[-l]], supports[atom_]))

    def write_ucs_body(cycle):
        for atom_ in cycle:  # writing cyclic atoms
            atom = CCG_MAPPINGS[LP_MAPPINGS[atom_]]
            print(atom, end=" ")
        for edge in cycle_free_components:
            sedge = set(edge)
            if sedge.intersection(cycle):
                for lit in sedge.difference(cycle):
                    a = LP_MAPPINGS[abs(lit)]
                    if not "projected_away" in a:
                        external_support = CCG_MAPPINGS[a]
                        print(-external_support, end=" ")
        print()

    def write_ucs_body_atoms(cycle):
        for atom_ in cycle:  # writing cyclic atoms
            atom = LP_MAPPINGS[atom_]
            print(atom, end=" ")
        for edge in cycle_free_components:
            sedge = set(edge)
            if sedge.intersection(cycle):
                for lit in sedge.difference(cycle):
                    a = LP_MAPPINGS[abs(lit)]
                    if not "projected_away" in a:
                        external_support = a if lit < 0 else "-"+a
                        print(external_support, end=" ")
        print()




    #print("c o supports")
    #for k,v in supports.items():
    #    print(atomify(k), list(map(atomify, v)))
    #print("c o positive dependency graph")
    simple_loops = set(map(frozenset, nx.simple_cycles(dependency_graph)))
    list(map(write,simple_loops))

    #print(simple_cycles)
    #print("c o simple cycles")
    #print(*[set(map(atomify, sc)) for sc in simple_cycles])
    #print("c o strongly connected components")
    #print(*[set(map(atomify, scc)) for scc in sccs])


        

    #print(sccs)
    #print(l2)
    #for l in l2:
    #    write_ucs_body_atoms(l)
    #


    #print(f"ucs {len(simple_cycles)}")
    """
    iter = sys.argv.__iter__() 
    for _ in range(3): next(iter)
    if next(iter,None) == "--v+at":
        n = 0
        for cycle in simple_cycles:
            write_ucs_body_atoms(cycle)
            intersecting = [c.union(cycle) for c in simple_cycles if c.intersection(cycle) and c!=cycle]
            for c in intersecting:
                n+=1
                write_ucs_body_atoms(c)
        print(f"{len(simple_cycles)} {n}")
    elif next(iter,None) == "--at":
        for cycle in simple_cycles:
            write_ucs_body_atoms(cycle)
            intersecting = [c.union(cycle) for c in simple_cycles if c.intersection(cycle) and c!=cycle]
            for c in intersecting:
                write_ucs_body_atoms(c)
    else:
        for cycle in simple_cycles:
            write_ucs_body(cycle)
            intersecting = [c.union(cycle) for c in simple_cycles if c.intersection(cycle) and c!=cycle]
            for c in intersecting:
                write_ucs_body(c)
    """
        #for c in simple_cycles:
        #    if c.intersection(cycle) and c!=cycle:
        #        print(c)
        #for l in map(
        #    lambda l: cycle.union(l),
        #    filter(lambda l: cycle.intersection(l), simple_cycles[i + 1 :]),
        #):
        #    write_ucs_body(l)
        #print()
        #if i==2: exit(0)

    # print(simple_cycles)
    # print(loops)
    # print(f"ucs {len(simple_cycles)} {len(loops)}")

    #import itertools
    ##strongly connected components of size >= 2
    #sccs = list(filter(lambda scc: len(scc) >= 2, lp._components))
    #l2 = []
    #for scc in sccs: 
    #    l2.append(scc)
    #    n = 2 
    #    while n < len(scc): 
    #        for sub_loop in map(set, itertools.combinations(scc, n)): 
    #            l2.append(sub_loop) 
    #            n+=1
    #map(write_ucs_body_atoms, sccs)
    #for l in l2:
    #    write_ucs_body_atoms(l)
    #    intersecting = [c.union(l) for c in l2 if c.intersection(l) and c!=l]
    #    map(write_ucs_body_atoms,intersecting)


    #print("c o positive dependency grap")
    #print(*[list(map(atomify, edge)) for edge in dependency_graph.edges])
    """
    program = Program(ctl)
    program.compute_components()
    #program._computeComponents()
    deps = program.dep

    print(program._nameMap)
    for n in nx.strongly_connected_components(deps): print(n)

    simple_cycles = list(map(frozenset, nx.simple_cycles(deps)))
    components = set(map(frozenset, deps.edges()))
    cycle_free_components = components.difference(simple_cycles)
                    

    for (i,a) in program._nameMap.items():
        print(i,a,mappings[program._nameMap[i]])
    #print(program._nameMap)
    for cycle in simple_cycles:
        for node in cycle: 
            l = mappings[program._nameMap[node]]
            #print("c",node, i_)
            print(l, end=" ")
            #print(node, end=" ")
        for edge in cycle_free_components:
            if set(edge).intersection(cycle):
                for lit in set(edge).difference(cycle):
                    # external_supports.append(-lit)
                    l = mappings[program._nameMap[lit]]
                    #print(-lit, end=" ")
                    print(-l, end=" ")
        print()
    """
    """
    for (i,a) in program._nameMap.items():
        print(f"c {i} {a}")
    for cycle in simple_cycles:
        for node in cycle: 
            print(node, end=" ")
        for edge in cycle_free_components:
            if set(edge).intersection(cycle):
                for lit in set(edge).difference(cycle):
                    # external_supports.append(-lit)
                    print(-lit, end=" ")
        print()
    """

    ###for (i,a) in program._nameMap.items():
    ###    print(f"c {i} {a}")
    ###opt = sys.argv[2]
    ###if opt == "-sc":
    ###    # external_supports = dict()
    ###    for cycle in simple_cycles:
    ###        for node in cycle:
    ###            print(node, end=" ")
    ###        for edge in cycle_free_components:
    ###            if set(edge).intersection(cycle):
    ###                for lit in set(edge).difference(cycle):
    ###                    # external_supports.append(-lit)
    ###                    print(-lit, end=" ")
    ###        print()
    ###elif opt == "-ac":
    ###    pass
    ###else:
    ###    print(f"unknown option: {opt}")

    # print(deps.nodes)
    # sscs = program._components
    # cycles = nx.simple_cycles(deps)
    # print(find_all_cycles(deps))
    # components = set(map(frozenset,deps.edges()))
