from datetime import datetime, timezone, timedelta

from app.services import token_blacklist_service as tbs


# ──────────────────────────────────────────────
# TOKEN BLACKLIST SERVICE
# ──────────────────────────────────────────────


def test_revoke_and_is_revoked_behavior():

    tbs._blacklist.clear()
    jti = "jti-1"
    exp = datetime.now(timezone.utc) + timedelta(minutes=5)

    tbs.revoke_token(jti, exp)

    assert tbs.is_token_revoked(jti) is True



def test_cleanup_removes_expired_entries():

    tbs._blacklist.clear()
    old = datetime.now(timezone.utc) - timedelta(minutes=1)
    tbs._blacklist["old-jti"] = old

    tbs._cleanup_expired()

    assert "old-jti" not in tbs._blacklist
