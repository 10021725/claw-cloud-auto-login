"""
阿里云SMTP邮件发送模块

此模块提供了一个符合Python开发规范的邮件发送功能，
专门用于调用阿里云SMTP服务发送邮件。

作者: Claude Code
日期: 2026-01-24
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class MailResult(Enum):
    """邮件发送结果枚举"""
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class SMTPConfig:
    """SMTP配置类"""
    smtp_server: str = "smtpdm.aliyun.com"
    smtp_port: int = 80
    smtp_user: str = ""
    smtp_password: str = ""
    sender: str = ""
    receivers: List[str] = None

    def __post_init__(self):
        if self.receivers is None:
            self.receivers = []


class AliyunSMTPMailService:
    """阿里云SMTP邮件服务类

    提供基于阿里云SMTP服务的邮件发送功能，支持HTML和纯文本格式邮件。
    """

    def __init__(self, config: SMTPConfig):
        """初始化邮件服务

        Args:
            config: SMTP配置对象
        """
        self.config = config
        if not self.config.smtp_password:
            # 尝试从环境变量获取密码
            env_var = os.environ.get('DOMAIN_SMTP_PWD', '')
            if env_var:
                self.config.smtp_password = env_var


    def send_html_mail(self, subject: str, html_content: str,
                      receivers: Optional[List[str]] = None) -> MailResult:
        """发送HTML格式邮件

        Args:
            subject: 邮件主题
            html_content: HTML格式的邮件内容
            receivers: 收件人列表，如果为None则使用配置中的收件人

        Returns:
            MailResult: 邮件发送结果
        """
        if not receivers:
            receivers = self.config.receivers

        if not receivers:
            print("错误: 未指定收件人")
            return MailResult.FAILURE

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = self.config.sender
        msg['To'] = ', '.join(receivers)

        # 添加HTML内容
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        try:
            # 发送邮件
            with smtplib.SMTP(self.config.smtp_server, port=self.config.smtp_port) as server:
                server.login(self.config.smtp_user, self.config.smtp_password)
                server.sendmail(self.config.sender, receivers, msg.as_string())
                print('邮件发送成功!')
                return MailResult.SUCCESS
        except smtplib.SMTPAuthenticationError as e:
            print(f"SMTP认证错误: {e}")
            return MailResult.FAILURE
        except smtplib.SMTPRecipientsRefused as e:
            print(f"收件人被拒绝: {e}")
            return MailResult.FAILURE
        except smtplib.SMTPResponseException as e:
            print(f"SMTP响应错误: {e.smtp_code} - {e.smtp_error}")
            return MailResult.FAILURE
        except Exception as e:
            print(f"发送邮件时发生错误: {e}")
            return MailResult.FAILURE

    def send_text_mail(self, subject: str, text_content: str,
                      receivers: Optional[List[str]] = None) -> MailResult:
        """发送纯文本格式邮件

        Args:
            subject: 邮件主题
            text_content: 纯文本格式的邮件内容
            receivers: 收件人列表，如果为None则使用配置中的收件人

        Returns:
            MailResult: 邮件发送结果
        """
        if not receivers:
            receivers = self.config.receivers

        if not receivers:
            print("错误: 未指定收件人")
            return MailResult.FAILURE

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = self.config.sender
        msg['To'] = ', '.join(receivers)

        # 添加文本内容
        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))

        try:
            # 发送邮件
            with smtplib.SMTP(self.config.smtp_server, port=self.config.smtp_port) as server:
                server.login(self.config.smtp_user, self.config.smtp_password)
                server.sendmail(self.config.sender, receivers, msg.as_string())
                print('邮件发送成功!')
                return MailResult.SUCCESS
        except smtplib.SMTPAuthenticationError as e:
            print(f"SMTP认证错误: {e}")
            return MailResult.FAILURE
        except smtplib.SMTPRecipientsRefused as e:
            print(f"收件人被拒绝: {e}")
            return MailResult.FAILURE
        except smtplib.SMTPResponseException as e:
            print(f"SMTP响应错误: {e.smtp_code} - {e.smtp_error}")
            return MailResult.FAILURE
        except Exception as e:
            print(f"发送邮件时发生错误: {e}")
            return MailResult.FAILURE


def create_default_config() -> SMTPConfig:
    """创建默认的SMTP配置

    Returns:
        SMTPConfig: 配置对象
    """
    return SMTPConfig(
        smtp_server='smtpdm.aliyun.com',
        smtp_port=80,  # 阿里云普通SMTP端口
        smtp_user=os.environ.get('ALIYUN_SMTP_USER', 'your_username@your_domain'),
        smtp_password=os.environ.get('ALIYUN_SMTP_PASSWORD', ''),  # 通常使用授权码而非登录密码
        sender=os.environ.get('ALIYUN_SMTP_SENDER', 'your_username@your_domain'),
        receivers=[
            os.environ.get('DEFAULT_RECEIVER_1', 'recipient1@example.com'),
            os.environ.get('DEFAULT_RECEIVER_2', 'recipient2@example.com')
        ]
    )


def send_test_email():
    """发送测试邮件

    该函数演示如何使用AliyunSMTPMailService发送邮件
    """
    # 创建配置
    config = create_default_config()

    # 可以根据实际需要修改配置
    config.smtp_user = os.environ.get('ALIYUN_SMTP_USER', 'domain@service.ctf.com.cn')
    config.sender = os.environ.get('ALIYUN_SMTP_SENDER', 'domain@service.ctf.com.cn')
    config.receivers = ["171952355@qq.com", "xiatian@ctf.com.cn"]

    # 创建邮件服务实例
    mail_service = AliyunSMTPMailService(config)

    # 准备邮件内容
    html_content = '''
    <html>
        <head></head>
        <body>
            <h1 style="color:red;">阿里云SMTP服务测试邮件</h1>
            <p>这是一封使用阿里云SMTP服务器发送的测试邮件。</p>
            <p>时间: {time}</p>
        </body>
    </html>
    '''.format(time=__import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # 发送邮件
    result = mail_service.send_html_mail(
        subject="阿里云SMTP邮件测试",
        html_content=html_content
    )

    print(f"邮件发送结果: {result.value}")



if __name__ == '__main__':
    send_test_email()