"""Conditional, read-only GitHub transport for the server, using the existing gh login."""
import json
import re
import subprocess
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit
from .github import APIError, GitHub


class CachedGitHub(GitHub):
    def __init__(self, repository, state, command=None, *, conditional=True):
        super().__init__(repository, command)
        self.state = state
        self.conditional = conditional

    def confirm_empty(self):
        # Deleting/transferring the final Issue needs a second independent,
        # unconditional complete read before replacing an existing nonempty board.
        return not CachedGitHub(self.repository, self.state, self.command, conditional=False).issues()

    def safe_path(self, path):
        if not isinstance(path, str) or any(ord(c) < 33 for c in path):
            raise APIError('Invalid GitHub response path')
        parsed = urlsplit(path)
        if parsed.scheme or parsed.netloc:
            if parsed.scheme != 'https' or parsed.netloc != 'api.github.com':
                raise APIError('Untrusted GitHub pagination origin')
            path = parsed.path.lstrip('/') + ('?' + parsed.query if parsed.query else '')
        if parsed.fragment or not path.startswith(self.root + '/') or '..' in urlsplit(path).path.split('/'):
            raise APIError('GitHub pagination crossed repository boundary')
        return path

    def next_page(self, headers, current):
        for part in headers.get('link', '').split(','):
            match = re.fullmatch(r'\s*<([^>]+)>;\s*rel="([^"]+)"\s*', part)
            if part.strip() and not match:
                raise APIError('Malformed GitHub pagination link')
            if match and match[2] == 'next':
                parsed = urlsplit(match[1])
                numeric = re.fullmatch(r'/repositories/[1-9]\d*(/.*)', parsed.path)
                if numeric and parsed.scheme == 'https' and parsed.netloc == 'api.github.com' and not parsed.fragment:
                    # GitHub can emit numeric repository URLs. Never trust an ID
                    # to select another repo: reuse our known endpoint and only its next query.
                    if numeric[1] != urlsplit(current).path[len(self.root):]:
                        raise APIError('Pagination changed the GitHub resource')
                    return self.safe_path(urlsplit(current).path + '?' + parsed.query)
                return self.safe_path(match[1])
        return None

    def rate_limit(self, status, headers):
        if status not in (403, 429) and headers.get('x-ratelimit-remaining') != '0':
            return
        now = self.state.clock()
        until = now + 60
        try:
            if headers.get('retry-after'):
                retry = headers['retry-after']
                until = max(until, now + float(retry) if retry.isdigit() else parsedate_to_datetime(retry).timestamp())
            if headers.get('x-ratelimit-remaining') == '0':
                until = max(until, float(headers['x-ratelimit-reset']) + 2)
        except (ValueError, KeyError, TypeError, OverflowError):
            pass
        self.state.block_until(until)

    def page(self, path, optional=False):
        path = self.safe_path(path)
        if self.state.blocked_until() > self.state.clock():
            raise APIError('GitHub requests paused until rate-limit recovery')
        # Blobs are content-addressed and change with every state version (>1 MB each):
        # caching them would add one large row per write without ever saving a request.
        storable = '/git/blobs/' not in urlsplit(path).path
        cached = self.state.cached(path) if self.conditional and storable else None
        command = self.command + ['api', '--method', 'GET', '--include', path,
                                  '-H', 'Accept: application/vnd.github+json',
                                  '-H', 'X-GitHub-Api-Version: 2022-11-28']
        if cached and cached['etag']:
            command += ['-H', 'If-None-Match: ' + cached['etag']]
        self.state.count('requests')
        try:
            response = subprocess.run(command, text=True, capture_output=True, timeout=90)
        except (OSError, subprocess.TimeoutExpired):
            self.state.count('errors')
            raise APIError('GitHub request unavailable') from None
        header_text, separator, body = response.stdout.replace('\r\n', '\n').partition('\n\n')
        lines = header_text.splitlines()
        match = re.fullmatch(r'HTTP/\S+ (\d{3})(?: .*)?', lines[0]) if lines else None
        if not separator or not match:
            self.state.count('errors')
            raise APIError('Invalid GitHub HTTP response')
        status = int(match[1])
        headers = {k.lower().strip(): v.strip() for line in lines[1:] if ':' in line for k, v in [line.split(':', 1)]}
        self.rate_limit(status, headers)
        if status == 304 and cached and cached['etag']:
            self.state.count('not_modified')
            next_path = self.next_page(headers, path) if 'link' in headers else cached['next']
            return cached['value'], self.safe_path(next_path) if next_path else None
        if status == 404:
            self.state.forget(path)
            if optional:
                self.state.count('optional_missing')
                return None, None
        if status != 200 or response.returncode:
            self.state.count('errors')
            raise APIError(f'GitHub GET failed (HTTP {status})', status)
        try:
            value = json.loads(body)
            next_path = self.next_page(headers, path)
        except (ValueError, APIError):
            self.state.count('errors')
            raise APIError('Invalid GitHub JSON or pagination') from None
        if storable:
            self.state.cache(path, headers.get('etag'), value, next_path)
        self.state.count('responses_200')
        return value, next_path

    def request(self, path, method='GET', payload=None, paginate=False, optional=False):
        if method != 'GET' or payload is not None:
            raise ValueError('The synchronization transport is read-only')
        if not paginate:
            return self.page(path, optional)[0]
        rows, seen = [], set()
        while path:
            path = self.safe_path(path)
            if path in seen or len(seen) >= 1000:
                raise APIError('GitHub pagination loop or excessive page count')
            seen.add(path)
            page, path = self.page(path, optional)
            if not isinstance(page, list):
                raise APIError('Expected complete GitHub pages')
            rows.extend(page)
        return rows
