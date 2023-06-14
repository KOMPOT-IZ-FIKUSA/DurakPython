class A:
    def __init__(self, vala):
        self.vala = vala

    def f(self):
        print(self.vala)

class B:
    def __init__(self, valb):
        self.valb = valb

    def g(self):
        print(self.valb)

class C(A, B):
    def __init__(self, vala, valb):
        super().__init__(vala)

        print(self.g)


c = C(1, 2)