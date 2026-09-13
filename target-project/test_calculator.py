import pytest

from calculator import add, subtract


class TestAdd:
    def test_positive_numbers(self):
        assert add(2, 3) == 5

    def test_negative_numbers(self):
        assert add(-2, -3) == -5

    def test_mixed_signs(self):
        assert add(-2, 3) == 1

    def test_with_zero(self):
        assert add(0, 5) == 5
        assert add(5, 0) == 5

    def test_floats(self):
        assert add(0.1, 0.2) == pytest.approx(0.3)


class TestSubtract:
    def test_positive_numbers(self):
        assert subtract(5, 3) == 2

    def test_negative_result(self):
        assert subtract(3, 5) == -2

    def test_negative_numbers(self):
        assert subtract(-2, -3) == 1

    def test_with_zero(self):
        assert subtract(5, 0) == 5
        assert subtract(0, 5) == -5

    def test_floats(self):
        assert subtract(0.3, 0.1) == pytest.approx(0.2)