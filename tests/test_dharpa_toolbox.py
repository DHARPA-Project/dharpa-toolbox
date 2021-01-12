#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `dharpa_toolbox` package."""

import dharpa_toolbox
import pytest  # noqa


def test_assert():

    assert dharpa_toolbox.get_version() is not None
