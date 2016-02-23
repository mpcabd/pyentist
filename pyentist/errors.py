class BadBehaviorError(Exception):

    def __init__(self, experiment, name, message):
        self.experiment = experiment
        self.name = name
        super(BadBehaviorError, self).__init__(
            message
        )


class BehaviorMissingError(BadBehaviorError):

    def __init__(self, experiment, name):
        super(BehaviorMissingError, self).__init__(
            experiment, name,
            "{} missing {} behavior".format(experiment.name, name)
        )


class BehaviorNotUniqueError(BadBehaviorError):

    def __init__(self, experiment, name):
        super(BehaviorNotUniqueError, self).__init__(
            experiment, name,
            "{} already has {} behavior".format(experiment.name, name)
        )


class NoValueError(Exception):

    def __init__(self, observation):
        self.observation = observation
        super(NoValueError, self).__init__(
            "{} didn't return a value".format(observation.name)
        )


class MismatchError(Exception):

    def __init__(self, name, result):
        self.name = name
        self.result = result

        super(MismatchError, self).__init__(
            "experiment '{}' observations mismatched".format(name)
        )
