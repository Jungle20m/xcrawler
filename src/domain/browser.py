from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class BrowserDomain:
    user_agent: Optional[str] = None
    proxy: Optional[Dict] = None