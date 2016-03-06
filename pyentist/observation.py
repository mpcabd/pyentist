import time


class Observation(object):

    def __init__(self, name, experiment, callback):
        self.name = name
        self.experiment = experiment
        self.callback = callback
        self.now = time.time()

        try:
            self._returned_value = self.callback()
        except Exception as e:
            self._raised_exception = e

        self.duration = time.time() - self.now

    def __hash__(self):
        return sum(map(hash, [self.returned_value, self.raised_exception, self.__class__]))

    def is_equivalent_to(self, other, comparer=None):
        if not isinstance(other, Observation):
            return False

        values_are_equal = False
        both_raised = self.raised_exception and other.raised_exception
        neither_raised = not self.raised_exception and not other.raised_exception

        if neither_raised:
            if comparer:
                values_are_equal = comparer(self.returned_value, other.returned_value)
            else:
                values_are_equal = self.returned_value == other.returned_value
            return values_are_equal
        elif both_raised:
            return (
                self.raised_exception.__class__ == other.raised_exception.__class__
                and str(self.raised_exception) == str(other.raised_exception)
            )
        return False

    @property
    def raised_exception(self):
        if not hasattr(self, '_raised_exception'):
            return None
        return self._raised_exception

    @property
    def returned_value(self):
        if not hasattr(self, '_returned_value'):
            return
        return self._returned_value

    @property
    def cleaned_value(self):
        if self.returned_value:
            return self.experiment.clean_value(self.returned_value)
