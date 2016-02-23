from .experiment import Experiment


class DefaultExperiment(Experiment):

    def __init__(self, name):
        self.name = name

    def is_enabled(self):
        return True

    def publish(self, result):
        pass
