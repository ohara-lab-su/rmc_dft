
def reach_threshold(inp):
    norm_threshold = 1e-3
    if inp < norm_threshold:
        return 1
    else:
        return 0
