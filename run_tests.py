import unittest
import sys

from datamodel import xmlmodel


normal_tests = [
	xmlmodel
]


if __name__ == '__main__':
	all_tests = normal_tests


	if len(sys.argv) > 1:
		modules_to_test = []

		for a in sys.argv[1:]:
			x = None
			for m in all_tests:
				if a == m.__name__:
					x = m
					break

			if x is None:
				for m in all_tests:
					name = m.__name__
					if name.endswith(a):
						x = m
						break

			if x is None:
				print 'Cannot find test module {0}'.format(a)
			else:
				modules_to_test.append(x)
	else:
		modules_to_test = normal_tests

	print 'Testing:'
	for m in modules_to_test:
		print m.__name__

	loader = unittest.TestLoader()

	suites = [loader.loadTestsFromModule(m)   for m in modules_to_test]

	runner = unittest.TextTestRunner()

	results = unittest.TestResult()

	overall_suite = unittest.TestSuite()
	overall_suite.addTests(suites)

	runner.run(overall_suite)

