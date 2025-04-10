import requests
from typing import List, Dict, Optional, Union
from urllib.parse import urlparse
import time
import re


class RedirectChecker:
    def __init__(self,
                 headers: Dict[str, str] = None,
                 proxies: Dict[str, str] = None):
        """
        初始化重定向检查器

        Args:
            headers: 自定义请求头
            proxies: 代理设置，格式如 {'http': 'http://user:pass@host:port', 'https': 'http://user:pass@host:port'}
        """
        self.session = requests.Session()

        # 设置基础headers
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

        # 更新自定义headers
        if headers:
            self.base_headers.update(headers)

        # 设置代理
        if proxies:
            self.session.proxies.update(proxies)

    def _get_headers(self, additional_headers: Dict[str, str] = None) -> Dict[str, str]:
        """
        获取请求头

        Args:
            additional_headers: 额外的请求头

        Returns:
            合并后的请求头
        """
        headers = self.base_headers.copy()
        if additional_headers:
            headers.update(additional_headers)
        return headers

    def _check_meta_refresh(self, content: str) -> Optional[str]:
        """检查HTML内容中是否存在meta refresh重定向"""
        content = content.lower()
        if 'meta' in content and 'refresh' in content:
            try:
                # 匹配多种meta refresh格式
                patterns = [
                    r'<meta\s+http-equiv="refresh"\s+content="0;\s*url=(.*?)"',
                    r'<meta\s+http-equiv="refresh"\s+content="0;url=(.*?)"',
                    r'<meta\s+http-equiv=refresh\s+content="0;\s*url=(.*?)"',
                    r'<meta\s+http-equiv=refresh\s+content="0;url=(.*?)"',
                    # 处理没有引号的情况
                    r'<meta\s+http-equiv=refresh\s+content=0;\s*url=(.*?)>',
                    r'<meta\s+http-equiv="refresh"\s+content=0;\s*url=(.*?)>',
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        # 清理URL中可能存在的引号
                        url = matches[0].strip('"\'')
                        return url

                # 如果上面的模式都没匹配到，尝试更宽松的匹配
                if 'content="0' in content or "content='0" in content or "content=0" in content:
                    start_markers = ['url=', 'URL=']
                    for marker in start_markers:
                        if marker in content:
                            start = content.find(marker) + len(marker)
                            # 查找结束位置（引号或其他分隔符）
                            end_chars = ['"', "'", ' ', '>', ';']
                            end_positions = [content.find(
                                char, start) for char in end_chars]
                            end_positions = [
                                pos for pos in end_positions if pos != -1]
                            if end_positions:
                                end = min(end_positions)
                                return content[start:end].strip()

            except Exception as e:
                print(f"Meta refresh解析错误: {str(e)}")
        return None

    def check_url(self,
                  url: str,
                  additional_headers: Dict[str, str] = None,
                  debug: bool = False) -> List[Dict]:
        """
        检查URL的重定向链

        Args:
            url: 要检查的URL
            additional_headers: 额外的请求头
            debug: 是否启用调试模式

        Returns:
            重定向结果列表，每个结果为一个字典
        """
        results = []
        current_url = url
        start_time = time.time()

        while True:
            try:
                start_request = time.time()
                response = self.session.get(
                    current_url,
                    headers=self._get_headers(additional_headers),
                    allow_redirects=False,
                    timeout=10
                )
                duration = f"{time.time() - start_request:.3f} s"

                if debug and response.status_code == 200:
                    print(f"\n调试 - 页面内容预览:")
                    print(response.text[:500])
                    print("..." if len(response.text) > 500 else "")

                parsed_url = urlparse(current_url)
                result = {
                    'url': current_url,
                    'host': parsed_url.netloc,
                    'status': response.status_code,
                    'status_text': response.reason,
                    'duration': duration,
                    'meta_refresh': False,
                    'location': None
                }

                # 检查HTTP重定向
                if 300 <= response.status_code < 400:
                    result['location'] = response.headers.get('Location')
                    if result['location']:
                        if not result['location'].startswith(('http://', 'https://')):
                            result['location'] = requests.compat.urljoin(
                                current_url, result['location'])

                # 检查meta refresh重定向
                elif response.status_code == 200:
                    meta_location = self._check_meta_refresh(response.text)
                    if debug:
                        print(f"\n调试 - Meta refresh检测结果: {meta_location}")
                    if meta_location:
                        result['meta_refresh'] = True
                        result['location'] = requests.compat.urljoin(
                            current_url, meta_location)

                results.append(result)

                # 如果没有下一个重定向位置，结束检查
                if not result['location']:
                    break

                # 更新当前URL为下一个重定向位置
                current_url = result['location']

                # 防止无限重定向
                if len(results) >= 10:
                    break

            except Exception as e:
                if debug:
                    print(f"\n调试 - 发生错误: {str(e)}")
                results.append({
                    'url': current_url,
                    'host': urlparse(current_url).netloc,
                    'status': 0,
                    'status_text': f"Error: {str(e)}",
                    'duration': f"{time.time() - start_request:.3f} s",
                    'meta_refresh': False,
                    'location': None
                })
                break

        return results

    def print_url_chain(self, results: List[Dict]) -> None:
        """打印URL重定向链"""
        print("\nURL重定向链:")
        for i, result in enumerate(results):
            print(f"{result['url']}", end="")
            if i < len(results) - 1:
                print(" ->\n", end="")
        print("\n")

    def print_domain_chain(self, results: List[Dict]) -> None:
        """只打印域名重定向链"""
        print("\n域名重定向链:")
        for i, result in enumerate(results):
            print(f"{result['host']}", end="")
            if i < len(results) - 1:
                print(" -> ", end="")
        print("\n")


def main():
    # 使用示例
    # 设置代理
    proxies = {
        'http': 'http://user:pass@host:port',
        'https': 'http://user:pass@host:port'
    }

    # 设置headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
        'Referer': 'https://example.com'
    }

    # 创建检查器实例
    checker = RedirectChecker(headers=headers, proxies=proxies)

    # 测试URL
    test_urls = [
        "https://www.redirectchecker.org/meta-redirect.html"
    ]

    for url in test_urls:
        print(f"\n检查URL: {url}")
        # 可以在check_url时添加额外的headers
        results = checker.check_url(url,
                                    additional_headers={
                                        'Custom-Header': 'Value'},
                                    debug=True)
        checker.print_url_chain(results)


if __name__ == "__main__":
    main()
