import sys

default_labels = [
    "django_socio_grpc/tests/",
]

ignore_labels = ["django_socio_grpc/tests/grpc_test_utils/"]


def get_suite(labels=default_labels, verbosity=3):
    from test_utils.test_runner import PytestTestRunner

    runner = PytestTestRunner(verbosity=verbosity)
    failures = runner.run_tests(labels, ignore_labels)
    if failures:
        sys.exit(failures)


def launch():
    labels = default_labels
    if len(sys.argv[1:]) > 0:
        labels = sys.argv[1:]
    get_suite(labels)


if __name__ == "__main__":
    launch()
