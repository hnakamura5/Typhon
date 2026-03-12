from .assertion_utils import assert_equal_with_meta_variable


def test_assert_equal_with_meta_variable():
    assert_equal_with_meta_variable("x + y", "x + y")
    assert_equal_with_meta_variable("x + y", "$a + $b")
    assert_equal_with_meta_variable("x + x", "$a + $a")
    try:
        assert_equal_with_meta_variable("x + y", "$a + $a")
        assert False, "Expected an assertion error"
    except AssertionError:
        pass
    try:
        assert_equal_with_meta_variable("x + y", "y + $a")
        assert False, "Expected an assertion error"
    except AssertionError:
        pass
