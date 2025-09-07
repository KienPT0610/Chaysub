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
      return data.get("allowed_users", [])
  except FileNotFoundError:
    return []
  
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