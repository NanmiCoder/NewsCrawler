from typing import Dict, Optional
import requests
import re
import json


def extract_answer_json(html_content: str) -> dict | None:
    """提取回答的JSON数据，这个网站的数据渲染有点奇葩，导致正则太难写了，fuck!!!
    Args:
        html_content (str): 网页内容

    Returns:
        dict: 包含回答数据的JSON数据
    """
    pattern = r'push\(("{\\"data\\":{\\"answer\\":.*?}}\")\);'
    matches = re.finditer(pattern, html_content, re.DOTALL)
    for match in matches:
        json_str = match.group(1)
        try:
            answer_data = json.loads(json_str)
            answer_data = json.loads(answer_data)
            if (
                "data" in answer_data
                and "answer" in answer_data["data"]
                and "content" in answer_data["data"]["answer"]
            ):
                return answer_data
        except json.JSONDecodeError:
            continue
    return None


def get_answer_content(html_content):
    answer_json = extract_answer_json(html_content)
    if answer_json and "data" in answer_json:
        answer = answer_json["data"]["answer"]
        content = json.loads(answer["content"])
        del answer["content"]
        print(answer)
        return content
    return None


def main():
    # url = "https://www.quora.com/What-is-the-best-life-advice-you-would-give/answers/113244679"
    # url = "https://www.quora.com/Many-foreigners-make-fun-of-India-by-saying-India-is-dirty-and-Indians-are-unhygienic-Are-we-really-that-bad/answer/Abhinandan-59"
    url = "https://www.quora.com/Why-could-Mongolia-successfully-get-independence-from-China-but-Tibet-and-Xinjiang-failed-to-get-Independence-from-China/answer/Harry-Wonderer?ch=10&oid=1477743745038914&share=066b0c2e&srid=3yuN5t&target_type=answer"
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "max-age=0",
    }
    response = requests.get(url, headers=headers)
    content = get_answer_content(response.text)
    print(content)
    if content:
        # 提取所有文本内容
        for section in content["sections"]:
            if "spans" in section:
                for span in section["spans"]:
                    if "text" in span:
                        print(span["text"])


if __name__ == "__main__":
    main()
