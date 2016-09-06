# -*- coding: utf-8 -*-
"""
Set of unit tests for Classifier
"""
import unittest

from reporter.classifier import Classifier
from reporter.reports import Report


class ClassifierTestClass(unittest.TestCase):
    def setUp(self):
        classifier_config = {
            'components': {
                'Helios': 1,
                'Mercury': 2,
                'Pandora': 3,
                'Phalanx': 4,
            },
            'paths': {

            }
        }
        self.classifier = Classifier(config=classifier_config)

    def test_classify_by_label(self):
        report = Report('foo', 'bar')
        assert self.classifier.classify(report) is None

        report = Report('foo', 'bar', label='MercuryErrors')
        assert self.classifier.classify(report) == (Classifier.PROJECT_MAIN, 2)

        report = Report('foo', 'bar', label='Helios')
        assert self.classifier.classify(report) == (Classifier.PROJECT_SER, 1)
