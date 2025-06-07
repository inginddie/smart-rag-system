# -*- coding: utf-8 -*-
import pytest
from src.utils.model_selector import ModelSelector
from config.settings import settings


def test_model_selector_simple_query():
    selector = ModelSelector()
    settings.enable_smart_selection = True
    query = "¿Qué es Python?"
    model, score, _ = selector.select_model(query)
    assert model == settings.simple_model
    assert score < settings.complexity_threshold


def test_model_selector_complex_query():
    selector = ModelSelector()
    settings.enable_smart_selection = True
    query = (
        "Realiza un análisis comparativo de frameworks de Machine Learning "
        "en la literatura académica y sus limitaciones"
    )
    model, score, _ = selector.select_model(query)
    assert model == settings.complex_model
    assert score >= settings.complexity_threshold
