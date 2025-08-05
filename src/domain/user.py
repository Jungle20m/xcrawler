
from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class UserDomain:
    id: str
    email: str
    password: str
    screen_name: str
    is_logged_in: bool
    browser_id: Optional[str] = None
    cookie: Optional[Dict] = None
    cookie_file: Optional[str] = None