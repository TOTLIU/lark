import json
import os
from typing import List, Tuple, Optional
import requests

class Recommender:
    def __init__(self):
        self.last_test_action: Optional[str] = None
        self.api_key = os.getenv("DOUBAO_API_KEY")
        self.api_url = "https://ark.cn-beijing.volcengineapi.com/api/v3/chat/completions"
        self.target_url = "https://aily.feishu.cn/ai/ailyplay/welcome"

    def _call_doubao_api(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "doubao-pro-32k",
            "messages": [
                {"role": "system", "content": "你是为 Web 程序生成 Playwright Python 测试用例的专家。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.7,
        }
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        except requests.RequestException as e:
            print(f"豆包 API 调用失败: {e}")
            return ""

    def recommend_test(self) -> Tuple[str, List[str]]:
        """根据上下文推荐测试用例和断言"""
        if self.last_test_action:
            prompt = (
                f"为该目标创建一个Playwright Python 测试用例 '{self.target_url}'"
                f"该测试需与先前的操作相关 '{self.last_test_action}' "
                f"例如先前的操作为收藏该对话，那么推荐的测试可以为测试收藏夹相关功能"
                f"至少包含一个断言来验证结果 (如 URL, 元素可见性, 或文本) "
                f"仅返回python代码 "
            )
        else:
            prompt = (
                f"为该目标创建一个Playwright Python 测试用例 '{self.target_url}' "
                f"常见的操作包括页面导航、登录或与模型聊天互动。如果没有特定的偏好，请优先考虑登录 "
                f"至少包含一个断言来验证结果 (如 URL, 元素可见性, 或文本) "
                f"仅返回python代码 "
            )
        
        test_code = self._call_doubao_api(prompt)
        if not test_code:
            return "", []

        assertions = [
            line.strip() for line in test_code.splitlines()
            if "expect(" in line and ")." in line
        ]

        for line in test_code.splitlines():
            if line.strip().startswith("def test_"):
                action = line.strip().replace("def test_", "").split("(")[0]
                self.last_test_action = action
                break
        
        return test_code.strip(), assertions

    def set_last_test(self, action: str):
        self.last_test_action = action

    def recommend_from_natural_language(self, input_text: str) -> Tuple[str, List[str]]:
        """从自然语言输入"""
        prompt = (
            f"为该目标创建一个Playwright Python 测试用例 '{self.target_url}'， "
            f"基于以下描述: '{input_text}' "
            f"至少包含一个断言来验证结果 (如 URL, 元素可见性, 或文本) "
            f"仅返回python代码 "
        )
        test_code = self._call_doubao_api(prompt)
        if not test_code:
            return "", []

        assertions = [
            line.strip() for line in test_code.splitlines()
            if "expect(" in line and ")." in line
        ]

        for line in test_code.splitlines():
            if line.strip().startswith("def test_"):
                action = line.strip().replace("def test_", "").split("(")[0]
                self.last_test_action = action
                break
        
        return test_code.strip(), assertions

def main():
    if not os.getenv("DOUBAO_API_KEY"):
        print("错误：请设置环境变量 DOUBAO_API_KEY")
        return
    
    recommender = Recommender()

    print("无先前操作")
    test_code, assertions = recommender.recommend_test()
    print("推荐的测试用例：")
    print(test_code if test_code else "无测试用例生成（API 失败）")
    print("\n推荐的断言：")
    print(json.dumps(assertions, indent=2, ensure_ascii=False))

    print("\n基于上一次测试动作推荐")
    recommender.set_last_test("chat_input")  # 示例动作，实际由 LLM 推断
    test_code, assertions = recommender.recommend_test()
    print("推荐的测试用例：")
    print(test_code if test_code else "无测试用例生成（API 失败）")
    print("\n推荐的断言：")
    print(json.dumps(assertions, indent=2, ensure_ascii=False))

    print("\n自然语言输入")
    test_code, assertions = recommender.recommend_from_natural_language(
        "测试用户可以在 Aily 平台输入聊天消息"
    )
    print("推荐的测试用例：")
    print(test_code if test_code else "无测试用例生成（API 失败）")
    print("\n推荐的断言：")
    print(json.dumps(assertions, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
    