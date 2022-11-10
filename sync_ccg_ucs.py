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

    # print(ucs_file[0], end="")
    for line in filter(lambda l: not l.startswith("c "), ucs_file[1:]):
        for a in map(int, line.strip(" \n").split(" ")):
            if a > 0:
                print(maps[a], end=" ")
            else:
                print(f"-{maps[abs(a)]}", end=" ")
        print()
    # for (a, _) in ucs.items():
    #    print(f"c {a} {")


    ###i = int(sys.argv[1])
    ###ucs_file = list(open(sys.argv[2], "r").readlines())
    ###ucs = {
    ###    l[i]: int(l[i + 1])
    ###    for l in map(
    ###        lambda l: l.rstrip("\n").split(" ")[1:],
    ###        filter(lambda l: l.startswith("c "), ucs_file),
    ###    )
    ###}
    ###j = int(sys.argv[3])
    ###ccg = {
    ###    l[j]: int(l[j + 1])
    ###    for l in map(
    ###        lambda l: l.rstrip("\n").split(" ")[1:],
    ###        filter(lambda l: l.startswith("c "), open(sys.argv[4], "r").readlines()),
    ###    )
    ###}

    ###maps = {
    ###    v_ucs: v_ccg
    ###    for (k_ucs, v_ucs) in ucs.items()
    ###    for (k_ccg, v_ccg) in ccg.items()
    ###    if k_ucs == k_ccg
    ###}

    #### print(ucs_file[0], end="")
    ###for line in filter(lambda l: not l.startswith("c "), ucs_file[1:]):
    ###    for a in map(int, line.strip(" \n").split(" ")):
    ###        if a > 0:
    ###            print(maps[a], end=" ")
    ###        else:
    ###            print(f"-{maps[abs(a)]}", end=" ")
    ###    print()
    #### for (a, _) in ucs.items():
    ####    print(f"c {a} {")
