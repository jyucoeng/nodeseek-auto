#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import requests
from urllib.parse import urljoin
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nodeseek_debug.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 常量定义
BASE_URL = "https://www.nodeseek.com/"
SIGN_IN_URL = urljoin(BASE_URL, "api/signin")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

class NodeSeekSigner:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': BASE_URL
        })
        
    def safe_json_parse(self, response):
        """安全地解析JSON响应"""
        try:
            # 检查响应内容是否为空
            if not response.text or not response.text.strip():
                logger.error("收到空响应")
                return None
                
            # 检查状态码
            if response.status_code != 200:
                logger.error(f"HTTP错误: {response.status_code}, 响应内容: {response.text}")
                return None
                
            # 尝试解析JSON
            return response.json()
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            logger.error(f"响应内容: {response.text}")
            return None
        except Exception as e:
            logger.error(f"解析响应时发生未知错误: {e}")
            logger.error(f"响应内容: {response.text}")
            return None
    
    def sign_in_with_cookie(self, cookie):
        """使用Cookie进行签到"""
        logger.info("开始使用Cookie签到...")
        
        # 设置Cookie
        self.session.headers['Cookie'] = cookie
        
        # 添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"签到尝试 {attempt + 1}/{max_retries}")
                
                # 发送签到请求
                response = self.session.post(
                    SIGN_IN_URL,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                # 安全解析响应
                result = self.safe_json_parse(response)
                if result is not None:
                    return result
                    
                # 如果解析失败，等待后重试
                if attempt < max_retries - 1:
                    logger.info(f"签到失败，{2 ** attempt}秒后重试...")
                    time.sleep(2 ** attempt)  # 指数退避
                    
            except requests.RequestException as e:
                logger.error(f"网络请求错误: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"网络错误，{2 ** attempt}秒后重试...")
                    time.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"签到过程中发生未知错误: {e}")
                break
                
        return None
    
    def sign_in_with_credentials(self, username, password):
        """使用用户名密码签到（需要验证码服务）"""
        logger.info("开始使用用户名密码签到...")
        # 这里需要实现登录逻辑，包括验证码处理
        # 由于涉及复杂验证码处理，建议优先使用Cookie方式
        logger.warning("用户名密码登录需要验证码服务支持，建议使用Cookie方式签到")
        return None
    
    def check_sign_status(self, cookie):
        """检查签到状态"""
        logger.info("检查签到状态...")
        
        try:
            # 先访问主页检查登录状态
            response = self.session.get(BASE_URL, timeout=30)
            
            if response.status_code == 200:
                # 检查是否已登录（通过页面内容判断）
                if "登录" in response.text and "注册" in response.text:
                    logger.warning("Cookie可能已失效")
                    return False
                else:
                    logger.info("Cookie有效")
                    return True
            else:
                logger.error(f"检查登录状态失败，HTTP状态码: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"检查签到状态时出错: {e}")
            return False

def main():
    """主函数"""
    logger.info("NodeSeek自动签到脚本启动")
    
    # 初始化签到器
    signer = NodeSeekSigner()
    
    # 获取环境变量
    ns_cookie = os.environ.get('NS_COOKIE', '')
    username = os.environ.get('USER', '')
    password = os.environ.get('PASS', '')
    
    # 检查配置
    if not ns_cookie and not (username and password):
        logger.error("请设置NS_COOKIE环境变量或USER/PASS环境变量")
        sys.exit(1)
    
    # 处理多账号Cookie
    cookies = []
    if ns_cookie:
        # 支持 & 或换行符分隔的多账号
        if '&' in ns_cookie:
            cookies = ns_cookie.split('&')
        elif '\n' in ns_cookie:
            cookies = ns_cookie.split('\n')
        else:
            cookies = [ns_cookie]
    
    # 为每个账号签到
    success_count = 0
    for i, cookie in enumerate(cookies):
        if not cookie.strip():
            continue
            
        logger.info(f"处理账号 {i+1}/{len(cookies)}")
        
        # 检查Cookie有效性
        if not signer.check_sign_status(cookie):
            logger.warning(f"账号 {i+1} 的Cookie可能已失效")
            if username and password:
                logger.info("尝试使用用户名密码登录...")
                result = signer.sign_in_with_credentials(username, password)
                if result:
                    logger.info("登录成功")
                else:
                    logger.error("登录失败")
                    continue
            else:
                logger.error("未提供用户名密码，跳过此账号")
                continue
        
        # 执行签到
        result = signer.sign_in_with_cookie(cookie)
        if result:
            success_count += 1
            logger.info(f"账号 {i+1} 签到成功: {result}")
        else:
            logger.error(f"账号 {i+1} 签到失败")
    
    logger.info(f"签到完成，成功 {success_count}/{len(cookies)} 个账号")

if __name__ == "__main__":
    main()
