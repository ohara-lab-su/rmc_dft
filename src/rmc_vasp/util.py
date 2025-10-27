def reach_threshold(inp):
    """
    Threshold that stops calculation.

    :param inp: Current value.
    :type inp: float
    :return: Returns 1 (break) or 0 (continue).
    :rtype: int
    """
    norm_threshold = 1e-3
    if inp < norm_threshold:
        return 1
    else:
        return 0
