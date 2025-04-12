import requests
from typing import List, Dict, Optional, Union
from urllib.parse import urlparse
import time
import re


class RedirectChecker:
    def __init__(self):
        """初始化重定向检查器"""
        self.session = requests.Session()
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

    def check_url(self, 
                  url: str, 
                  headers: Dict[str, str] = None, 
                  proxies: Dict[str, str] = None,
                  timeout: int = 5,
                  max_hops: int = 10) -> Dict[str, Union[List[str], str]]:
        """
        检查URL的重定向链

        Args:
            url: 要检查的URL
            headers: 请求头
            proxies: 代理设置
            timeout: 超时时间（秒）
            max_hops: 最大跳转次数

        Returns:
            dict: 包含重定向路径和最终URL的字典
        """
        if headers:
            self.base_headers.update(headers)
        
        if proxies:
            self.session.proxies.update(proxies)

        results = []
        current_url = url
        redirect_path = [url]

        for _ in range(max_hops):
            try:
                response = self.session.get(
                    current_url,
                    headers=self.base_headers,
                    allow_redirects=False,
                    timeout=timeout
                )

                print(f"状态：{response.status_code}  URL：{current_url} headers：{self.session.headers} proxies：{self.session.proxies}")

                # 检查HTTP重定向
                if 300 <= response.status_code < 400 and 'Location' in response.headers:
                    next_url = response.headers['Location']
                    if not next_url.startswith(('http://', 'https://')):
                        next_url = requests.compat.urljoin(current_url, next_url)
                    redirect_path.append(next_url)
                    current_url = next_url
                    continue

                # 检查meta refresh重定向
                if response.status_code == 200:
                    meta_location = self._check_meta_refresh(response.text)
                    if meta_location:
                        next_url = requests.compat.urljoin(current_url, meta_location)
                        redirect_path.append(next_url)
                        current_url = next_url
                        continue
                break

            except Exception as e:
                print(f"检查重定向时出错: {str(e)}")
                break

        return {
            'redirect_path': redirect_path,
            'target_url': redirect_path[-1] if redirect_path else url
        }

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
    """使用示例"""
    # 测试URL
    test_url = "https://www.redirectchecker.org/meta-redirect.html"
    
    # 设置headers和proxies
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
        'Referer': 'https://example.com'
    }
    proxies = {
        'http': 'http://user:pass@host:port',
        'https': 'http://user:pass@host:port'
    }

    # 创建检查器实例并检查URL
    checker = RedirectChecker()
    result = checker.check_url(
        url=test_url,
        headers=headers,
        proxies=proxies,
        timeout=5,
        max_hops=10
    )
    
    print(f"\n检查URL: {test_url}")
    print("重定向路径:", " -> ".join(result['redirect_path']))
    print("最终URL:", result['target_url'])


if __name__ == "__main__":
    main()
