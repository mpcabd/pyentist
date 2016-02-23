# Pyentist
Python Scientist - Port of GitHub's [Scientist](https://github.com/github/scientist) - A library for carefully refactoring critical paths

## What is this?

This is a Python port of GitHub's [Scientist](https://github.com/github/scientist) which is a library for carefully refactoring critical paths.

Let's pretend you're changing the way you handle permissions in a large web app. Tests can help guide your refactoring, but you really want to compare the current and refactored behaviors under load.

By using an experiment from this library, you can try both ways (the old way and the new way), and you can make sure that the result is the same, and they both don't have issues (or at least the same issues).

When you wrap your change in an experiment, you will get that:

* It (the experiment) decides whether or not to run the new way (we call it the `try` path) based on your configuration,
* Randomizes the order in which the old way (we call it the `use` path) and `try` paths are run,
* Measures the durations of all behaviors,
* Compares the result of `try` to the result of `use`,
* Swallows (but records) any exceptions raised in the `try` path, and
* Publishes all this information.

The `use` block is also called the **control**. The `try` block is also called the **candidate**.

If you don't declare any `try` blocks, none of the Scientist machinery is invoked and the control value is always returned.

## How to science?

Here's a quick and dirty way to science

    # Import the library
    import pyentist

    # Using a context manager makes it easy to setup
    with pyentist.science('exp1') as e:
        x = 10
        y = 5

        # You can change the configuration of the experiment here
        e.should_raise_on_mismatch = True

        # The `use` method accepts the function that will be used as a control
        # case, the base case, the old case, etc.
        e.use(lambda: x * y)

        # The `try_candidate` method accepts the name of the candidate and the
        # function that will be used in this candidate.
        e.try_candidate('candidate1', lambda: sum(x for _ in range(y)))

        # You can try more than one candidate if you want.

    # You have access to the returned value by the control case
    print(e.returned_value)

    # You can also peek at e.result wich is an instance of pyentist.Result

_More documentation coming soon_

## License

GNU General Public License v3 or later (GPLv3+)
