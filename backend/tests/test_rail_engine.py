from app.services.rail_engine import Segment, first_fit, free_gaps, validate_forbidden


def test_first_fit_leftmost():
    occ = [Segment(20, 40)]
    p = first_fit(100, occ, 15)
    assert p is not None
    assert p.start_cm == 0
    assert p.end_cm == 15


def test_first_fit_skips_too_small_gap():
    occ = [Segment(0, 10), Segment(18, 50)]
    p = first_fit(100, occ, 10)
    assert p is not None
    assert p.start_cm == 50


def test_no_space():
    occ = [Segment(0, 80)]
    assert first_fit(100, occ, 25) is None


def test_free_gaps_edges():
    gaps = free_gaps(50, [Segment(10, 20), Segment(30, 35)])
    assert gaps == [Segment(0, 10), Segment(20, 30), Segment(35, 50)]


# —— 禁挂段 ——


def test_forbidden_splits_gap():
    # 禁挂带把一整段空闲剖成两段
    gaps = free_gaps(200, [], [Segment(80, 100)])
    assert gaps == [Segment(0, 80), Segment(100, 200)]


def test_forbidden_splits_gap_between_garments():
    occ = [Segment(0, 45), Segment(45, 80)]
    gaps = free_gaps(200, occ, [Segment(80, 100)])
    assert gaps == [Segment(100, 200)]


def test_first_fit_never_lands_in_forbidden_band():
    # 禁挂 80–100，唯一够长的间隙在 100 之后；放置不得与禁挂带重叠
    forbidden = [Segment(80, 100)]
    p = first_fit(200, [Segment(0, 45), Segment(45, 80)], 50, forbidden)
    assert p is not None
    assert p.start_cm == 100
    assert p.end_cm == 150


def test_first_fit_forbidden_only_space_fails():
    # 剩余空闲全在禁挂带内 → 上杆失败
    forbidden = [Segment(80, 200)]
    assert first_fit(200, [Segment(0, 80)], 10, forbidden) is None


def test_forbidden_makes_rail_full():
    # 无禁挂时可放；加禁挂后无处可放
    occ = [Segment(0, 100)]
    assert first_fit(200, occ, 60) is not None
    assert first_fit(200, occ, 60, [Segment(100, 200)]) is None


def test_no_forbidden_behaves_as_before():
    occ = [Segment(0, 10), Segment(18, 50)]
    assert free_gaps(100, occ, None) == free_gaps(100, occ)
    assert free_gaps(100, occ, []) == free_gaps(100, occ)
    assert first_fit(100, occ, 10, None) == first_fit(100, occ, 10)
    assert first_fit(100, occ, 10, []) == first_fit(100, occ, 10)


def test_validate_forbidden_ok():
    assert validate_forbidden(200, [Segment(80, 100)]) is None
    assert validate_forbidden(200, []) is None
    # 相邻端点相接（半开区间）不算相交
    assert validate_forbidden(200, [Segment(0, 50), Segment(50, 100)]) is None


def test_validate_forbidden_out_of_bounds():
    assert validate_forbidden(200, [Segment(-1, 50)]) is not None
    assert validate_forbidden(200, [Segment(150, 201)]) is not None
    assert validate_forbidden(200, [Segment(0, 200)]) is None


def test_validate_forbidden_start_ge_end():
    assert validate_forbidden(200, [Segment(100, 100)]) is not None
    assert validate_forbidden(200, [Segment(120, 100)]) is not None


def test_validate_forbidden_self_overlap():
    assert validate_forbidden(200, [Segment(50, 90), Segment(80, 120)]) is not None
    assert validate_forbidden(200, [Segment(80, 120), Segment(50, 90)]) is not None
    assert validate_forbidden(200, [Segment(50, 100), Segment(60, 70)]) is not None
