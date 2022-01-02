from dataclasses import dataclass


@dataclass
class WebPunchSettings:
    allowed: bool
    password: str
    authorized_ip_addresses: str
    allow_punch_from_unauthorized_ip: bool
    use_global_authorized_ip_addresses: bool
