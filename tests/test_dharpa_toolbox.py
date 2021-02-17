#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `dharpa_toolbox` package."""

import dharpa
import pytest  # noqa


def test_assert():

    assert dharpa.get_version() is not None
