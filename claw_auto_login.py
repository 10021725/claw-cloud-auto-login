# 使用drission 自动登录claw cloud，避免被识别为闲置账号导致pod被删除
from DrissionPage import ChromiumPage, ChromiumOptions
import os
import time

# 创建配置文件目录
profile_dir = r"C:\temp\claw_cloud_profile"
os.makedirs(profile_dir, exist_ok=True)

def login_to_claw_cloud():
    """
    使用DrissionPage模拟用户打开Edge浏览器访问https://claw.cloud/login，
    并点击“使用github账号登陆”
    """
    # 配置ChromiumOptions以使用Edge浏览器
    co = ChromiumOptions()

    # 设置Edge浏览器路径
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    co.set_browser_path(edge_path)

    # 设置固定的用户数据目录（浏览器配置文件）确保每次使用相同的用户配置
    co.set_local_port(9222)  # 固定端口
    co.set_user_data_path(r"C:\temp\claw_cloud_profile")  # 固定用户配置文件

    # 可选：设置其他选项来更好地模拟真实用户行为
    co.set_argument("--start-maximized")  # 最大化窗口
    co.set_argument("--no-first-run")
    co.set_argument("--disable-blink-features=AutomationControlled")

    # 创建页面实例
    page = ChromiumPage(addr_or_opts=co)

    try:
        # 访问登录页面
        print("正在打开 https://claw.cloud/login...")
        page.get("https://claw.cloud/login")

        # 检测是否已经登录（检查是否存在"客户中心"）
        print("正在检测登录状态...")
        customer_center_elements = page.eles('text():客户中心')

        if customer_center_elements:
            print("检测到已登录状态（找到'客户中心'），跳过登录步骤")
            button_found = True  # 标记为已登录，跳过后续登录流程
        else:
            print("未检测到登录状态，开始执行登录流程...")

            # 等待页面加载并查找GitHub登录按钮
            print("正在等待GitHub登录按钮出现...")

            # 持续查找按钮直到找到为止
            button_found = False
            attempts = 0
            max_attempts = 10  # 最大尝试次数，防止无限循环

            while not button_found and attempts < max_attempts:
                # 尝试多种可能的选择器（包括中文和英文版本）
                github_login_selectors = [
                    "xpath:/html/body/div[2]/div[1]/div/div/div/div[1]/div[2]/div/div[2]/button",  # 你提供的精确XPath
                    'xpath:/html/body/div[2]/div[1]/div/div/div/div[1]/div[2]/div/div[2]/button/a/span',  # 原始精确的XPath你提供的
                    'text():Sign in with GitHub',
                    'text():Sign in with Github',
                    'text():signin with github',
                    'text():Sign In With GitHub',
                    'text():使用github账号登陆',
                    'text():使用 GitHub 账号登录',
                    'text():GitHub 登录',
                    'button:contains("github")',
                    'button:contains("GitHub")',
                    '[data-testid="github-login"]',
                    '.github-login',
                    '#github-login'
                ]

                for selector in github_login_selectors:
                    try:
                        element = page.ele(selector, timeout=0.5)  # 使用较短的超时时间
                        if element:
                            print(f"找到登录按钮，使用选择器: {selector}")
                            print(f"按钮文本: {element.text}")

                            # 对于XPath，可能需要点击父级元素，比如button
                            if "xpath:" in selector and "/span" in selector:
                                # 点击span的父级button元素
                                parent_button = element.parent(tag='button')
                                if parent_button:
                                    parent_button.click()
                                else:
                                    # 如果找不到父级button，则直接点击当前元素
                                    element.click()
                            elif "xpath:" in selector and "/button" in selector:
                                # 对于按钮的XPath，直接点击
                                element.click()
                            else:
                                element.click()  # 直接点击元素
                            button_found = True
                            break
                    except:
                        continue

                if not button_found:
                    print(f"第 {attempts + 1} 次尝试未找到按钮，继续等待...")
                    page.wait(1)  # 等待1秒后再次尝试
                    attempts += 1

        if not button_found:
            print("警告: 未找到'使用github账号登陆'按钮，请检查页面元素")
            # 尝试直接通过索引获取"Sign in with GitHub"按钮
            try:
                # 获取页面上所有的按钮元素
                buttons = page.eles('tag:button')
                for i, btn in enumerate(buttons):
                    if "github" in btn.text.lower():
                        print(f"找到包含'github'的按钮 {i}: {btn.text}")
                        btn.click()  # 使用正常点击方法
                        button_found = True
                        break
            except Exception as e:
                print(f"尝试通过索引查找按钮失败: {str(e)}")

            if not button_found:
                print("页面上找到的按钮:")
                for i, btn in enumerate(buttons):
                    print(f"  {i}: {btn.text}")

        if button_found:
            print("已点击GitHub登录按钮，正在等待页面跳转...")
            # 等待页面跳转到GitHub登录页面或处理弹窗
            # 等待至少2秒以确保页面状态变化
            page.wait(2)

            # 先检查当前URL是否有变化
            initial_url = page.url

            # 尝试等待URL变化，但以非异常方式处理
            url_changed = False
            try:
                page.wait.url_change(timeout=15)  # 等待URL变化
                print(f"页面已跳转到: {page.url}")
                url_changed = True
            except:
                print(f"页面未跳转，当前仍在: {page.url}")

            # 检查是否跳转到了GitHub授权页面
            current_url = page.url
            if url_changed or "github.com" in current_url.lower():
                if "github.com" in current_url.lower():
                    print("检测到GitHub相关页面，正在查找授权按钮...")

                    # 等待并点击GitHub授权按钮
                    auth_button_found = False
                    auth_attempts = 0
                    max_auth_attempts = 10

                    while not auth_button_found and auth_attempts < max_auth_attempts:
                        try:
                            # 尝试使用提供的XPath
                            auth_element = page.ele('xpath:/html/body/div[1]/div[4]/main/div/div[2]/form/div[3]/input', timeout=0.5)

                            if auth_element:
                                # 获取按钮的文本或值属性
                                element_text = ""
                                try:
                                    element_text = auth_element.text.lower()
                                except:
                                    pass

                                # 尝试获取value属性（对于input元素）
                                try:
                                    element_value = auth_element.attr('value')
                                    if element_value:
                                        element_text = element_value.lower()
                                except:
                                    pass

                                print(f"当前找到的按钮文本/值: {element_text}")

                                if 'sign in' in element_text or 'authorize' in element_text or '授权' in element_text:
                                    print("找到匹配条件的GitHub授权按钮，正在点击...")
                                    auth_element.click()
                                    auth_button_found = True
                                    break
                                else:
                                    print("找到的元素不匹配所需文本，继续搜索...")
                        except Exception as e:
                            print(f"查找授权按钮时出错: {str(e)}")
                            pass

                        # 尝试其他可能的授权按钮选择器
                        auth_selectors = [
                            'text():Sign in', 'text():Sign in with GitHub', 'text():Sign in to continue',
                            'text():Authorize', 'text():Authorize application',
                            'text():授权', 'text():同意授权', 'button:contains("uthoriz")',
                            'input[type="submit"][value*="uthoriz"]',
                            'input[type="submit"][value*="授权"]',
                            'input[type="submit"][value*="ign in"]',
                            'input[value*="Sign in"]'
                        ]

                        for selector in auth_selectors:
                            try:
                                auth_element = page.ele(selector, timeout=0.5)
                                if auth_element:
                                    print(f"找到授权按钮，使用选择器: {selector}")
                                    auth_element.click()
                                    auth_button_found = True
                                    break
                            except:
                                continue

                        if not auth_button_found:
                            print(f"第 {auth_attempts + 1} 次尝试未找到授权按钮，继续等待...")
                            page.wait(1)
                            auth_attempts += 1

                    if not auth_button_found:
                        print("警告: 未找到GitHub授权按钮，请手动完成授权")
                    else:
                        print("已点击GitHub授权按钮")
                else:
                    # 如果没有跳转到GitHub页面，可能是在同域下处理登录，等待一段时间看是否有授权页面出现
                    print("页面未跳转到GitHub，正在继续等待可能的授权页面...")
                    page.wait(5)  # 等待5秒看看是否有授权页面出现

                    # 再次检查URL是否变成了GitHub相关的授权页面
                    if "github.com" in page.url.lower():
                        print("检测到GitHub授权页面，正在查找授权按钮...")

                        auth_button_found = False
                        auth_attempts = 0
                        max_auth_attempts = 50

                        while not auth_button_found and auth_attempts < max_auth_attempts:
                            try:
                                # 尝试使用提供的XPath
                                auth_element = page.ele('xpath:/html/body/div[1]/div[4]/main/div/div[2]/form/div[3]/input', timeout=0.5)

                                if auth_element:
                                    element_text = auth_element.text.lower()
                                    if 'sign in' in element_text or 'authorize' in element_text or '授权' in element_text:
                                        print("找到GitHub授权按钮")
                                        auth_element.click()
                                        auth_button_found = True
                                        break
                            except:
                                pass

                            # 尝试其他可能的授权按钮选择器
                            auth_selectors = [
                                'text():Sign in', 'text():Sign in with GitHub', 'text():Sign in to continue',
                                'text():Authorize', 'text():Authorize application',
                                'text():授权', 'text():同意授权', 'button:contains("uthoriz")',
                                'input[type="submit"][value*="uthoriz"]',
                                'input[type="submit"][value*="授权"]',
                                'input[type="submit"][value*="ign in"]',
                                'input[value*="Sign in"]'
                            ]

                            for selector in auth_selectors:
                                try:
                                    auth_element = page.ele(selector, timeout=0.5)
                                    if auth_element:
                                        print(f"找到授权按钮，使用选择器: {selector}")
                                        auth_element.click()
                                        auth_button_found = True
                                        break
                                except:
                                    continue

                            if not auth_button_found:
                                print(f"第 {auth_attempts + 1} 次尝试未找到授权按钮，继续等待...")
                                page.wait(1)
                                auth_attempts += 1

                        if not auth_button_found:
                            print("警告: 未找到GitHub授权按钮，请手动完成授权")
                        else:
                            print("已点击GitHub授权按钮")
            else:
                print("页面似乎没有跳转，可能在同一页处理登录流程")

                # 等待一段时间看是否有动态内容加载
                page.wait(5)

                # 检查是否有弹窗或模态框出现
                try:
                    modal_selectors = [
                        'xpath://*[contains(@class, "modal")]',
                        'xpath://*[contains(@class, "popup")]',
                        'xpath://*[contains(@class, "dialog")]',
                        'tag:iframe'
                    ]

                    for selector in modal_selectors:
                        try:
                            modal = page.ele(selector, timeout=1)
                            if modal:
                                print(f"检测到可能的弹窗/iframe: {selector}")
                                # 切换到iframe上下文
                                if modal.tag == 'iframe':
                                    frame = page.get_frame(modal)
                                    if frame:
                                        frame.switch.to()
                                        print("已切换到iframe上下文")

                                        # 在iframe中查找授权按钮
                                        auth_button_found = False
                                        auth_attempts = 0
                                        max_auth_attempts = 50

                                        while not auth_button_found and auth_attempts < max_auth_attempts:
                                            try:
                                                auth_element = frame.ele('xpath:/html/body/div[1]/div[4]/main/div/div[2]/form/div[3]/input', timeout=0.5)

                                                if auth_element:
                                                    element_text = auth_element.text.lower()
                                                    if 'sign in' in element_text or 'authorize' in element_text or '授权' in element_text:
                                                        print("在iframe中找到GitHub授权按钮")
                                                        auth_element.click()
                                                        auth_button_found = True
                                                        break
                                            except:
                                                pass

                                            auth_attempts += 1
                                            page.wait(1)

                                        if auth_button_found:
                                            print("已点击iframe中的GitHub授权按钮")

                                        # 切回主页面
                                        page.main_tab.switch.to()
                                        break
                        except:
                            continue
                except:
                    pass

        # 保持浏览器打开一段时间以便观察
        print("正在打开新标签页访问 https://ap-southeast-1.run.claw.cloud ...")

        # 打开新标签页并访问指定URL
        new_tab = page.new_tab(url="https://ap-southeast-1.run.claw.cloud")

        # 等待新页面加载
        new_tab.wait(3)

        # 检测是否已经登录（检查是否存在GitHub头像）
        print("正在检测GitHub头像...")
        avatar_elements = new_tab.eles('xpath://img[contains(@src, "avatars.githubusercontent.com")]')

        if avatar_elements:
            print("检测到已登录状态（找到GitHub头像），跳过登录步骤")
        else:
            print("未检测到登录状态，开始执行登录流程...")

            # 查找并点击GitHub登录按钮
            print("正在查找GitHub登录按钮...")
            github_button_xpath = '/html/body/div[1]/div/div/div[2]/div/div[3]/button[1]'

            github_button_found = False
            github_attempts = 0
            max_github_attempts = 10

            while not github_button_found and github_attempts < max_github_attempts:
                try:
                    github_button = new_tab.ele(f'xpath:{github_button_xpath}', timeout=0.5)
                    if github_button:
                        print("找到GitHub登录按钮，正在点击...")
                        github_button.click()
                        github_button_found = True
                        break
                except Exception as e:
                    print(f"查找GitHub登录按钮时出错: {str(e)}")

                if not github_button_found:
                    print(f"第 {github_attempts + 1} 次尝试未找到GitHub登录按钮，继续等待...")
                    new_tab.wait(1)
                    github_attempts += 1

            if not github_button_found:
                print("警告: 未找到GitHub登录按钮，请检查页面元素")
            else:
                print("已点击GitHub登录按钮，正在等待页面跳转...")

                # 等待页面跳转到GitHub授权页面
                page.wait(2)

                # 等待并点击GitHub授权按钮
                print("正在查找GitHub授权按钮...")
                auth_button_xpath = '/html/body/div[1]/div[4]/main/div/div[2]/form/div[3]/input'

                auth_button_found = False
                auth_attempts = 0
                max_auth_attempts = 10

                while not auth_button_found and auth_attempts < max_auth_attempts:
                    try:
                        auth_button = new_tab.ele(f'xpath:{auth_button_xpath}', timeout=0.5)

                        if auth_button:
                            # 获取按钮的文本或值属性
                            element_text = ""
                            try:
                                element_text = auth_button.text.lower()
                            except:
                                pass

                            # 尝试获取value属性（对于input元素）
                            try:
                                element_value = auth_button.attr('value')
                                if element_value:
                                    element_text = element_value.lower()
                            except:
                                pass

                            print(f"当前找到的按钮文本/值: {element_text}")

                            if 'sign in' in element_text or 'authorize' in element_text or '授权' in element_text:
                                print("找到匹配条件的GitHub授权按钮，正在点击...")
                                auth_button.click()
                                auth_button_found = True
                                break
                            else:
                                print("找到的元素不匹配所需文本，继续搜索...")
                    except Exception as e:
                        print(f"查找授权按钮时出错: {str(e)}")

                    if not auth_button_found:
                        print(f"第 {auth_attempts + 1} 次尝试未找到授权按钮，继续等待...")
                        new_tab.wait(1)
                        auth_attempts += 1

                if not auth_button_found:
                    print("警告: 未找到GitHub授权按钮，请手动完成授权")
                else:
                    print("已成功点击GitHub授权按钮")

        input("按回车键关闭浏览器...")

    except Exception as e:
        print(f"发生错误: {str(e)}")
    finally:
        # 关闭浏览器
        page.quit()

if __name__ == "__main__":
    login_to_claw_cloud()