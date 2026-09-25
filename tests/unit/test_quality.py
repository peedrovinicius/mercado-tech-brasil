from src.quality.checks import valid_cbo, valid_salary, valid_uf


def test_valid_uf():
    assert valid_uf("CE")
    assert valid_uf("SP")
    assert not valid_uf("XX")


def test_valid_cbo():
    assert valid_cbo("212405")
    assert not valid_cbo("21A405")
    assert not valid_cbo("123")


def test_valid_salary():
    assert valid_salary(None)
    assert valid_salary(0)
    assert valid_salary(2500.50)
    assert not valid_salary(-1)
