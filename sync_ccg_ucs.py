if __name__ == "__main__":
    import sys


    ucs_file = list(open(sys.argv[1], "r").readlines())
    ucs = {
        l[1]: int(l[0])
        for l in map(
            lambda l: l.rstrip("\n").split(" ")[1:],
            filter(lambda l: l.startswith("c "), ucs_file),
        )
    }
    ccg = {
        l[1]: int(l[0])
        for l in map(
            lambda l: l.rstrip("\n").split(" ")[1:],
            filter(lambda l: l.startswith("c "), open(sys.argv[2], "r").readlines()),
        )
    }

    maps = {
        v_ucs: v_ccg
        for (k_ucs, v_ucs) in ucs.items()
        for (k_ccg, v_ccg) in ccg.items()
        if k_ucs == k_ccg
    }

    for line in filter(lambda l: not l.startswith("c "), ucs_file[1:]):
        for a in map(int, line.strip(" \n").split(" ")):
            if a > 0:
                a_ = maps.get(a, None)
                if a_: print(a, end=" ")
                else: continue
                #print(maps[a], end=" ")
            else:
                a_ = maps.get(-a, None)
                if a_: print(-a, end=" ")
                else: continue
                #print(f"-{maps[abs(a)]}", end=" ")
        print()
