# test_find_max.py
import pytest
from find_max import find_max  # 실제 모듈 경로에 맞게 수정


# ---------- 정상 케이스 ----------
class TestNormal:
    def test_max_in_middle(self):
        assert find_max([3, 9, 4, 1]) == 9

    def test_unsorted_list(self):
        assert find_max([55, 70, 85, 60, 90, 75]) == 90

    def test_negative_numbers(self):
        assert find_max([-5, -2, -9, -3]) == -2

    def test_mixed_sign(self):
        assert find_max([-10, 0, 7, -3]) == 7

    def test_floats(self):
        assert find_max([1.5, 2.7, 2.6, 0.1]) == pytest.approx(2.7)

    def test_does_not_modify_input(self):
        data = [3, 1, 2]
        find_max(data)
        assert data == [3, 1, 2]

    def test_tuple_input(self):
        assert find_max((4, 8, 6)) == 8


# ---------- 예외 케이스 ----------
class TestExceptions:
    def test_empty_list_raises_index_error(self):
        with pytest.raises(IndexError):
            find_max([])

    def test_none_raises_type_error(self):
        with pytest.raises(TypeError):
            find_max(None)

    def test_non_sequence_raises_type_error(self):
        with pytest.raises(TypeError):
            find_max(42)

    def test_incomparable_types_raise_type_error(self):
        with pytest.raises(TypeError):
            find_max([1, "a", 3])


# ---------- 경계값 케이스 ----------
class TestBoundary:
    def test_single_element(self):
        assert find_max([7]) == 7

    def test_two_elements_max_first(self):
        assert find_max([9, 1]) == 9

    def test_two_elements_max_last(self):
        # 현재 코드에서 실패: 마지막 원소를 검사하지 않음
        assert find_max([1, 9]) == 9

    def test_max_at_first_position(self):
        assert find_max([100, 50, 20, 10]) == 100

    def test_max_at_last_position(self):
        # 현재 코드에서 실패: 마지막 원소를 검사하지 않음
        assert find_max([10, 20, 50, 100]) == 100

    def test_all_equal(self):
        assert find_max([5, 5, 5, 5]) == 5

    def test_duplicate_max(self):
        assert find_max([3, 8, 2, 8]) == 8

    def test_zero_and_extremes(self):
        assert find_max([0, 0, 0]) == 0
        assert find_max([float("-inf"), -1e308]) == -1e308

    def test_large_list(self):
        data = list(range(10_000))
        # 현재 코드에서 실패: 최댓값이 마지막에 있음
        assert find_max(data) == 9_999


# ---------- 매개변수화 요약 ----------
@pytest.mark.parametrize(
    "scores, expected",
    [
        ([1], 1),
        ([2, 1], 2),
        ([1, 2], 2),          # 현재 코드에서 실패
        ([1, 3, 2], 3),
        ([1, 2, 3], 3),       # 현재 코드에서 실패
        ([-1, -1], -1),
    ],
)
def test_find_max_parametrized(scores, expected):
    assert find_max(scores) == expected
