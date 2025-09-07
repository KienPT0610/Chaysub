import os
import json
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from chaysub import ChaySub
import time
from utils import load_allowed_users, add_allowed_user, countdown, remove_allowed_user, getBalanceInfo, addBalance

# load environment variables
load_dotenv()
TOKEN = os.getenv("BOT1_TOKEN")
CHAYSUB_TOKEN = os.getenv("CHAYSUB_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
# Initialize Class 
chaysub = ChaySub(CHAYSUB_TOKEN)

# ----- Bot Commands -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ALLOWED_USER = load_allowed_users()
    if update.effective_user.id not in ALLOWED_USER:
        await update.message.reply_text("Bạn không có quyền sử dụng bot này.")
        return

    keyboard = [
        [InlineKeyboardButton("🚀 Bắt đầu", callback_data='start')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Chào mừng! Nhấn nút bên dưới để bắt đầu.', reply_markup=reply_markup)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Bạn không có quyền sử dụng bot này.")
        return

    status, result = chaysub.getBalance()
    keyboard = [
        [InlineKeyboardButton("Thêm người dùng", callback_data='add_user')],
        [InlineKeyboardButton("Thêm số dư cho người dùng", callback_data='add_balance')],
        [InlineKeyboardButton("Xem người dùng", callback_data='view_users')],
        [InlineKeyboardButton("Xóa người dùng", callback_data='remove_user')],
        [InlineKeyboardButton("Quay lại", callback_data='start')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=f'Số dư: {result.get("balance", "NaN")} {result.get("currency", "VNĐ")}\nChọn chức năng bạn muốn:', reply_markup=reply_markup)

async def getId(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    await update.message.reply_text(f"ID của bạn là: {user_id}")

async def getService(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    status, result = chaysub.getServices()
    if status == 200:
        print(result)
        # services = result.get("data", [])
        # service_list = "\n".join([f"{svc['service']}: {svc['name']} - {svc['rate']} {svc['category']}" for svc in services])
        # await update.message.reply_text(f"Dịch vụ hiện có:\n{service_list}")
    else:
        await update.message.reply_text(f"Lỗi khi lấy dịch vụ: {result.get('message', 'Không xác định')}")

# Button handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == 'start':
      balance = getBalanceInfo(update.effective_user.id)
      keyboard = [
          [InlineKeyboardButton("Tiktok", callback_data='tiktok')],
          [InlineKeyboardButton("Facebook", callback_data='facebook')],
      ]
      reply_markup = InlineKeyboardMarkup(keyboard)
      await query.edit_message_text(
        text=f'Số dư: {balance} VNĐ\nChọn dịch vụ bạn muốn:',
        reply_markup=reply_markup
      )

    elif query.data == 'add_user':
      await query.edit_message_text(text='Vui lòng gửi ID người dùng mới dưới dạng tin nhắn:')
      context.user_data['waiting_for_user_id'] = True

    elif query.data == 'view_users':
        users = load_allowed_users()
        if not users:
            await query.edit_message_text(text="Chưa có người dùng nào được phép.")
            return
        user_list = "\n".join([f"{user_id} - {getBalanceInfo(user_id)} VNĐ" for user_id in users])
        await query.edit_message_text(text=f"Người dùng được phép:\n{user_list}")

    elif query.data == 'tiktok':
      keyboard = [
          [InlineKeyboardButton("Tăng view video", callback_data='tiktok_view')],
          [InlineKeyboardButton("Tăng follow", callback_data='tiktok_follow')],
          [InlineKeyboardButton("Tăng tim", callback_data='tiktok_heart')],
          [InlineKeyboardButton("Quay lại", callback_data='start')],
      ]
      reply_markup = InlineKeyboardMarkup(keyboard)
      await query.edit_message_text(text='Chọn dịch vụ Tiktok:', reply_markup=reply_markup)

    elif query.data == 'tiktok_view':
      services = chaysub.getListServiceByCategoryAndName("Tiktok Buff View", "view")
      if not services:
          await query.edit_message_text(text="Không tìm thấy dịch vụ Tiktok View.")
          return
      keyboard = []
      for service in services:
          service_id = service.get("service")
          # name = service.get("name")
          rate = service.get("rate")
          min = service.get("min")
          max = service.get("max")
          keyboard.append([InlineKeyboardButton(f"[{service_id}] (Min: {min}, Max: {max}) - {rate}đ", callback_data=f'tiktok_view_{service_id}')])
      keyboard.append([InlineKeyboardButton("Quay lại", callback_data='tiktok')])
      reply_markup = InlineKeyboardMarkup(keyboard)
      await query.edit_message_text(text='Chọn loại dịch vụ muốn buff!', reply_markup=reply_markup)

    elif query.data.startswith('tiktok_view_'):
      service_id = query.data.split('_')[-1]
      await query.edit_message_text(text='Vui lòng gửi link video TikTok bạn muốn buff dưới dạng tin nhắn:')
      context.user_data['waiting_for_link'] = True
      context.user_data['service_id'] = service_id

    elif query.data == 'tiktok_follow':
        services = chaysub.getListServiceByCategoryAndName("Tiktok Buff Sub", "follow")
        if not services:
            await query.edit_message_text(text="Không tìm thấy dịch vụ Tiktok Follow.")
            return
        keyboard = []
        for service in services:
            service_id = service.get("service")
            # name = service.get("name")
            rate = service.get("rate")
            min = service.get("min")
            max = service.get("max")
            keyboard.append([InlineKeyboardButton(f"[{service_id}] (Min: {min}, Max: {max}) - {rate}đ", callback_data=f'tiktok_follow_{service_id}')])
        keyboard.append([InlineKeyboardButton("Quay lại", callback_data='tiktok')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text='Chọn loại dịch vụ muốn buff!', reply_markup=reply_markup)

    elif query.data.startswith('tiktok_follow_'):
      service_id = query.data.split('_')[-1]
      await query.edit_message_text(text='Vui lòng gửi link profile TikTok bạn muốn buff dưới dạng tin nhắn:')
      context.user_data['waiting_for_link'] = True
      context.user_data['service_id'] = service_id

    elif query.data == 'tiktok_heart':
        services = chaysub.getListServiceByCategoryAndName("Tiktok Buff Like", "like")
        if not services:
            await query.edit_message_text(text="Không tìm thấy dịch vụ Tiktok Like.")
            return
        keyboard = []
        for service in services:
            service_id = service.get("service")
            # name = service.get("name")
            rate = service.get("rate")
            min = service.get("min")
            max = service.get("max")
            keyboard.append([InlineKeyboardButton(f"[{service_id}] (Min: {min}, Max: {max}) - {rate}đ", callback_data=f'tiktok_heart_{service_id}')])
        keyboard.append([InlineKeyboardButton("Quay lại", callback_data='tiktok')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text='Chọn loại dịch vụ muốn buff!', reply_markup=reply_markup)

    elif query.data.startswith('tiktok_heart_'):
      service_id = query.data.split('_')[-1]
      await query.edit_message_text(text='Vui lòng gửi link video TikTok bạn muốn buff dưới dạng tin nhắn:')
      context.user_data['waiting_for_link'] = True
      context.user_data['service_id'] = service_id

    elif query.data == 'facebook':
      await update.callback_query.message.reply_text("Chức năng này chưa hoàn thiện.")

    elif query.data == 'paid':
      object_id = context.user_data.get('object_id')
      quantity = context.user_data.get('quantity')
      if not object_id or not quantity:
          await query.edit_message_text(text="Lỗi: Thiếu thông tin đơn hàng.")
          return
      await query.edit_message_text(text="✅ Thanh toán thành công! Đang tạo đơn hàng...")
      await buff(update, context, object_id, quantity)

    elif query.data == 'cancel':
      await query.edit_message_text(text="❌ Đơn hàng đã bị hủy.")

    elif query.data == 'remove_user':
      users = load_allowed_users()
      if not users:
          await query.edit_message_text(text="Chưa có người dùng nào được phép.")
          return
      keyboard = []
      for user_id in users:
          keyboard.append([InlineKeyboardButton(f"Xóa {user_id}", callback_data=f'remove_{user_id}')])
      keyboard.append([InlineKeyboardButton("Quay lại", callback_data='admin')])
      reply_markup = InlineKeyboardMarkup(keyboard)
      await query.edit_message_text(text='Chọn người dùng bạn muốn xóa:', reply_markup=reply_markup)

    elif query.data.startswith('remove_'):
      user_id = int(query.data.split('_')[-1])
      if remove_allowed_user(user_id):
          await query.edit_message_text(text=f"✅ Đã xóa người dùng với ID: {user_id}")
      else:
          await query.edit_message_text(text=f"⚠️ Không tìm thấy người dùng với ID: {user_id}")

    elif query.data == 'add_balance':
      # lay danh sách user
      users = load_allowed_users()
      if not users:
          await query.edit_message_text(text="Chưa có người dùng nào được phép.")
          return
      keyboard = []
      for user_id in users:
          keyboard.append([InlineKeyboardButton(f"Nạp cho {user_id}", callback_data=f'addbal_{user_id}')])
      keyboard.append([InlineKeyboardButton("Quay lại", callback_data='admin')])
      reply_markup = InlineKeyboardMarkup(keyboard)
      await query.edit_message_text(text='Chọn người dùng bạn muốn nạp số dư:', reply_markup=reply_markup)

    elif query.data.startswith('addbal_'):
      user_id = int(query.data.split('_')[-1])
      await query.edit_message_text(text=f'Vui lòng gửi số tiền bạn muốn nạp cho người dùng {user_id} dưới dạng tin nhắn:')
      context.user_data['waiting_for_balance'] = True
      context.user_data['target_user_id'] = user_id

# Buff function
async def buff(update: Update, context: ContextTypes.DEFAULT_TYPE, object_id: str, quantity: int):
    message = update.message or update.callback_query.message
    service_id = context.user_data.get('service_id')
    if not service_id:
        await message.reply_text("Lỗi: ID dịch vụ không hợp lệ.")
        return

    await message.reply_text(f"Đang tạo đơn hàng cho link: {object_id} với số lượng: {quantity}")
    status, result = chaysub.create_order(service_id, object_id, quantity)
    if status == 200:
        order_id = result.get("order", "N/A")
        await message.reply_text(f"✅ Đơn hàng đã được tạo thành công! Mã đơn hàng: {order_id}")
    else:
        error_message = result.get("message", "Không xác định")
        await message.reply_text(f"❌ Lỗi khi tạo đơn hàng: {error_message}")

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Xác nhận", callback_data='paid')],
        [InlineKeyboardButton("Hủy", callback_data='cancel')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    service_id = context.user_data.get('service_id')
    object_id = context.user_data.get('object_id') 
    quantity = context.user_data.get('quantity')
    # get amount for service
    amount = chaysub.getServicePrice(service_id)
    if amount == 0:
        await update.message.reply_text("Lỗi: Không thể lấy giá dịch vụ.")
        return
    price = int(round(amount * quantity))
    balance = getBalanceInfo(update.effective_user.id)
    if balance < price:
        await update.message.reply_text(f"Số dư của bạn không đủ để thực hiện giao dịch này. Vui lòng nạp thêm tiền.\nSố dư hiện tại: {balance} VNĐ, Giá dịch vụ: {price} VNĐ")
        return
    view_order = f"Service: {service_id}\nLink: {object_id}\nSố lượng: {quantity}"
    await update.message.reply_text(f"Xác nhận {view_order}\nThanh toán {price} VNĐ để tiếp tục?", reply_markup=reply_markup)

# Handler
async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for_link'):
        object_id = update.message.text.strip() # get link from user
        # check valid link tiktok
        if "tiktok.com" not in object_id:
            await update.message.reply_text("Link không hợp lệ. Vui lòng gửi lại link TikTok hợp lệ:")
            return
        context.user_data['waiting_for_link'] = False
        context.user_data['object_id'] = object_id
        await update.message.reply_text("Vui lòng gửi số lượng bạn muốn buff:")
        context.user_data['waiting_for_quantity'] = True
    elif context.user_data.get('waiting_for_quantity'):
        try:
            quantity = int(update.message.text.strip())
            if quantity <= 0:
                raise ValueError("Số lượng phải là số nguyên dương.")
            object_id = context.user_data.get('object_id')
            if not object_id:
                await update.message.reply_text("Lỗi: Link không hợp lệ.")
                context.user_data['waiting_for_quantity'] = False
                return
            context.user_data['quantity'] = quantity
            # Proceed to payment confirmation
            await payment(update, context) 
            # await buff(update, context, object_id, quantity)
            context.user_data['waiting_for_quantity'] = False
        except ValueError:
            await update.message.reply_text("Số lượng không hợp lệ. Vui lòng gửi lại số lượng hợp lệ:")
    elif context.user_data.get('waiting_for_user_id'):
        try:
            new_user_id = int(update.message.text.strip())
            if new_user_id <= 0:
                raise ValueError("ID người dùng phải là số nguyên dương.")
            if add_allowed_user(new_user_id, 0):
                await update.message.reply_text(f"✅ Đã thêm người dùng với ID: {new_user_id}")
            else:
                await update.message.reply_text(f"⚠️ Người dùng với ID: {new_user_id} đã tồn tại.")
            context.user_data['waiting_for_user_id'] = False
        except ValueError:
            await update.message.reply_text("ID người dùng không hợp lệ. Vui lòng gửi lại ID hợp lệ:")
    elif context.user_data.get('waiting_for_balance'):
        try:
            amount = int(update.message.text.strip())
            if amount <= 0:
                raise ValueError("Số tiền phải là số nguyên dương.")
            target_user_id = context.user_data.get('target_user_id')
            status, result = chaysub.getBalance() # lay so du bot
            if int(result.get("balance", 0)) < int(amount): # so sanh voi so du bot
                await update.message.reply_text(f"Số dư của bot không đủ để nạp số tiền này. Vui lòng nạp thêm tiền vào bot.\nSố dư hiện tại của bot: {result.get('balance', 0)} VNĐ")
                context.user_data['waiting_for_balance'] = False
                return
            if not target_user_id:
                await update.message.reply_text("Lỗi: ID người dùng không hợp lệ.")
                context.user_data['waiting_for_balance'] = False
                return
            if addBalance(target_user_id, amount):
                await update.message.reply_text(f"✅ Đã nạp {amount} VNĐ cho người dùng với ID: {target_user_id}")
            else:
                await update.message.reply_text(f"⚠️ Không tìm thấy người dùng với ID: {target_user_id}.")
            context.user_data['waiting_for_balance'] = False
        except ValueError:
            await update.message.reply_text("Số tiền không hợp lệ. Vui lòng gửi lại số tiền hợp lệ:")
    else:
        await update.message.reply_text("Vui lòng nhấn /start để bắt đầu.")


# ----- Main -----   
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("getid", getId))
    app.add_handler(CommandHandler("getservice", getService))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))
    #run bot
    app.run_polling()

if __name__ == "__main__":
    main()
