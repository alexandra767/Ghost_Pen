"""
Instagram platform adapter using web API with session-based auth.

Setup:
  Set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in .env
  The adapter will authenticate via Instagram's web login API.

Notes:
  - Instagram requires an image for every post
  - Rate limit yourself to 2-3 posts per day to avoid blocks
"""

import os
import json
import time
import random
import uuid
import struct
from pathlib import Path
from urllib.parse import unquote

import requests

from .base import PlatformAdapter, PostResult


class InstagramAdapter(PlatformAdapter):
    """Instagram posting via web API."""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._logged_in = False
        self._user_id = None
        self.session_file = os.path.expanduser("~/.instagram_web_session.json")

        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'X-Requested-With': 'XMLHttpRequest',
            'X-IG-App-ID': '936619743392459',
            'Referer': 'https://www.instagram.com/',
            'Origin': 'https://www.instagram.com',
        })

    @property
    def platform_name(self) -> str:
        return "instagram"

    @property
    def max_content_length(self) -> int:
        return 2200

    def _save_session(self):
        """Save session cookies to file."""
        data = {
            'cookies': dict(self.session.cookies),
            'user_id': self._user_id,
        }
        with open(self.session_file, 'w') as f:
            json.dump(data, f)

    def _load_session(self) -> bool:
        """Try to load a saved session."""
        if not os.path.exists(self.session_file):
            return False
        try:
            with open(self.session_file) as f:
                data = json.load(f)
            for name, value in data.get('cookies', {}).items():
                self.session.cookies.set(name, value, domain='.instagram.com')
            self._user_id = data.get('user_id')

            # Verify session is still valid
            self.session.headers['X-CSRFToken'] = self.session.cookies.get('csrftoken', '')
            r = self.session.get('https://www.instagram.com/api/v1/web/accounts/current_user/', timeout=10)
            if r.status_code == 200 and r.json().get('user', {}).get('username') == self.username:
                print(f"Instagram: restored saved session for {self.username}")
                return True
            return False
        except Exception as e:
            print(f"Instagram: saved session invalid ({e})")
            return False

    def _login(self):
        """Login via Instagram web API."""
        if self._logged_in:
            return

        # Try saved session first
        if self._load_session():
            self._logged_in = True
            return

        # Fresh web login
        r = self.session.get('https://www.instagram.com/accounts/login/', timeout=10)
        csrf = self.session.cookies.get('csrftoken', '')
        if not csrf:
            raise RuntimeError("Instagram: could not get CSRF token")

        self.session.headers['X-CSRFToken'] = csrf

        login_data = {
            'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:0:{self.password}',
            'username': self.username,
            'queryParams': '{}',
            'optIntoOneTap': 'false',
        }

        time.sleep(random.uniform(1, 3))

        r2 = self.session.post(
            'https://www.instagram.com/accounts/login/ajax/',
            data=login_data,
            timeout=15,
        )

        resp = r2.json()
        if not resp.get('authenticated'):
            error = resp.get('message', 'Login failed')
            if resp.get('two_factor_required'):
                error = 'Two-factor authentication is enabled. Disable it temporarily or use an app password.'
            raise RuntimeError(f"Instagram login failed: {error}")

        self._user_id = resp.get('userId')
        self._logged_in = True

        # Update CSRF after login
        csrf = self.session.cookies.get('csrftoken', '')
        if csrf:
            self.session.headers['X-CSRFToken'] = csrf

        self._save_session()
        print(f"Instagram: logged in as {self.username} (ID: {self._user_id})")

    def _get_image_dimensions(self, image_path: str):
        """Get image width and height from PNG file header."""
        try:
            with open(image_path, 'rb') as f:
                header = f.read(32)
                if header[:8] == b'\x89PNG\r\n\x1a\n':
                    w, h = struct.unpack('>II', header[16:24])
                    return w, h
                # JPEG
                f.seek(0)
                data = f.read()
                i = 2
                while i < len(data) - 1:
                    if data[i] != 0xFF:
                        break
                    marker = data[i + 1]
                    if marker in (0xC0, 0xC1, 0xC2):
                        h = (data[i + 5] << 8) + data[i + 6]
                        w = (data[i + 7] << 8) + data[i + 8]
                        return w, h
                    size = (data[i + 2] << 8) + data[i + 3]
                    i += 2 + size
        except Exception:
            pass
        return 1080, 1080  # Default square

    async def post(
        self,
        content: str,
        image_path: str = None,
        **kwargs,
    ) -> PostResult:
        """Post a photo with caption to Instagram via web API."""
        if not image_path:
            return PostResult(
                success=False,
                platform="instagram",
                error="Instagram requires an image.",
            )

        if not os.path.exists(image_path):
            return PostResult(
                success=False,
                platform="instagram",
                error=f"Image not found: {image_path}",
            )

        try:
            self._login()
        except Exception as e:
            return PostResult(success=False, platform="instagram", error=str(e))

        caption = content[:2200]
        time.sleep(random.uniform(1, 3))

        try:
            # Step 1: Upload the image
            upload_id = str(int(time.time() * 1000))
            w, h = self._get_image_dimensions(image_path)

            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Determine content type
            ct = 'image/png' if image_path.lower().endswith('.png') else 'image/jpeg'

            rupload_params = json.dumps({
                "media_type": 1,
                "upload_id": upload_id,
                "upload_media_height": h,
                "upload_media_width": w,
                "xsharing_user_ids": "[]",
                "image_compression": json.dumps({
                    "lib_name": "moz",
                    "lib_version": "3.1.m",
                    "quality": "80",
                }),
            })

            upload_name = f"{upload_id}_0_{random.randint(1000000000, 9999999999)}"
            upload_url = f"https://i.instagram.com/rupload_igphoto/{upload_name}"

            upload_headers = {
                'X-Entity-Name': upload_name,
                'X-Entity-Length': str(len(image_data)),
                'X-Entity-Type': ct,
                'X-Instagram-Rupload-Params': rupload_params,
                'Content-Type': 'application/octet-stream',
                'Offset': '0',
            }

            r_upload = self.session.post(
                upload_url,
                data=image_data,
                headers=upload_headers,
                timeout=60,
            )

            if r_upload.status_code != 200:
                return PostResult(
                    success=False,
                    platform="instagram",
                    error=f"Image upload failed: HTTP {r_upload.status_code}",
                )

            upload_resp = r_upload.json()
            if upload_resp.get('status') != 'ok':
                return PostResult(
                    success=False,
                    platform="instagram",
                    error=f"Image upload rejected: {upload_resp}",
                )

            time.sleep(random.uniform(2, 4))

            # Step 2: Configure/publish the post
            csrf = self.session.cookies.get('csrftoken', '')
            if csrf:
                self.session.headers['X-CSRFToken'] = csrf

            configure_data = {
                'upload_id': upload_id,
                'caption': caption,
                'usertags': '',
                'custom_accessibility_caption': '',
                'retry_timeout': '',
                'source_type': 'library',
            }

            r_configure = self.session.post(
                'https://www.instagram.com/api/v1/media/configure/',
                data=configure_data,
                timeout=30,
            )

            if r_configure.status_code != 200:
                return PostResult(
                    success=False,
                    platform="instagram",
                    error=f"Post configure failed: HTTP {r_configure.status_code}",
                )

            conf_resp = r_configure.json()
            if conf_resp.get('status') == 'ok':
                media = conf_resp.get('media', {})
                code = media.get('code', '')
                pk = media.get('pk', '')
                return PostResult(
                    success=True,
                    platform="instagram",
                    post_id=str(pk),
                    url=f"https://www.instagram.com/p/{code}/" if code else None,
                )
            else:
                return PostResult(
                    success=False,
                    platform="instagram",
                    error=f"Post failed: {conf_resp.get('message', conf_resp)}",
                )

        except Exception as e:
            return PostResult(success=False, platform="instagram", error=str(e))

    async def validate_credentials(self) -> bool:
        """Check Instagram login."""
        try:
            self._login()
            return True
        except Exception:
            return False
