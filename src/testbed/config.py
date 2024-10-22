from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class HostConfig:
    """Configuration for the baremetal host.
    """
    user: str  # username of the host
    ip: str  # IP address of the host
    arch: str  # hardware architecture of the host
    authorized_key: Optional[str] = None  # path to the authorized ssh key.
    intf: Optional[List[str]] = field(default=None)  # interfaces of the host
