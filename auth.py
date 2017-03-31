from datetime import datetime
from functools import wraps

import jwt
from flask import request
from werkzeug.exceptions import Forbidden


def _get_claims(audience, ttl):
    from server import app
    return {
        # Expiration Time Claim
        'exp': datetime.utcnow() + ttl,
        # Not Before Time Claim
        'nbf': datetime.utcnow(),
        # Issuer Claim
        'iss': app.config['ISSUER'],
        # Audience Claim
        'aud': audience,
        # Issued At Claim
        'iat': datetime.utcnow()
    }


def verify_logged_in(token, audience=None):
    from server import app
    return jwt.decode(token, app.config['PUBLIC_ECDSA_KEY'],
                      audience=audience or app.config['AUDIENCE'],
                      issuer=app.config['ISSUER'],
                      algorithms=app.config['LOGIN_ALGORITHM'])


def verify_jwt(check=None, *check_args, **check_kwargs):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                raise Forbidden("Auth header required")
            auth_type, auth_value = auth_header.split()
            if auth_type != "JWT":
                raise Forbidden("JWT required")
            auth_data = check(auth_value, *check_args, **check_kwargs)
            request.authorization = auth_data
            return f(*args, **kwargs)

        return wrapped

    return decorator
