from .errors import *
from .result import Result
from .experiment import Experiment
from .observation import Observation
from .default import DefaultExperiment

from contextlib import contextmanager

@contextmanager
def science(name, options=None):
    if options and 'experiment_class' in options:
        args = 'args' in options and options['args'] or []
        kwargs = 'kwargs' in options and options['kwargs'] or {}
        experiment = options['experiment_class'](name, *args, **kwargs)
    else:
        experiment = DefaultExperiment(name)

    if options and 'context' in options:
        experiment.context = options['context']
    else:
        experiment.context = default_scientist_context()

    yield experiment

    if options and 'run' in options:
        experiment.run(options['run'])
    else:
        experiment.run()


def default_scientist_context():
    return {}

__all__ = [
    'BadBehaviorError', 'BehaviorMissingError', 'BehaviorNotUniqueError', 'NoValueError', 'MismatchError',
    'Result',
    'Experiment',
    'Observation',
    'DefaultExperiment',
]
