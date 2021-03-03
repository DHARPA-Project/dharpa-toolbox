#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `dharpa_toolbox` package."""

import pytest  # noqa

import dharpa


def test_assert():

    assert dharpa.get_version() is not None
