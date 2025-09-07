import os
import time
import requests
from colorama import init, Fore

init(autoreset=True)

class ChaySub:
  # constructor
  def __init__(self, api_token, server_id="34225"):
    self.api_token = api_token
    self.server_id = server_id
    self.API_URL = "https://chaysub.vn/api/v2"
    self.total_view = 0
    self.success_count = 0
    self.fail_count = 0

  # def create_order(self, object_id):
  #   headers = {
  #     "Authorization": f"Bearer {self.api_token}",
  #     "User-Agent": "Mozilla/5.0",
  #     "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
  #     "Accept": "application/json, text/javascript, */*; q=0.01",
  #     "X-Requested-With": "XMLHttpRequest",
  #     "Origin": "https://chaysub.vn",
  #     "Referer": "https://chaysub.vn/service/free/free"
  #   }

  #   quantity = 100 
  #   if self.server_id == "34225":
  #       quantity = 500

  #   data = {
  #     "object_id": object_id,
  #     "provider_server": self.server_id,
  #     "quantity": str(quantity),
  #     "schedule_date": "",
  #     "schedule_time": "",
  #     "repeat_interval": "1",
  #     "repeat_delay": "0",
  #     "note": ""
  #   }

  #   try:
  #     resp = requests.post(f"{self.API_URL}/order", headers=headers, data=data, timeout=30)
  #     return resp.status_code, resp.json()
  #   except Exception as e:
  #     return 500, {"status": "error", "message": str(e)}

  def create_order(self, service_id, link, quantity):
    data = {
        "key": self.api_token,
        "action": "add",
        "service": service_id,
        "link": link,
        "quantity": quantity
    }

    try:
        response = requests.post(self.API_URL, data=data, timeout=30)
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"message": str(e)}  
    
  def getBalance(self):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "key": self.api_token,
        "action": "balance"
    }

    try:
        resp = requests.post(self.API_URL, headers=headers, data=data, timeout=30)
        return resp.status_code, resp.json()
    except Exception as e:
        return 500, {"status": "error", "message": str(e)}
    
  def getServices(self):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "key": self.api_token,
        "action": "services"
    }

    try:
        resp = requests.post(self.API_URL, headers=headers, data=data, timeout=30)
        return resp.status_code, resp.json()
    except Exception as e:
        return 500, {"status": "error", "message": str(e)}
    
  def getListServiceByCategoryAndName(self, category, name):
    status_code, services = self.getServices()
    if status_code == 200 and isinstance(services, list):
        filtered_services = [
            service for service in services
            if service.get("category", "").lower() == category.lower()
            and name.lower() in service.get("name", "").lower()
        ]
        print(Fore.GREEN + f"[INFO] Found {len(filtered_services)} services in category '{category}' with name containing '{name}'.")
        return sorted(filtered_services, key=lambda x: x.get("rate", 0))
    return []
  
    
  def getServicePrice(self, service_id): 
    status_code, services = self.getServices()
    if status_code == 200 and isinstance(services, list):
        for service in services:
            if str(service.get("service")) == str(service_id):
                return float(service.get("rate", 0))
    return 0