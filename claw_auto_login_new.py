"""
Claw Cloud 自动登录服务

该模块提供自动化登录 Claw Cloud 的功能，用于防止账号因闲置而被回收。
遵循 CLAUDE.md 中的 DDD 和 Pythonic 设计原则。
"""

import os
import sys
import time
import logging
from dataclasses import dataclass
from typing import Optional, List, Protocol
from abc import ABC, abstractmethod

# 尝试导入 DrissionPage，如果不存在则提示
try:
    from DrissionPage import ChromiumPage, ChromiumOptions
    from DrissionPage.items import ChromiumElement
except ImportError:
    print("错误: 未安装 DrissionPage。请运行 pip install DrissionPage")
    sys.exit(1)

# 添加父目录到 sys.path 以导入 xt_mail
current_dir = os.getcwd()
parent_dir = os.path.join(current_dir, os.pardir)
sys.path.insert(0, parent_dir)

try:
    from xt_mail import send_html, smtp_config
except ImportError:
    # 模拟 xt_mail 模块用于开发环境或缺少依赖时
    logging.warning("无法导入 xt_mail，将使用模拟邮件发送功能")

    def send_html(text, title, **kwargs):
        print(f"模拟发送邮件: 标题={title}")

    smtp_config = {}

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# --- Domain Layer (领域层) ---

@dataclass
class BrowserConfig:
    """浏览器配置值对象"""
    user_data_path: str
    browser_path: Optional[str] = None
    headless: bool = True
    local_port: int = 9222

    def __post_init__(self):
        # 如果未提供路径，尝试使用默认值或环境变量
        if not self.browser_path:
            # 尝试常见的 Edge 安装路径
            common_paths = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            ]
            for path in common_paths:
                if os.path.exists(path):
                    self.browser_path = path
                    break

            if not self.browser_path:
                logger.warning("未找到 Edge 浏览器路径，将使用 DrissionPage 默认设置")

@dataclass
class LoginResult:
    """登录结果值对象"""
    claw_cloud_success: bool
    ap_southeast_success: bool
    message: str = ""

    @property
    def is_fully_successful(self) -> bool:
        return self.claw_cloud_success and self.ap_southeast_success


class NotificationService(Protocol):
    """通知服务接口"""
    def send(self, title: str, content: str) -> bool: ...


