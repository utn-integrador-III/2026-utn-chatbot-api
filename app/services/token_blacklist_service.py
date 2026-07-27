"""
app/services/token_blacklist_service.py
Gestiona la lista negra de tokens JWT revocados (para logout seguro).

Estrategia:
  - Se almacena el JTI (JWT ID) de cada token revocado junto con su expiración.
  - Al validar un token, se verifica que su JTI no esté en la blacklist.
  - Los tokens expirados se eliminan automáticamente para no crecer indefinidamente.

Almacenamiento:
  - En memoria (dict) para desarrollo/pruebas.
  - Reemplazar por Redis en producción para persistencia y escalabilidad horizontal.
  -
"""
import threading
from datetime import datetime, timezone

# ──────────────────────────────────────────────
# STORE EN MEMORIA
# Thread-safe con Lock para entornos multi-hilo (Flask dev server, Gunicorn threads)
# En producción: reemplazar por redis.StrictRedis
# ──────────────────────────────────────────────

_blacklist: dict[str, datetime] = {}   # { jti: expires_at }
_lock = threading.Lock()


def revoke_token(jti: str, expires_at: datetime) -> None:
    """
    Agrega el JTI del token a la blacklist con su fecha de expiración.
    Se llama al hacer logout.
    """
    with _lock:
        _blacklist[jti] = expires_at
        _cleanup_expired()


def is_token_revoked(jti: str) -> bool:
    """
    Verifica si el JTI está en la blacklist.
    Devuelve True si el token fue revocado (debe rechazarse).
    """
    with _lock:
        return jti in _blacklist


def _cleanup_expired() -> None:
    """
    Elimina JTIs cuyos tokens ya expiraron (ya no hace falta guardarlos).
    Se llama internamente en cada revocación para mantener el store acotado.
    """
    now = datetime.now(timezone.utc)
    expired = [jti for jti, exp in _blacklist.items() if exp <= now]
    for jti in expired:
        del _blacklist[jti]


# ──────────────────────────────────────────────
# NOTA PARA PRODUCCIÓN
# ──────────────────────────────────────────────
# Reemplazar las funciones anteriores por:
#
# import redis
# _redis = redis.StrictRedis.from_url(settings.REDIS_URL, decode_responses=True)
#
# def revoke_token(jti: str, expires_at: datetime) -> None:
#     ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())
#     if ttl > 0:
#         _redis.setex(f"blacklist:{jti}", ttl, "1")
#
# def is_token_revoked(jti: str) -> bool:
#     return _redis.exists(f"blacklist:{jti}") == 1