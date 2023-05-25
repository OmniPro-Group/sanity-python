import base64
from datetime import datetime, timedelta
import hmac
import hashlib
from cgi import parse_header
import json


def parse_signature(signature_header):
    if not signature_header:
        return None, None

    header_elements = signature_header.split(",")
    timestamp, signatures = None, []

    for element in header_elements:
        [k, v] = element.split("=")
        if k == "t":
            timestamp = v
        if k == "v1":
            signatures.append(v)

    return timestamp, signatures


def timestamp_is_valid(timestamp):
    current_time = datetime.today()
    sanity_timestamp = datetime.fromtimestamp(int(timestamp)/1000)

    diff = current_time - sanity_timestamp

    return diff < timedelta(minutes=5)


def contains_valid_signature(payload, timestamp, signatures, secret):
    payload_bytes = (timestamp + "." + payload).encode()

    digest = hmac.new(
        key=secret.encode(), msg=payload_bytes, digestmod=hashlib.sha256
    ).digest()
    computed_hmac = base64.b64encode(digest)
    computed_signature = computed_hmac.decode("utf-8").replace("/", "_").replace("+", "-").rstrip('=')

    t = any(
        hmac.compare_digest(event_signature, computed_signature)
        for event_signature in signatures
    )
    if t:
        return True
    return False


def get_json_payload(event):
    content_type = get_content_type(event.get("headers", {}))
    if content_type != "application/json":
        raise ValueError("Unsupported content-type")

    payload = normalize_body(
        raw_payload=event.get("body"), is_base64_encoded=event["isBase64Encoded"]
    )

    try:
        payload_json = json.loads(payload)
    except ValueError as err:
        raise ValueError("Invalid JSON payload") from err

    return payload_json


def normalize_body(raw_payload, is_base64_encoded):
    if raw_payload is None:
        raise ValueError("Missing event body")
    if is_base64_encoded:
        return base64.b64decode(raw_payload).decode("utf-8")
    return raw_payload


def get_content_type(headers):
    raw_content_type = headers.get("content-type")

    if raw_content_type is None:
        return None

    content_type, _ = parse_header(raw_content_type)
    return content_type
