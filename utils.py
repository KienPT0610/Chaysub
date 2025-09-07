import json
import asyncio

async def countdown(sec):
    while sec > 0:
        await asyncio.sleep(1)
        sec -= 1

def load_allowed_users():
  try:
    with open('users.json', 'r') as f:
      data = json.load(f)
      allowed_users = data.get("allowed_users", [])
      return [int(user["id"]) for user in allowed_users]
  except FileNotFoundError:
    return []


def getBalanceInfo(user_id: int) -> int:
    with open("users.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        for user in data["allowed_users"]:
            if str(user["id"]) == str(user_id):
                return int(user["balance"])
    return 0  # Trả về 0 nếu không tìm thấy

def addBalance(user_id: int, amount: int) -> bool:
    with open("users.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        for user in data["allowed_users"]:
            if str(user["id"]) == str(user_id):
                user["balance"] += amount
                with open("users.json", "w", encoding="utf-8") as fw:
                    json.dump(data, fw, ensure_ascii=False, indent=4)
                return True
    return False  # Trả về False nếu không tìm thấy người dùng

def add_allowed_user(user_id):
  users = load_allowed_users()
  if user_id not in users:
    users.append(user_id)
    with open('users.json', 'w') as f:
      json.dump({"allowed_users": users}, f)
    return True
  return False

def remove_allowed_user(user_id):
  users = load_allowed_users()
  if user_id in users:
    users.remove(user_id)
    with open('users.json', 'w') as f:
      json.dump({"allowed_users": users}, f)
    return True
  return False