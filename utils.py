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

def updateBalance(user_id: int, new_balance: int) -> bool:
    with open("users.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        for user in data["allowed_users"]:
            if str(user["id"]) == str(user_id):
                user["balance"] = new_balance
                with open("users.json", "w", encoding="utf-8") as fw:
                    json.dump(data, fw, ensure_ascii=False, indent=4)
                return True
    return False  # Trả về False nếu không tìm thấy người dùng

def save_allowed_users(users):
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump({"allowed_users": users}, f, ensure_ascii=False, indent=2)

def add_allowed_user(user_id: int, balance: int = 0) -> bool:
    users = load_allowed_users()
    
    # Nếu users là list chứa các int cũ, chuyển đổi hết về dạng dict
    updated_users = []
    for user in users:
        if isinstance(user, int):  # Dữ liệu kiểu cũ
            updated_users.append({"id": str(user), "balance": 0})
        elif isinstance(user, dict):
            updated_users.append(user)
    
    # Kiểm tra trùng lặp
    for user in updated_users:
        if str(user["id"]) == str(user_id):
            return False  # Đã tồn tại

    # Thêm người dùng mới
    updated_users.append({"id": str(user_id), "balance": balance})
    save_allowed_users(updated_users)
    return True

def remove_allowed_user(user_id: int) -> bool:
    # truy cập vào file users.json và sửa
    with open('users.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        users = data.get("allowed_users", [])
        updated_users = [user for user in users if str(user["id"]) != str(user_id)]
        if len(updated_users) == len(users):
            return False  # Không tìm thấy người dùng để xóa
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump({"allowed_users": updated_users}, f, ensure_ascii=False, indent=2)
    return True
