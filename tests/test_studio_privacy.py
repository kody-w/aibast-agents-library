import pytest

from tools import render_studio_walkthrough as renderer
from tools.studio_privacy import has_unapproved_email, reserved_email


@pytest.mark.parametrize("address", [
    "fictional@example.com", "fictional@ford.example.com", "FICTIONAL@EXAMPLE.COM",
    "fictional@company.test", "fictional@records.invalid",
])
def test_only_explicit_reserved_domains_are_allowed(address):
    assert reserved_email(address)
    assert not has_unapproved_email(address)
    renderer.check_privacy({"synthetic_contact": address})


@pytest.mark.parametrize("address", [
    "fictional@notexample.com", "fictional@example.com.example.net", "fictional@example.net",
    "fictional@contoso.com", "fictional@test.com", "fictional@invalid.com",
    "fictional%40unapproved.example.net", "fictional&#64;unapproved.example.net",
])
def test_lookalikes_and_unapproved_domains_fail_closed(address):
    assert has_unapproved_email(address)
    with pytest.raises(renderer.WalkthroughError, match="email address"):
        renderer.check_privacy({"synthetic_contact": address})


def test_one_allowed_address_does_not_hide_an_unapproved_address():
    with pytest.raises(renderer.WalkthroughError, match="email address"):
        renderer.check_privacy("fictional@example.com; fictional@unapproved.example.net")
