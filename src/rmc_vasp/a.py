class Try:
    ccc = "ccccc"

    def __init__(self):
        self._a = "aaaaa"

    def run(self):
        print(self._a)


if __name__ == "__main__":
    t1 = Try()
    # t1.a = "bbb"
    # t1.run()
    # print(t1.a)

    print(Try.ccc)
    Try.ccc = "nakada"
    print(Try.ccc)

    Try.ccc = "kobayhashi"
    print(Try.ccc)
