import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
# SMTP 邮件发送配置
smtp_config = {
    'smtp_server': 'smtpdm.aliyun.com',
    'smtp_user': 'domain@service.ctf.com.cn',
    'smtp_password': os.environ.get('domain_smtp_pwd'),
    'sender': 'domain@service.ctf.com.cn',
    'receivers': [
        "171952355@qq.com",
        "xiatian@ctf.com.cn"
    ]
}

def send_html(text,title,smtp_server, smtp_user, smtp_password, sender, receivers):
    # 发送html内容的邮件
    msg = MIMEMultipart()
    msg['Subject'] = title
    msg['From'] = sender
    msg['To'] = ', '.join(receivers)
    # 添加正文内容
    msg.attach(MIMEText(text, 'html', 'utf-8'))
    try:
    # 发送邮件
        with smtplib.SMTP(smtp_server,port=80) as server:
            #server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(sender, receivers, msg.as_string())
            print('Sent Successfully!')
    except smtplib.SMTPResponseException as e:
        print(f"SMTP Response Error: {e.smtp_code} - {e.smtp_error}")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == '__main__':
    text = '<h1 style="color:red;">This is a test email from Python!</h1><p>This email is sent using SMTP server.</p>'
    send_html(text, title="claw cloud 邮件测试", **smtp_config)
