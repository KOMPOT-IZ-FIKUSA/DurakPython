import log


class SignalHandler:
    def __init__(self, true_signal):
        self.signal = true_signal
        self.args_queue = []
        self.kwargs_queue = []
        self.functions_queue = []
        self.running_stack_currently = False

        def f():
            while len(self.kwargs_queue) > 0:
                function = self.functions_queue[0]
                args = self.args_queue[0]
                kwargs = self.kwargs_queue[0]
                try:
                    function(*args, **kwargs)
                except Exception as e:
                    log.error("error in signal emit queue", e, function=function, args=args, kwargs=kwargs,
                              functions_queue_size=len(self.functions_queue))
                self.functions_queue.pop(0)
                self.args_queue.pop(0)
                self.kwargs_queue.pop(0)
            self.running_stack_currently = False

        self.signal.connect(f)

    def add(self, function, *args, **kwargs):
        self.functions_queue.append(function)
        self.args_queue.append(args)
        self.kwargs_queue.append(kwargs)

    def emit(self):
        if not self.running_stack_currently:
            self.running_stack_currently = True
            self.signal.emit()

    def wait(self):
        while len(self.functions_queue) > 0:
            pass

    def contains_function(self, function):
        for f in self.functions_queue:
            if f == function:
                return True
        return False