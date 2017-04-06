#!/usr/bin/env python

import distutils.core

distutils.core.setup(
    name='process-control',
    version='1.0.5',
    author='Adam Roses Wight',
    author_email='awight@wikimedia.org',
    url='https://github.com/adamwight/process-control',
    packages=['processcontrol'],
    scripts=[
        'bin/check-jobs-icinga',
        'bin/cron-generate',
        'bin/run-job',
    ],
)
