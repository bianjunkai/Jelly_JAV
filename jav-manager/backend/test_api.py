#!/usr/bin/env python3
"""
API 测试脚本
用于验证后端 API 是否正常工作
"""
import requests
import sys

BASE_URL = 'http://localhost:5000/api'

def test_endpoint(name, method, path, expected_status=200, json=None, params=None):
    """测试单个 API 端点"""
    url = f"{BASE_URL}{path}"
    try:
        if method == 'GET':
            resp = requests.get(url, params=params, timeout=5)
        elif method == 'POST':
            resp = requests.post(url, json=json, timeout=5)
        elif method == 'PUT':
            resp = requests.put(url, json=json, timeout=5)
        elif method == 'DELETE':
            resp = requests.delete(url, timeout=5)
        else:
            print(f"❌ {name}: Unknown method {method}")
            return False

        if resp.status_code == expected_status:
            print(f"✅ {name}: {method} {path} -> {resp.status_code}")
            return True
        else:
            print(f"❌ {name}: {method} {path} -> {resp.status_code} (expected {expected_status})")
            print(f"   Response: {resp.text[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"⚠️  {name}: {method} {path} -> Connection Error (is server running?)")
        return False
    except Exception as e:
        print(f"❌ {name}: {method} {path} -> Error: {e}")
        return False


def main():
    print("=" * 50)
    print("JAV Manager API Test")
    print("=" * 50)
    print()

    results = []

    # 统计
    print("[Statistics]")
    results.append(test_endpoint("Get Stats", "GET", "/stats"))

    # 影片
    print("\n[Movies]")
    results.append(test_endpoint("List Movies", "GET", "/movies", params={'page': 1, 'per_page': 10}))

    # 演员
    print("\n[Actors]")
    results.append(test_endpoint("List Actors", "GET", "/actors"))

    # 榜单
    print("\n[Charts]")
    results.append(test_endpoint("List Charts", "GET", "/charts"))
    results.append(test_endpoint("Chart Detail", "GET", "/charts/JavDB%20TOP250", params={'page': 1}))

    # 报告
    print("\n[Reports]")
    results.append(test_endpoint("Latest Reports", "GET", "/reports/latest"))
    results.append(test_endpoint("List Reports", "GET", "/reports"))

    # 待看
    print("\n[Todos]")
    results.append(test_endpoint("List Todos", "GET", "/todos"))

    # 任务
    print("\n[Tasks]")
    results.append(test_endpoint("Get Tasks", "GET", "/tasks"))

    # 打印结果
    print()
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
