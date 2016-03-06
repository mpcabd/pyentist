from .. import DefaultExperiment, Experiment

import unittest


class TestDefault(unittest.TestCase):

    def setUp(self):
        self.ex = DefaultExperiment('default')

    def test_enabled(self):
        self.assertTrue(self.ex.is_enabled())

    def test_publish_does_nothing(self):
        self.assertIsNone(self.ex.publish('data'))

    def test_it_is_an_experiment(self):
        self.assertIsInstance(self.ex, Experiment)

    def test_raises_when_an_internal_action_raises(self):
        with self.assertRaises(TypeError):
            self.ex.raised('publish', TypeError('kaboom'))

    def test_raises_exceptions_raised_in_publish_by_default(self):
        from types import MethodType

        def bad_publish(self, result):
            raise TypeError('kaboom')

        self.ex.publish = MethodType(bad_publish, self.ex)

        self.ex.use(lambda: 'control')
        self.ex.try_candidate(lambda: 'candidate')

        with self.assertRaises(TypeError) as e:
            self.ex.run()

        self.assertEqual('kaboom', str(e.exception))

if __name__ == '__main__':
    unittest.main()
