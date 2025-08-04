from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class BrowserConfig:
    user_agent: Optional[str] = None
    proxy: Optional[Dict] = None
    

class BrowserConfigSelector:
    def __init__(self, browser_configs: List[BrowserConfig]):
        self.browser_configs = browser_configs
        self.current_index = -1
        self.total_profiles = len(browser_configs)

    def get_browser_config(self) -> BrowserConfig:
        self.current_index = (self.current_index + 1) % self.total_profiles
        current_config = self.browser_configs[self.current_index]
        return current_config
    
    def get_browser_config_index(self) -> int:
        return self.current_index
    
    
@dataclass
class UserProfile:
    email: str
    password: str
    screen_name: str
    state_file: str