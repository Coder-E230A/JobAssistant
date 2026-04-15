"""
BOSS直聘爬虫模块
"""
import asyncio
import os
import json
import random
from typing import Optional, List, Dict
from pathlib import Path

from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from app.config import settings


class BossCrawler:
    """BOSS直聘爬虫"""

    BASE_URL = "https://www.zhipin.com"

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.qrcode_path: Optional[str] = None
        self._playwright = None

    async def _init_browser(self):
        """初始化浏览器"""
        if not self.browser:
            self._playwright = await async_playwright().start()
            self.browser = await self._playwright.chromium.launch(
                headless=settings.PLAYWRIGHT_HEADLESS
            )
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()

    async def get_qrcode(self) -> Optional[str]:
        """获取登录二维码"""
        await self._init_browser()

        # 访问登录页面
        await self.page.goto(f"{self.BASE_URL}/web/user/?ka=header-login")

        # 等待二维码出现
        await self.page.wait_for_selector(".login-scan-wrapper", timeout=10000)

        # 截取二维码图片
        qrcode_element = await self.page.query_selector(".login-scan-wrapper img")
        if qrcode_element:
            # 保存二维码图片
            self.qrcode_path = os.path.join(settings.UPLOAD_DIR, "qrcode.png")
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            await qrcode_element.screenshot(path=self.qrcode_path)
            return self.qrcode_path

        return None

    async def check_login(self) -> bool:
        """检查是否已登录"""
        if not self.page:
            return False

        try:
            # 检查是否跳转到首页或显示用户信息
            await asyncio.sleep(2)

            # 检查登录成功标志
            user_element = await self.page.query_selector(".nav-figure")
            if user_element:
                return True

            # 或者检查 URL 变化
            current_url = self.page.url
            if "web/user" not in current_url and "zhipin.com" in current_url:
                return True

            return False
        except Exception:
            return False

    async def get_cookies(self) -> str:
        """获取登录后的 Cookie"""
        if not self.context:
            return ""

        cookies = await self.context.cookies()
        return json.dumps(cookies)

    async def load_cookies(self, cookies_str: str):
        """加载保存的 Cookie"""
        await self._init_browser()

        if cookies_str:
            cookies = json.loads(cookies_str)
            await self.context.add_cookies(cookies)

        await self.page.goto(self.BASE_URL)

    async def search_jobs(
        self,
        keywords: str,
        location: Optional[str] = None,
        salary_min: Optional[int] = None,
        salary_max: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict]:
        """搜索岗位"""
        await self._init_browser()

        if not self.page:
            await self.page.goto(self.BASE_URL)

        # 构建搜索 URL
        search_url = f"{self.BASE_URL}/web/geek/job?query={keywords}"

        # 添加城市参数
        if location:
            # BOSS直聘城市编码映射（简化版）
            city_codes = {
                "北京": "101010100",
                "上海": "101020100",
                "广州": "101280100",
                "深圳": "101280600",
                "杭州": "101210100",
                "成都": "101270100",
                "南京": "101190100",
                "武汉": "101200100",
                "西安": "101110100",
                "苏州": "101190400",
            }
            city_code = city_codes.get(location, "101010100")
            search_url += f"&city={city_code}"

        # 添加薪资参数
        if salary_min and salary_max:
            # BOSS薪资编码
            salary_map = {
                (0, 5): "101",
                (5, 10): "102",
                (10, 15): "103",
                (15, 20): "104",
                (20, 25): "105",
                (25, 30): "106",
                (30, 50): "107",
                (50, 100): "108",
            }
            for (min_k, max_k), code in salary_map.items():
                if salary_min >= min_k and salary_max <= max_k:
                    search_url += f"&salary={code}"
                    break

        await self.page.goto(search_url)

        # 等待岗位列表加载
        await self.page.wait_for_selector(".job-list-box", timeout=15000)

        # 模拟滚动加载更多
        for _ in range(3):
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)

        # 解析岗位列表
        jobs = []
        job_elements = await self.page.query_selector_all(".job-card-wrapper")

        for i, job_el in enumerate(job_elements[:limit]):
            try:
                job_data = await self._parse_job_element(job_el)
                jobs.append(job_data)

                # 添加随机延迟
                if i < limit - 1:
                    delay = random.uniform(0.5, 1.5)
                    await asyncio.sleep(delay)
            except Exception as e:
                print(f"解析岗位失败: {e}")
                continue

        return jobs

    async def _parse_job_element(self, job_el) -> Dict:
        """解析单个岗位元素"""
        # 获取岗位标题
        title_el = await job_el.query_selector(".job-name")
        title = await title_el.inner_text() if title_el else ""

        # 获取公司名称
        company_el = await job_el.query_selector(".company-name")
        company = await company_el.inner_text() if company_el else ""

        # 获取薪资
        salary_el = await job_el.query_selector(".salary")
        salary_text = await salary_el.inner_text() if salary_el else ""
        salary_min, salary_max = self._parse_salary(salary_text)

        # 获取地点
        location_el = await job_el.query_selector(".job-area")
        location = await location_el.inner_text() if location_el else ""

        # 获取岗位 ID
        job_link = await job_el.query_selector("a.job-card-left")
        job_url = await job_link.get_attribute("href") if job_link else ""
        job_id = job_url.split("/")[-1].split(".")[0] if job_url else ""

        # 获取 JD 内容（需要点击进入详情页）
        jd_content = ""
        try:
            if job_link:
                await job_link.click()
                await asyncio.sleep(1)

                detail_el = await self.page.query_selector(".job-detail-section")
                if detail_el:
                    jd_content = await detail_el.inner_text()

                # 返回列表页
                await self.page.goBack()
                await asyncio.sleep(0.5)
        except Exception:
            pass

        return {
            "job_id": job_id,
            "title": title.strip(),
            "company": company.strip(),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_text": salary_text.strip(),
            "location": location.strip(),
            "jd_content": jd_content.strip(),
            "url": f"{self.BASE_URL}/web/geek/job-detail/{job_id}.html"
        }

    def _parse_salary(self, salary_text: str) -> tuple[int, int]:
        """解析薪资文本"""
        import re

        # 匹配 "10-20K" 格式
        match = re.search(r"(\d+)-(\d+)K", salary_text, re.IGNORECASE)
        if match:
            return int(match.group(1)), int(match.group(2))

        # 匹配 "10K以上" 格式
        match = re.search(r"(\d+)K以上", salary_text, re.IGNORECASE)
        if match:
            return int(match.group(1)), 999

        return 0, 0

    async def apply_job(self, job_id: str) -> bool:
        """投递岗位"""
        if not self.page:
            return False

        try:
            # 访问岗位详情页
            await self.page.goto(f"{self.BASE_URL}/web/geek/job-detail/{job_id}.html")
            await self.page.wait_for_selector(".job-detail-footer", timeout=10000)

            # 查找投递按钮
            apply_btn = await self.page.query_selector(".btn-apply")
            if not apply_btn:
                # 可能已经投递过了
                return False

            # 点击投递
            await apply_btn.click()

            # 等待投递结果
            await asyncio.sleep(2)

            # 检查是否投递成功
            success_indicator = await self.page.query_selector(".btn-applied")
            return success_indicator is not None

        except Exception as e:
            print(f"投递失败: {e}")
            return False

    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None