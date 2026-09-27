from datetime import UTC, date, datetime

from app.bitget.session import AnchorStatus, NEW_YORK, expected_last_regular_date, validate_expected_anchor


def test_normal_weekday_before_close_uses_prior_day() -> None:
    as_of = datetime(2026, 9, 23, 15, 0, tzinfo=NEW_YORK)
    assert expected_last_regular_date(as_of) == date(2026, 9, 22)


def test_friday_after_close_uses_friday() -> None:
    as_of = datetime(2026, 9, 25, 17, 0, tzinfo=NEW_YORK)
    assert expected_last_regular_date(as_of) == date(2026, 9, 25)


def test_saturday_uses_friday() -> None:
    as_of = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)
    assert expected_last_regular_date(as_of) == date(2026, 9, 25)


def test_holiday_closure_skips_to_previous_session() -> None:
    closures = [
        (
            datetime(2026, 9, 7, 0, 0, tzinfo=NEW_YORK),
            datetime(2026, 9, 7, 23, 59, tzinfo=NEW_YORK),
        )
    ]
    as_of = datetime(2026, 9, 8, 12, 0, tzinfo=NEW_YORK)
    assert expected_last_regular_date(as_of, closures) == date(2026, 9, 4)


def test_dst_conversion_uses_new_york_rules() -> None:
    winter = datetime(2026, 1, 15, 21, 30, tzinfo=UTC).astimezone(NEW_YORK)
    summer = datetime(2026, 7, 15, 20, 30, tzinfo=UTC).astimezone(NEW_YORK)
    assert winter.hour == summer.hour == 16
    assert winter.utcoffset() != summer.utcoffset()


def test_missing_expected_anchor_fails_closed() -> None:
    assert (
        validate_expected_anchor(date(2026, 9, 25), {date(2026, 9, 24)})
        is AnchorStatus.MISSING_EXPECTED_ANCHOR
    )
