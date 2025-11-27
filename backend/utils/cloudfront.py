import base64
import json
import datetime
from urllib.parse import quote

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

PRIVATE_KEY_PATH = "/home/ubuntu/keys/cloudfront-private-key.pem"
CLOUDFRONT_DOMAIN = "https://d2t4m4nzg5dowd.cloudfront.net"
KEY_PAIR_ID = "K18TV0WP9G6UP3"


def rsa_signer(policy):
    with open(PRIVATE_KEY_PATH, 'rb') as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )

    signature = private_key.sign(
        policy,
        padding.PKCS1v15(),
        hashes.SHA1()
    )
    return signature


def generate_signed_url(path, expire_minutes=60):
    expires = int((datetime.datetime.utcnow() + datetime.timedelta(minutes=expire_minutes)).timestamp())
    resource_url = f"{CLOUDFRONT_DOMAIN}{path}"

    # Simple policy
    policy = {
        "Statement": [
            {
                "Resource": resource_url,
                "Condition": {"DateLessThan": {"AWS:EpochTime": expires}},
            }
        ]
    }

    policy_json = json.dumps(policy).encode("utf-8")
    policy_encoded = base64.b64encode(policy_json).decode("utf-8")

    signature = rsa_signer(policy_json)
    signature_encoded = base64.b64encode(signature).decode("utf-8")

    url = f"{resource_url}?Policy={quote(policy_encoded)}&Signature={quote(signature_encoded)}&Key-Pair-Id={KEY_PAIR_ID}"
    return url
