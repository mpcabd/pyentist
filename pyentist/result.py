class Result(object):

    def __init__(self, experiment, observations=(), control=None):
        super(Result, self).__init__()

        self.experiment = experiment
        self.observations = observations
        self.control = control
        if control:
            self.candidates = tuple(o for o in observations if o != control)
        else:
            self.candidates = tuple(observations[:])
        self.ignored = []
        self.mismatched = []

        self.evaluate_candidates()

    @property
    def context(self):
        return self.experiment.context

    @property
    def experiment_name(self):
        return self.experiment.name

    @property
    def was_matched(self):
        return not self.mismatched and not self.was_ignored

    @property
    def was_mismatched(self):
        return bool(self.mismatched)

    @property
    def was_ignored(self):
        return bool(self.ignored)

    def evaluate_candidates(self):
        mismatched = tuple(
            candidate
            for candidate in self.candidates
            if not self.experiment.are_observations_equivalent(self.control, candidate)
        )

        self.ignored = tuple(
            candidate
            for candidate in mismatched
            if self.experiment.should_ignore_mismatched_observation(self.control, candidate)
        )

        self.mismatched = tuple(candidate for candidate in mismatched if not candidate in self.ignored)
