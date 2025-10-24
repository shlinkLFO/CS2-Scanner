"""
Rate Limit Detection and VPN Rotation Handler
Detects Steam rate limits and triggers intelligent IP switching
"""

import logging
import time
import subprocess
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimitHandler:
    def __init__(self):
        self.rate_limit_hits = 0
        self.last_rate_limit_time = None
        self.base_wait_time = 60  # 1 minute base
        self.max_wait_time = 600  # 10 minutes max
        self.ip_switch_count = 0
        self.last_ip_switch_time = None
        self.min_ip_switch_interval = 300  # 5 minutes between IP switches
        
    def detect_rate_limit(self, page_html: str = None, error: Exception = None) -> bool:
        """
        Detect if we've hit a rate limit
        
        Indicators:
        1. Error: "Target page, context or browser has been closed"
        2. Empty results after consecutive searches
        3. HTTP 429 status
        4. Steam error pages
        """
        if error:
            error_str = str(error)
            # Browser closed unexpectedly = likely rate limit
            if "Target page, context or browser has been closed" in error_str:
                logger.warning("Detected browser closure - likely rate limit")
                return True
            if "429" in error_str or "Too Many Requests" in error_str:
                logger.warning("Detected HTTP 429 - rate limit")
                return True
        
        if page_html:
            # Check for Steam error messages
            rate_limit_indicators = [
                "Please wait before trying again",
                "Too many requests",
                "Rate limit exceeded",
                "Access denied",
                "Your connection has been temporarily blocked"
            ]
            for indicator in rate_limit_indicators:
                if indicator.lower() in page_html.lower():
                    logger.warning(f"Detected rate limit indicator: '{indicator}'")
                    return True
        
        return False
    
    def get_wait_time(self) -> int:
        """Calculate wait time with exponential backoff"""
        if self.rate_limit_hits == 0:
            return self.base_wait_time
        
        # Exponential backoff: 60s, 120s, 240s, 480s, 600s (max)
        wait_time = min(
            self.base_wait_time * (2 ** (self.rate_limit_hits - 1)),
            self.max_wait_time
        )
        return int(wait_time)
    
    def should_switch_ip(self) -> bool:
        """Determine if we should switch IP"""
        # Always switch on rate limit
        if self.rate_limit_hits > 0:
            return True
        
        # Proactive switching: every N successful scrapes
        if self.ip_switch_count > 0 and self.last_ip_switch_time:
            time_since_switch = (datetime.now() - self.last_ip_switch_time).total_seconds()
            # Switch every 5 minutes or 15 successful scrapes
            if time_since_switch > self.min_ip_switch_interval:
                return True
        
        return False
    
    def switch_vpn_server(self, vpn_type: str = "nordvpn") -> bool:
        """
        Switch VPN server
        
        Args:
            vpn_type: 'nordvpn' or 'expressvpn'
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Switching {vpn_type} server...")
            
            if vpn_type.lower() == "nordvpn":
                # Disconnect
                subprocess.run(["nordvpn", "disconnect"], 
                             capture_output=True, timeout=30)
                time.sleep(2)
                
                # Connect to random server
                result = subprocess.run(["nordvpn", "connect"], 
                                      capture_output=True, timeout=60, text=True)
                
                if "Connected" in result.stdout or result.returncode == 0:
                    logger.info("✓ NordVPN: Connected to new server")
                    self.ip_switch_count += 1
                    self.last_ip_switch_time = datetime.now()
                    return True
                else:
                    logger.error(f"NordVPN connection failed: {result.stderr}")
                    return False
            
            elif vpn_type.lower() == "expressvpn":
                # Disconnect
                subprocess.run(["expressvpn", "disconnect"], 
                             capture_output=True, timeout=30)
                time.sleep(2)
                
                # Connect to random server
                result = subprocess.run(["expressvpn", "connect", "smart"], 
                                      capture_output=True, timeout=60, text=True)
                
                if "Connected" in result.stdout or result.returncode == 0:
                    logger.info("✓ ExpressVPN: Connected to new server")
                    self.ip_switch_count += 1
                    self.last_ip_switch_time = datetime.now()
                    return True
                else:
                    logger.error(f"ExpressVPN connection failed: {result.stderr}")
                    return False
            
            else:
                logger.warning(f"Unknown VPN type: {vpn_type}")
                return False
        
        except subprocess.TimeoutExpired:
            logger.error("VPN switch timed out")
            return False
        except FileNotFoundError:
            logger.error(f"{vpn_type} CLI not found - install it first")
            return False
        except Exception as e:
            logger.error(f"Error switching VPN: {e}")
            return False
    
    def handle_rate_limit(self, vpn_type: Optional[str] = None) -> bool:
        """
        Handle rate limit detection
        
        Returns:
            True if handled successfully, False if should abort
        """
        self.rate_limit_hits += 1
        self.last_rate_limit_time = datetime.now()
        
        wait_time = self.get_wait_time()
        
        logger.warning("="*80)
        logger.warning("⚠️  RATE LIMIT DETECTED")
        logger.warning("="*80)
        logger.warning(f"Rate limit hit #{self.rate_limit_hits}")
        logger.warning(f"Wait time: {wait_time} seconds ({wait_time/60:.1f} minutes)")
        
        # Switch IP if VPN available
        if vpn_type and self.should_switch_ip():
            logger.info("Attempting to switch IP address...")
            if self.switch_vpn_server(vpn_type):
                logger.info("✓ IP switched successfully")
                # Reduce wait time after successful IP switch
                wait_time = max(30, wait_time // 2)
                logger.info(f"Reduced wait time to {wait_time} seconds")
            else:
                logger.warning("✗ IP switch failed, using full wait time")
        
        # Wait with countdown
        logger.info(f"Waiting {wait_time} seconds before retry...")
        for remaining in range(wait_time, 0, -10):
            if remaining % 30 == 0:
                logger.info(f"  {remaining} seconds remaining...")
            time.sleep(min(10, remaining))
        
        logger.info("Wait complete, resuming scraping")
        logger.warning("="*80)
        
        # Reset rate limit counter if we've recovered
        if self.rate_limit_hits >= 3:
            logger.warning("Multiple rate limits hit - consider longer delays")
        
        return True
    
    def reset_rate_limit_counter(self):
        """Reset rate limit counter after successful scrapes"""
        if self.rate_limit_hits > 0:
            logger.info(f"Resetting rate limit counter (was {self.rate_limit_hits})")
            self.rate_limit_hits = 0
    
    def get_strategic_delay(self, successful_scrapes: int) -> int:
        """
        Calculate strategic delay between scrapes
        
        Args:
            successful_scrapes: Number of consecutive successful scrapes
        
        Returns:
            Delay in seconds
        """
        # Start conservative, speed up if successful
        if successful_scrapes < 5:
            return 5  # 5 seconds
        elif successful_scrapes < 10:
            return 4  # 4 seconds
        elif successful_scrapes < 20:
            return 3  # 3 seconds
        else:
            return 2  # 2 seconds minimum