class EmailNotificationService(NotificationService):
    """邮件通知服务实现"""
    def __init__(self, config: dict):
        self.config = config

    def send(self, title: str, content: str) -> bool:
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                send_html(content, title, **self.config)
                logger.info(f"邮件发送成功: {title}")
                return True
            except Exception as e:
                logger.error(f"邮件发送失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                if attempt == max_retries:
                    return False
        return False


# --- Infrastructure Layer (基础设施层) ---

class BrowserDriver(ABC):
    """浏览器驱动抽象基类"""
    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def visit(self, url: str) -> None: ...

    @abstractmethod
    def find_element(self, selector: str, timeout: float = 2.0) -> Optional[object]: ...

    @abstractmethod
    def click_element(self, selector: str) -> bool: ...


class DrissionPageDriver(BrowserDriver):
    """基于 DrissionPage 的浏览器驱动实现"""
    def __init__(self, config: BrowserConfig):
        self.config = config
        self.page: Optional[ChromiumPage] = None

    def start(self) -> None:
        co = ChromiumOptions()
        if self.config.browser_path:
            co.set_browser_path(self.config.browser_path)

        co.set_local_port(self.config.local_port)
        co.set_user_data_path(self.config.user_data_path)

        if self.config.headless:
            co.headless(True)

        # 模拟真实用户行为
        co.set_argument("--start-maximized")
        co.set_argument("--no-first-run")
        co.set_argument("--disable-blink-features=AutomationControlled")

        self.page = ChromiumPage(addr_or_opts=co)
        logger.info("浏览器驱动已启动")

    def close(self) -> None:
        if self.page:
            self.page.quit()
            logger.info("浏览器驱动已关闭")

    def visit(self, url: str) -> None:
        if not self.page:
            raise RuntimeError("Browser not started")
        logger.info(f"访问 URL: {url}")
        self.page.get(url)

    def find_element(self, selector: str, timeout: float = 2.0) -> Optional[ChromiumElement]:
        if not self.page:
            raise RuntimeError("Browser not started")
        try:
            ele = self.page.ele(selector, timeout=timeout)
            return ele if ele else None
        except Exception:
            return None

    def find_elements(self, selector: str) -> List[ChromiumElement]:
        if not self.page:
            raise RuntimeError("Browser not started")
        return self.page.eles(selector)

    def click_element(self, selector: str) -> bool:
        ele = self.find_element(selector)
        if ele:
            try:
                ele.click()
                return True
            except Exception as e:
                logger.warning(f"点击元素失败 {selector}: {e}")
                return False
        return False

    def wait(self, seconds: float) -> None:
        if self.page:
            self.page.wait(seconds)

    def get_url(self) -> str:
        return self.page.url if self.page else ""

    def new_tab(self, url: str):
        if self.page:
            return self.page.new_tab(url)
        return None


# --- Application Layer (应用层) ---

class ClawLoginService:
    """Claw Cloud 登录服务"""

    GITHUB_LOGIN_SELECTORS = [
        "xpath:/html/body/div[2]/div[1]/div/div/div/div[1]/div[2]/div/div[2]/button",
        'xpath:/html/body/div[2]/div[1]/div/div/div/div[1]/div[2]/div/div[2]/button/a/span',
        'text():Sign in with GitHub',
        'text():使用github账号登陆',
        'text():GitHub 登录',
        'button:contains("GitHub")',
        '.github-login'
    ]

    GITHUB_AUTH_SELECTORS = [
        'xpath:/html/body/div[1]/div[4]/main/div/div[2]/form/div[3]/input',
        'text():Sign in',
        'text():Authorize',
        'text():授权',
        'text():同意授权',
        'input[type="submit"][value*="uthoriz"]',
        'input[type="submit"][value*="授权"]'
    ]

    def __init__(self, driver: DrissionPageDriver, notifier: NotificationService):
        self.driver = driver
        self.notifier = notifier

    def run(self) -> LoginResult:
        """执行完整的登录流程"""
        try:
            self.driver.start()

            # 1. 登录 claw.cloud
            claw_success = self._login_site(
                "https://claw.cloud/login",
                "text():客户中心",
                self.GITHUB_LOGIN_SELECTORS
            )

            # 2. 登录 ap-southeast-1.run.claw.cloud
            # 注意：第二个站点使用新标签页逻辑，这里为了简化复用 driver 逻辑，
            # 我们可以直接访问，或者在 driver 中封装多标签页逻辑。
            # 鉴于原始代码使用了 new_tab，我们这里简单处理为直接访问，
            # 因为 DrissionPage 的 get() 也会在当前标签页导航。
            ap_success = self._login_site(
                "https://ap-southeast-1.run.claw.cloud",
                'xpath://img[contains(@src, "avatars.githubusercontent.com")]',
                ['xpath:/html/body/div[1]/div/div/div[2]/div/div[3]/button[1]']
            )

            result = LoginResult(claw_success, ap_success)
            self._handle_result(result)
            return result

        except Exception as e:
            logger.exception("登录过程发生未捕获异常")
            return LoginResult(False, False, str(e))
        finally:
            self.driver.close()

    def _login_site(self, url: str, success_marker: str, login_selectors: List[str]) -> bool:
        """通用的单站点登录逻辑"""
        logger.info(f"开始登录站点: {url}")
        self.driver.visit(url)

        # 检查是否已登录
        if self.driver.find_element(success_marker):
            logger.info(f"检测到已登录状态 ({success_marker})")
            return True

        logger.info("未登录，开始尝试 GitHub 登录...")

        # 尝试点击登录按钮
        if not self._try_click_any(login_selectors):
            logger.warning("未找到登录按钮")
            return False

        logger.info("已点击登录按钮，等待跳转...")
        self.driver.wait(2)

        # 处理 GitHub 授权
        if "github.com" in self.driver.get_url() or self.driver.find_element("text():Sign in to GitHub"):
            return self._handle_github_auth()

        # 再次检查是否登录成功 (可能直接跳转回去了)
        if self.driver.find_element(success_marker):
            return True

        return False

    def _handle_github_auth(self) -> bool:
        """处理 GitHub 授权页面"""
        logger.info("进入 GitHub 授权流程")

        # 查找授权按钮
        for _ in range(10): # 重试几次
            if self._try_click_any(self.GITHUB_AUTH_SELECTORS):
                logger.info("点击了 GitHub 授权/登录按钮")
                self.driver.wait(3)
                return True
            self.driver.wait(1)

        logger.warning("未找到 GitHub 授权按钮")
        return False

    def _try_click_any(self, selectors: List[str]) -> bool:
        """尝试点击列表中的任意一个元素"""
        for selector in selectors:
            if self.driver.click_element(selector):
                logger.info(f"成功点击元素: {selector}")
                return True
        return False

    def _handle_result(self, result: LoginResult) -> None:
        """处理结果并发送通知"""
        status_text = "成功" if result.is_fully_successful else "失败"
        title = f"claw cloud 自动登录结果 - {status_text}"

        content = f"""
        <h2>claw cloud 自动登录结果</h2>
        <p>claw.cloud 登录: {'成功' if result.claw_cloud_success else '失败'}</p>
        <p>ap-southeast-1.run.claw.cloud 登录: {'成功' if result.ap_southeast_success else '失败'}</p>
        <p>附加信息: {result.message}</p>
        """

        self.notifier.send(title, content)


# --- Main Entry Point (入口) ---

def main():
    """主程序入口"""
    # 配置文件路径
    profile_dir = r"C:\temp\claw_cloud_profile"
    os.makedirs(profile_dir, exist_ok=True)

    # 初始化配置
    config = BrowserConfig(
        user_data_path=profile_dir,
        headless=True  # 生产环境通常使用 headless
    )

    # 初始化依赖
    driver = DrissionPageDriver(config)
    notifier = EmailNotificationService(smtp_config)

    # 执行服务
    service = ClawLoginService(driver, notifier)
    service.run()

if __name__ == "__main__":
    main()
