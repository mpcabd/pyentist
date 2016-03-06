from .. import (
    Experiment, DefaultExperiment, Observation,
    BehaviorMissingError, BehaviorNotUniqueError, MismatchError
)

import unittest


class TestExperiment(unittest.TestCase):

    def test_experiment_is_enabled_needs_implementation(self):
        ex = Experiment()
        with self.assertRaises(NotImplementedError):
            ex.is_enabled()

    def test_experiment_publish_needs_implementation(self):
        ex = Experiment()
        with self.assertRaises(NotImplementedError):
            ex.publish('result')


class TestFakeExperiment(unittest.TestCase):

    class FakeExperiment(Experiment):

        def __init__(self, *args, **kwargs):
            super(TestFakeExperiment.FakeExperiment, self).__init__(*args, **kwargs)
            self.published_result = None
            self.exceptions = []

        def is_enabled(self):
            return True

        def publish(self, result):
            self.published_result = result

        def raised(self, operation, exception):
            self.exceptions.append((operation, exception))

    def setUp(self):
        self.ex = TestFakeExperiment.FakeExperiment()
        self.old_class_raise_on_mismatch = Experiment.raise_on_mismatch

    def tearDown(self):
        Experiment.raise_on_mismatch = self.old_class_raise_on_mismatch

    def test_has_a_default_implementation(self):
        self.assertEqual(self.ex.name, 'experiment')

    def test_does_not_run_without_control_behvior(self):
        with self.assertRaises(BehaviorMissingError):
            self.ex.run()

    def test_control_runs_on_its_own(self):
        self.ex.use(lambda: 'control')
        self.assertEqual(self.ex.run(), 'control')

    def test_runs_both_but_returns_control(self):
        ran = []

        def control():
            ran.append('control')
            return 'control'

        def candidate():
            ran.append('candidate')
            return 'candidate'

        self.ex.use(control)
        self.ex.try_candidate(candidate)
        self.assertEqual(self.ex.run(), 'control')
        self.assertEqual(len(ran), 2)
        self.assertIn('control', ran)
        self.assertIn('candidate', ran)

    def test_complains_about_duplicate_behavior_names(self):
        self.ex.use(lambda: 'control')
        with self.assertRaises(BehaviorNotUniqueError) as e:
            self.ex.use(lambda: 'control again')

        self.assertEqual(self.ex, e.exception.experiment)
        self.assertEqual('control', e.exception.name)

    def test_silences_exceptions_raised_by_candidates(self):
        self.ex.use(lambda: 1)
        self.ex.try_candidate(lambda: 1 / 0)

        self.assertEqual(self.ex.run(), 1)

    def test_raises_exceptions_raised_by_control(self):
        self.ex.use(lambda: 1 / 0)
        self.ex.try_candidate(lambda: 1)

        with self.assertRaises(ZeroDivisionError):
            self.ex.run()

    def test_shuffles_behaviors_before_running(self):
        run = []
        runs = []

        self.ex.use(lambda: run.append('control') or 'control')
        self.ex.try_candidate(lambda: run.append('candidate') or 'candidate')

        for i in range(10000):
            self.assertEqual(self.ex.run(), 'control')
            runs.append(run[-1])
            run.clear()

        self.assertGreater(len(set(runs)), 1)

    def test_reports_raised_exceptions_during_publishing(self):
        from types import MethodType

        def bad_publish(self, result):
            raise TypeError('kaboom')

        self.ex.publish = MethodType(bad_publish, self.ex)

        self.ex.use(lambda: 'control')
        self.ex.try_candidate(lambda: 'candidate')

        self.assertEqual(self.ex.run(), 'control')

        (operation, exception) = self.ex.exceptions.pop()

        self.assertEqual('publish', operation)
        self.assertEqual('kaboom', str(exception))

    def test_publishes_results(self):
        self.ex.use(lambda: 'control')
        self.ex.try_candidate(lambda: 'candidate')

        self.assertEqual(self.ex.run(), 'control')

        self.assertIsNotNone(self.ex.published_result)

    def test_does_not_publish_results_when_there_is_only_control(self):
        self.ex.use(lambda: 'control')
        self.assertEqual(self.ex.run(), 'control')
        self.assertIsNone(self.ex.published_result)

    def test_compares_results_using_the_comparator_provided(self):
        self.ex.use(lambda: '1')
        self.ex.try_candidate(lambda: 1)
        self.ex.comparer = lambda a, b: str(a.returned_value) == str(b.returned_value)

        self.assertEqual(self.ex.run(), '1')
        self.assertTrue(self.ex.published_result.was_matched)

    def test_compares_two_observations_without_comparer(self):
        a = Observation(self.ex, 'a', lambda: 1)
        b = Observation(self.ex, 'b', lambda: 2)

        self.assertTrue(self.ex.are_observations_equivalent(a, a))
        self.assertFalse(self.ex.are_observations_equivalent(a, b))

    def test_compares_two_observations_with_comparer(self):
        a = Observation(self.ex, 'a', lambda: 1)
        b = Observation(self.ex, 'b', lambda: '1')

        # Not equivalent without a comparer
        self.assertFalse(self.ex.are_observations_equivalent(a, b))

        # Equivalent with a comparer
        self.ex.comparer = lambda a, b: str(a.returned_value) == str(b.returned_value)
        self.assertTrue(self.ex.are_observations_equivalent(a, b))

    def test_reports_raised_exceptions_in_comparer(self):
        self.ex.use(lambda: 'control')
        self.ex.try_candidate(lambda: 'candidate')

        def bad_comparer(a, b):
            raise TypeError('kaboom')

        self.ex.comparer = bad_comparer

        self.assertEqual(self.ex.run(), 'control')
        (operation, exception) = self.ex.exceptions.pop()

        self.assertEqual('comparer', operation)
        self.assertIsInstance(exception, TypeError)
        self.assertEqual('kaboom', str(exception))

    def test_reports_raised_exceptions_in_is_enabled(self):
        self.ex.use(lambda: 'control')
        self.ex.try_candidate(lambda: 'candidate')

        from types import MethodType

        def bad_is_enabled(self):
            raise TypeError('kaboom')

        self.ex.is_enabled = MethodType(bad_is_enabled, self.ex)

        self.assertEqual(self.ex.run(), 'control')
        (operation, exception) = self.ex.exceptions.pop()

        self.assertEqual('enabled', operation)
        self.assertIsInstance(exception, TypeError)
        self.assertEqual('kaboom', str(exception))

    def test_reports_raised_exceptions_in_should_run_callback(self):
        self.ex.use(lambda: 'control')
        self.ex.try_candidate(lambda: 'candidate')

        def bad_should_run_callback():
            raise TypeError('kaboom')

        self.ex.should_run_callback = bad_should_run_callback

        self.assertEqual(self.ex.run(), 'control')
        (operation, exception) = self.ex.exceptions.pop()

        self.assertEqual('should_run_callback', operation)
        self.assertIsInstance(exception, TypeError)
        self.assertEqual('kaboom', str(exception))

    def test_returns_the_given_value_whithout_cleaner(self):
        self.assertEqual(10, self.ex.clean_value(10))

    def test_calls_the_value_cleaner(self):
        self.ex.cleaner = lambda v: str(v).upper()

        self.assertEqual('A', self.ex.clean_value('a'))

    def test_reports_raised_exceptions_in_cleaner_and_returns_original_value(self):
        def bad_cleaner(value):
            raise TypeError('kaboom')

        self.ex.cleaner = bad_cleaner
        self.assertEqual(10, self.ex.clean_value(10))

        (operation, exception) = self.ex.exceptions.pop()

        self.assertEqual('cleaner', operation)
        self.assertIsInstance(exception, TypeError)
        self.assertEqual('kaboom', str(exception))

    def test_does_not_run_if_should_run_callback_is_false(self):
        ran = []

        self.ex.use(lambda: ran.append('control') or 'control')
        self.ex.try_candidate(lambda: ran.append('candidate') or 'candidate')
        self.ex.should_run_callback = lambda: ran.append('should_run_callback') or False

        self.assertEqual(self.ex.run(), 'control')
        self.assertIn('should_run_callback', ran)
        self.assertIn('control', ran)
        self.assertNotIn('candidate', ran)

    def test_runs_if_should_run_callback_is_true(self):
        ran = []

        self.ex.use(lambda: ran.append('control') or 'control')
        self.ex.try_candidate(lambda: ran.append('candidate') or 'candidate')
        self.ex.should_run_callback = lambda: ran.append('should_run_callback') or True

        self.assertEqual(self.ex.run(), 'control')
        self.assertIn('should_run_callback', ran)
        self.assertIn('control', ran)
        self.assertIn('candidate', ran)

    def test_does_not_ignore_an_observation_if_not_ignorer_is_set(self):
        a = Observation(self.ex, 'a', lambda: 1)
        b = Observation(self.ex, 'b', lambda: 2)

        self.assertFalse(self.ex.should_ignore_mismatched_observation(a, b))

    def test_uses_the_ignorer(self):
        a = Observation(self.ex, 'a', lambda: 1)
        b = Observation(self.ex, 'b', lambda: 2)

        called = False

        def ignorer(v1, v2):
            nonlocal called
            called = True
            self.assertEqual(v1, a.returned_value)
            self.assertEqual(v2, b.returned_value)
            return True

        self.ex.add_ignorer(ignorer)

        self.assertTrue(self.ex.should_ignore_mismatched_observation(a, b))
        self.assertTrue(called)

    def test_calls_all_ignorers_until_one_matches(self):
        a = Observation(self.ex, 'a', lambda: 1)
        b = Observation(self.ex, 'b', lambda: 2)

        called = []

        self.ex.add_ignorer(lambda v1, v2: called.append('ignorer_1') or False)
        self.ex.add_ignorer(lambda v1, v2: called.append('ignorer_2') or False)
        self.ex.add_ignorer(lambda v1, v2: called.append('ignorer_3') or True)
        self.ex.add_ignorer(lambda v1, v2: called.append('ignorer_4') or False)

        self.assertTrue(self.ex.should_ignore_mismatched_observation(a, b))
        self.assertIn('ignorer_1', called)
        self.assertIn('ignorer_2', called)
        self.assertIn('ignorer_3', called)
        self.assertNotIn('ignorer_4', called)

    def test_reports_raised_exceptions_in_ignorer_and_returns_false(self):
        a = Observation(self.ex, 'a', lambda: 1)
        b = Observation(self.ex, 'b', lambda: 2)

        def bad_ignorer(v1, v2):
            raise TypeError('kaboom')

        self.ex.add_ignorer(bad_ignorer)

        self.assertFalse(self.ex.should_ignore_mismatched_observation(a, b))

        (operation, exception) = self.ex.exceptions.pop()

        self.assertEqual('ignorer', operation)
        self.assertIsInstance(exception, TypeError)
        self.assertEqual('kaboom', str(exception))

    def test_reports_raised_exceptions_in_ignorer_but_uses_other_ignorers(self):
        a = Observation(self.ex, 'a', lambda: 1)
        b = Observation(self.ex, 'b', lambda: 2)

        def bad_ignorer(v1, v2):
            raise TypeError('kaboom')

        self.ex.add_ignorer(bad_ignorer)
        self.ex.add_ignorer(lambda v1, v2: True)

        self.assertTrue(self.ex.should_ignore_mismatched_observation(a, b))

        (operation, exception) = self.ex.exceptions.pop()

        self.assertEqual('ignorer', operation)
        self.assertIsInstance(exception, TypeError)
        self.assertEqual('kaboom', str(exception))

    def test_raises_when_should_raise_on_mismatch_is_true(self):
        self.ex.use(lambda: 'control')
        self.ex.try_candidate(lambda: 'candidate')
        self.ex.should_raise_on_mismatch = True

        with self.assertRaises(MismatchError) as e:
            self.ex.run()

    def test_does_not_raise_when_should_raise_on_mismatch_is_false(self):
        self.ex.use(lambda: 'control')
        self.ex.try_candidate(lambda: 'candidate')
        self.ex.should_raise_on_mismatch = False
        self.assertEqual(self.ex.run(), 'control')

    def test_raises_when_should_raise_on_mismatch_is_true_and_candidate_raises_and_control_does_not(self):
        self.ex.use(lambda: 1)
        self.ex.try_candidate(lambda: 1 / 0)
        self.ex.should_raise_on_mismatch = True

        with self.assertRaises(MismatchError) as e:
            self.ex.run()

    def test_raises_when_should_raise_on_mismatch_is_true_and_control_raises_and_candidate_does_not(self):
        self.ex.use(lambda: 1 / 0)
        self.ex.try_candidate(lambda: 1)
        self.ex.should_raise_on_mismatch = True

        with self.assertRaises(MismatchError) as e:
            self.ex.run()

    def test_respects_class_raise_on_mismatch_by_default(self):
        self.ex.use(lambda: 'control')
        self.ex.try_candidate(lambda: 'candidate')

        Experiment.raise_on_mismatch = True
        with self.assertRaises(MismatchError) as e:
            self.ex.run()

        Experiment.raise_on_mismatch = False
        self.assertEqual(self.ex.run(), 'control')

    def test_does_not_respect_class_raise_on_mismatch_when_instance_should_raise_on_mismatch_is_set(self):
        self.ex.use(lambda: 'control')
        self.ex.try_candidate(lambda: 'candidate')

        Experiment.raise_on_mismatch = False
        self.ex.should_raise_on_mismatch = True
        with self.assertRaises(MismatchError) as e:
            self.ex.run()

        Experiment.raise_on_mismatch = True
        self.ex.should_raise_on_mismatch = False
        self.assertEqual(self.ex.run(), 'control')

    def test_mismatch_error(self):
        self.ex.use(lambda: 'control')
        self.ex.try_candidate(lambda: 'candidate')
        self.ex.should_raise_on_mismatch = True
        with self.assertRaises(MismatchError) as e:
            self.ex.run()
        self.assertEqual(e.exception.name, self.ex.name)
        self.assertEqual(e.exception.result, self.ex.published_result)

    def test_before_run(self):
        # Should run first before control and candidate
        ran = []
        self.ex.use(lambda: ran.append('control') or 'control')
        self.ex.try_candidate(lambda: ran.append('candidate') or 'candidate')
        self.ex.before_run = lambda: ran.append('before_run') or True
        self.assertEqual(self.ex.run(), 'control')
        self.assertEqual(ran[0], 'before_run')
        self.assertIn('control', ran)
        self.assertIn('candidate', ran)

        # Should not run if the expirement is disabled
        ran.clear()
        from types import MethodType
        self.ex.is_enabled = MethodType(lambda: False, self.ex)
        self.assertEqual(self.ex.run(), 'control')
        self.assertEqual(ran[0], 'control')
        self.assertEqual(len(ran), 1)


if __name__ == '__main__':
    unittest.main()
