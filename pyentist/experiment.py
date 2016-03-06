import random

from .observation import Observation
from .result import Result
from .errors import BehaviorNotUniqueError, BehaviorMissingError, MismatchError


class Experiment(object):
    raise_on_mismatch = False

    def __init__(self, name="experiment"):
        self.name = name

    def is_enabled(self):
        raise NotImplementedError('Must be implmented in child class')

    def publish(self, result):
        raise NotImplementedError('Must be implmented in child class')

    @property
    def context(self):
        if not hasattr(self, '_context'):
            self._context = {}
        return self._context

    @context.setter
    def context(self, new_context):
        if not hasattr(self, '_context'):
            self._context = {}
        self._context.update(new_context or {})

    @property
    def returned_value(self):
        if not hasattr(self, '_returned_value'):
            return
        return self._returned_value

    @returned_value.setter
    def returned_value(self, value):
        self._returned_value = value

    @property
    def result(self):
        if not hasattr(self, '_result'):
            return
        return self._result

    @result.setter
    def result(self, value):
        self._result = value

    @property
    def before_run(self):
        if not hasattr(self, '_before_run'):
            self._before_run = None
        return self._before_run

    @before_run.setter
    def before_run(self, func):
        self._before_run = func

    @property
    def behaviors(self):
        if not hasattr(self, '_behaviors'):
            self._behaviors = {}
        return self._behaviors

    @property
    def cleaner(self):
        if not hasattr(self, '_cleaner'):
            self._cleaner = None
        return self._cleaner

    @cleaner.setter
    def cleaner(self, func):
        self._cleaner = func

    @property
    def comparer(self):
        if not hasattr(self, '_comparer'):
            self._comparer = None
        return self._comparer

    @comparer.setter
    def comparer(self, func):
        self._comparer = func

    @property
    def should_run_callback(self):
        if not hasattr(self, '_should_run_callback'):
            self._should_run_callback = None
        return self._should_run_callback

    @should_run_callback.setter
    def should_run_callback(self, func):
        self._should_run_callback = func

    @property
    def ignorers(self):
        if not hasattr(self, '_ignorers'):
            self._ignorers = []
        return self._ignorers

    @property
    def should_raise_on_mismatch(self):
        if not hasattr(self, '_should_raise_on_mismatch'):
            return Experiment.raise_on_mismatch
        return self._should_raise_on_mismatch

    @should_raise_on_mismatch.setter
    def should_raise_on_mismatch(self, value):
        self._should_raise_on_mismatch = value

    def are_observations_equivalent(self, observation1, observation2):
        try:
            if self.comparer:
                return self.comparer(observation1, observation2)
            else:
                return observation1 == observation2
        except Exception as e:
            self.raised('comparer', e)
            return False

    def should_ignore_mismatched_observation(self, control, candidate):
        if not self.ignorers:
            return False
        for ignorer in self.ignorers:
            try:
                if ignorer(control.returned_value, candidate.returned_value):
                    return True
            except Exception as e:
                self.raised('ignorer', e)
        return False

    def _can_run_if_callback_allows(self):
        if self.should_run_callback:
            try:
                return self.should_run_callback()
            except Exception as e:
                self.raised('should_run_callback', e)
                return False
        return True

    def _should_experiment_run(self):
        try:
            return len(self.behaviors) > 1 and self.is_enabled() and self._can_run_if_callback_allows()
        except Exception as e:
            self.raised('enabled', e)
            return False

    def try_candidate(self, name='candidate', callback=None):
        if not callback and hasattr(name, '__call__'):
            callback = name
            name = 'candidate'

        if not callback:
            raise AttributeError('callback must be set')

        if name in self.behaviors:
            raise BehaviorNotUniqueError(self, name)

        self.behaviors[name] = callback

    def use(self, callback):
        self.try_candidate('control', callback)

    def run(self, name='control'):
        callback = self.behaviors.get(name, None)
        if not callback:
            raise BehaviorMissingError(self, name)

        if not self._should_experiment_run():
            return callback()

        if self.before_run:
            self.before_run()

        observations = []

        behaviors_names = list(self.behaviors.keys())
        random.shuffle(behaviors_names)
        for key in behaviors_names:
            callback = self.behaviors[key]
            observations.append(Observation(key, self, callback))

        control = next(
            (
                observation
                for observation in observations
                if observation.name == name
            ),
            None
        )

        self.result = Result(self, observations, control)

        try:
            self.publish(self.result)
        except Exception as e:
            self.raised('publish', e)

        if self.should_raise_on_mismatch and self.result.was_mismatched:
            raise MismatchError(self.name, self.result)

        if control.raised_exception:
            raise control.raised_exception
        else:
            self.returned_value = control.returned_value
            return self.returned_value

    def add_ignorer(self, func):
        self.ignorers.append(func)

    def clean_value(self, value):
        if self.cleaner:
            try:
                return self.cleaner(value)
            except Exception as e:
                self.raised('cleaner', e)
                return value
        else:
            return value

    def raised(self, operation, exception):
        raise exception
