import os
import json
import asyncio
from aiohttp import web
import logging
from typing import List
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from chaysub import ChaySub
from utils import (
    load_allowed_users, add_allowed_user, countdown, remove_allowed_user,
    getBalanceInfo, addBalance, updateBalance
)

# ================== ENV & INIT ==================
load_dotenv()

TOKEN = os.getenv("BOT1_TOKEN")
CHAYSUB_TOKEN = os.getenv("CHAYSUB_TOKEN")
_admin_env = os.getenv("ADMIN_ID")
try:
    ADMIN_ID = int(_admin_env) if _admin_env else None
except ValueError:
    ADMIN_ID = None

if not TOKEN:
    raise RuntimeError("Thiếu BOT1_TOKEN trong .env")
if not CHAYSUB_TOKEN:
    raise RuntimeError("Thiếu CHAYSUB_TOKEN trong .env")
if ADMIN_ID is None:
    raise RuntimeError("Thiếu hoặc sai ADMIN_ID trong .env (phải là số nguyên)")

# logging & error handler
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

chaysub = ChaySub(CHAYSUB_TOKEN)


# ================== HELPERS ==================
def _is_allowed(user_id: int) -> bool:
    return user_id in load_allowed_users()

async def _guard_allow(update: Update) -> bool:
    uid = update.effective_user.id
    if not _is_allowed(uid):
        # nếu admin thì luôn cho qua
        if uid == ADMIN_ID:
            return True
        if update.effective_message:
            await update.effective_message.reply_text("Bạn không có quyền sử dụng bot này.")
        return False
    return True

async def _send_long_text(update_or_ctx, text: str):
    """Gửi text dài bằng cách cắt nhỏ tránh 4096 ký tự của Telegram."""
    # ưu tiên gửi qua message hiện có
    message = None
    if isinstance(update_or_ctx, Update):
        message = update_or_ctx.effective_message
    else:
        # context dùng trong một số trường hợp
        message = update_or_ctx

    MAX = 3900
    if len(text) <= MAX:
        await message.reply_text(text)
        return
    # chunk theo dòng
    lines = text.splitlines()
    buf, size = [], 0
    for ln in lines:
        if size + len(ln) + 1 > MAX:
            await message.reply_text("\n".join(buf))
            buf, size = [], 0
        buf.append(ln)
        size += len(ln) + 1
    if buf:
        await message.reply_text("\n".join(buf))

async def _show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.effective_message.reply_text("Bạn không có quyền sử dụng bot này.")
        return
    status, result = chaysub.getBalance()
    balance = result.get("balance", "NaN") if isinstance(result, dict) else "NaN"
    currency = result.get("currency", "VNĐ") if isinstance(result, dict) else "VNĐ"
    keyboard = [
        [InlineKeyboardButton("Thêm người dùng", callback_data='add_user')],
        [InlineKeyboardButton("Thêm số dư cho người dùng", callback_data='add_balance')],
        [InlineKeyboardButton("Xem người dùng", callback_data='view_users')],
        [InlineKeyboardButton("Xóa người dùng", callback_data='remove_user')],
        [InlineKeyboardButton("Quay lại", callback_data='start')],
    ]
    await update.effective_message.edit_text(
        text=f"Số dư: {balance} {currency}\nChọn chức năng bạn muốn:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================== COMMANDS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard_allow(update):
        return
    keyboard = [[InlineKeyboardButton("🚀 Bắt đầu", callback_data='start')]]
    await update.message.reply_text(
        'Chào mừng! Nhấn nút bên dưới để bắt đầu.',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Bạn không có quyền sử dụng bot này.")
        return
    # dùng chung trình bày menu admin
    # gửi 1 message rồi edit về sau để đồng nhất với callback
    status, result = chaysub.getBalance()
    balance = result.get("balance", "NaN") if isinstance(result, dict) else "NaN"
    currency = result.get("currency", "VNĐ") if isinstance(result, dict) else "VNĐ"
    keyboard = [
        [InlineKeyboardButton("Thêm người dùng", callback_data='add_user')],
        [InlineKeyboardButton("Thêm số dư cho người dùng", callback_data='add_balance')],
        [InlineKeyboardButton("Xem người dùng", callback_data='view_users')],
        [InlineKeyboardButton("Xóa người dùng", callback_data='remove_user')],
        [InlineKeyboardButton("Quay lại", callback_data='start')],
    ]
    await update.message.reply_text(
        text=f"Số dư: {balance} {currency}\nChọn chức năng bạn muốn:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def getId(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"ID của bạn là: {update.effective_user.id}")

async def getService(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _guard_allow(update):
        return
    status, result = chaysub.getServices()
    if status == 200 and isinstance(result, dict):
        services = result.get("data", [])
        if not services:
            await update.message.reply_text("Không có dịch vụ nào được trả về.")
            return
        # gói gọn thông tin quan trọng
        lines: List[str] = []
        for s in services:
            sid = s.get("service")
            name = s.get("name")
            rate = s.get("rate")
            cat  = s.get("category")
            minv = s.get("min")
            maxv = s.get("max")
            lines.append(f"[{sid}] {name} | {cat} | rate: {rate} | min:{minv} max:{maxv}")
        await _send_long_text(update, "Danh sách dịch vụ:\n" + "\n".join(lines))
    else:
        msg = result.get('message', 'Không xác định') if isinstance(result, dict) else 'Không xác định'
        await update.message.reply_text(f"Lỗi khi lấy dịch vụ: {msg}")


# ================== CALLBACKS ==================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    # guard quyền cho mọi callback (trừ admin – có check riêng)
    if query.data != 'admin' and not _is_allowed(update.effective_user.id) and update.effective_user.id != ADMIN_ID:
        await query.edit_message_text("Bạn không có quyền sử dụng bot này.")
        return

    if query.data == 'start':
        balance = getBalanceInfo(int(update.effective_user.id))
        keyboard = [
            [InlineKeyboardButton("Tiktok", callback_data='tiktok')],
            [InlineKeyboardButton("Facebook", callback_data='facebook')],
        ]
        await query.edit_message_text(
            text=f'Số dư: {balance} VNĐ\nChọn dịch vụ bạn muốn:',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == 'admin':
        # quay lại menu admin (có check quyền)
        await _show_admin_menu(update, context)

    elif query.data == 'add_user':
        if update.effective_user.id != ADMIN_ID:
            await query.edit_message_text("Bạn không có quyền sử dụng bot này.")
            return
        await query.edit_message_text(text='Vui lòng gửi ID người dùng mới dưới dạng tin nhắn:')
        context.user_data['waiting_for_user_id'] = True

    elif query.data == 'view_users':
        if update.effective_user.id != ADMIN_ID:
            await query.edit_message_text("Bạn không có quyền sử dụng bot này.")
            return
        users = load_allowed_users()
        if not users:
            await query.edit_message_text(text="Chưa có người dùng nào được phép.")
            return
        user_list = "\n".join([f"{uid} - {getBalanceInfo(uid)} VNĐ" for uid in users])
        await query.edit_message_text(text=f"Người dùng được phép:\n{user_list}")

    elif query.data == 'tiktok':
        keyboard = [
            [InlineKeyboardButton("Tăng view video", callback_data='tiktok_view')],
            [InlineKeyboardButton("Tăng follow", callback_data='tiktok_follow')],
            [InlineKeyboardButton("Tăng tim", callback_data='tiktok_heart')],
            [InlineKeyboardButton("Quay lại", callback_data='start')],
        ]
        await query.edit_message_text(text='Chọn dịch vụ Tiktok:', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'tiktok_view':
        services = chaysub.getListServiceByCategoryAndName("Tiktok Buff View", "view")
        if not services:
            await query.edit_message_text(text="Không tìm thấy dịch vụ Tiktok View.")
            return
        keyboard = []
        for service in services:
            service_id = service.get("service")
            rate = service.get("rate")
            minv = service.get("min")
            maxv = service.get("max")
            keyboard.append([InlineKeyboardButton(f"[{service_id}] (Min:{minv}, Max:{maxv}) - {rate}đ", callback_data=f'tiktok_view_{service_id}')])
        keyboard.append([InlineKeyboardButton("Quay lại", callback_data='tiktok')])
        await query.edit_message_text(text='Chọn loại dịch vụ muốn buff!', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('tiktok_view_'):
        service_id = query.data.split('_')[-1]
        await query.edit_message_text(text='Vui lòng gửi danh sách link video TikTok bạn muốn buff (mỗi link 1 dòng):')
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
            rate = service.get("rate")
            minv = service.get("min")
            maxv = service.get("max")
            keyboard.append([InlineKeyboardButton(f"[{service_id}] (Min:{minv}, Max:{maxv}) - {rate}đ", callback_data=f'tiktok_follow_{service_id}')])
        keyboard.append([InlineKeyboardButton("Quay lại", callback_data='tiktok')])
        await query.edit_message_text(text='Chọn loại dịch vụ muốn buff!', reply_markup=InlineKeyboardMarkup(keyboard))

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
            rate = service.get("rate")
            minv = service.get("min")
            maxv = service.get("max")
            keyboard.append([InlineKeyboardButton(f"[{service_id}] (Min:{minv}, Max:{maxv}) - {rate}đ", callback_data=f'tiktok_heart_{service_id}')])
        keyboard.append([InlineKeyboardButton("Quay lại", callback_data='tiktok')])
        await query.edit_message_text(text='Chọn loại dịch vụ muốn buff!', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('tiktok_heart_'):
        service_id = query.data.split('_')[-1]
        await query.edit_message_text(text='Vui lòng gửi link video TikTok bạn muốn buff dưới dạng tin nhắn:')
        context.user_data['waiting_for_link'] = True
        context.user_data['service_id'] = service_id

    elif query.data == 'facebook':
        await query.edit_message_text("Chức năng này chưa hoàn thiện.")

    elif query.data == 'paid':
        object_id = context.user_data.get('object_id')
        quantity = context.user_data.get('quantity')
        if not object_id or not quantity:
            await query.edit_message_text(text="Lỗi: Thiếu thông tin đơn hàng.")
            return
        await query.edit_message_text(text="✅ Thanh toán thành công! Đang tạo đơn hàng...")
        # chỉ update khi đã có new_balance
        if 'new_balance' in context.user_data:
            updateBalance(update.effective_user.id, context.user_data.get('new_balance', 0))
        await buff(update, context, object_id, int(quantity))

    elif query.data == 'cancel':
        await query.edit_message_text(text="❌ Đơn hàng đã bị hủy.")

    elif query.data == 'remove_user':
        if update.effective_user.id != ADMIN_ID:
            await query.edit_message_text("Bạn không có quyền sử dụng bot này.")
            return
        users = load_allowed_users()
        if not users:
            await query.edit_message_text(text="Chưa có người dùng nào được phép.")
            return
        keyboard = [[InlineKeyboardButton(f"Xóa {uid}", callback_data=f'remove_{uid}')] for uid in users]
        keyboard.append([InlineKeyboardButton("Quay lại", callback_data='admin')])
        await query.edit_message_text(text='Chọn người dùng bạn muốn xóa:', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('remove_'):
        if update.effective_user.id != ADMIN_ID:
            await query.edit_message_text("Bạn không có quyền sử dụng bot này.")
            return
        user_id = int(query.data.split('_')[-1])
        if remove_allowed_user(user_id):
            await query.edit_message_text(text=f"✅ Đã xóa người dùng với ID: {user_id}")
        else:
            await query.edit_message_text(text=f"⚠️ Không tìm thấy người dùng với ID: {user_id}")

    elif query.data == 'add_balance':
        if update.effective_user.id != ADMIN_ID:
            await query.edit_message_text("Bạn không có quyền sử dụng bot này.")
            return
        users = load_allowed_users()
        if not users:
            await query.edit_message_text(text="Chưa có người dùng nào được phép.")
            return
        keyboard = [[InlineKeyboardButton(f"Nạp cho {uid}", callback_data=f'addbal_{uid}')] for uid in users]
        keyboard.append([InlineKeyboardButton("Quay lại", callback_data='admin')])
        await query.edit_message_text(text='Chọn người dùng bạn muốn nạp số dư:', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('addbal_'):
        if update.effective_user.id != ADMIN_ID:
            await query.edit_message_text("Bạn không có quyền sử dụng bot này.")
            return
        user_id = int(query.data.split('_')[-1])
        await query.edit_message_text(text=f'Vui lòng gửi số tiền bạn muốn nạp cho người dùng {user_id} dưới dạng tin nhắn:')
        context.user_data['waiting_for_balance'] = True
        context.user_data['target_user_id'] = user_id


# ================== BUFF & PAYMENT ==================
async def buff(update: Update, context: ContextTypes.DEFAULT_TYPE, object_id: str, quantity: int):
    message = update.message or (update.callback_query.message if update.callback_query else None)
    if not message:
        return
    service_id = context.user_data.get('service_id')
    if not service_id:
        await message.reply_text("Lỗi: ID dịch vụ không hợp lệ.")
        return

    status, result = chaysub.create_order(service_id, object_id, quantity)
    if status == 200:
        order_id = result.get("order", "N/A") if isinstance(result, dict) else "N/A"
        await message.reply_text(f"✅ Đơn hàng đã được tạo thành công! Mã đơn hàng: {order_id}")
    else:
        error_message = result.get("message", "Không xác định") if isinstance(result, dict) else "Không xác định"
        await message.reply_text(f"❌ Lỗi khi tạo đơn hàng: {error_message}")

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _guard_allow(update):
        return
    keyboard = [
        [InlineKeyboardButton("Xác nhận", callback_data='paid')],
        [InlineKeyboardButton("Hủy", callback_data='cancel')],
    ]
    service_id = context.user_data.get('service_id')
    object_id = context.user_data.get('object_id')
    quantity = context.user_data.get('quantity')
    amount = chaysub.getServicePrice(service_id)
    if not amount:
        await update.message.reply_text("Lỗi: Không thể lấy giá dịch vụ.")
        return
    price = int(round(amount * int(quantity)))
    balance = getBalanceInfo(update.effective_user.id)
    if balance < price:
        await update.message.reply_text(
            f"Số dư của bạn không đủ. Số dư hiện tại: {balance} VNĐ, Giá dịch vụ: {price} VNĐ"
        )
        return
    context.user_data['new_balance'] = balance - price
    view_order = f"Service: {service_id}\nLink: {object_id}\nSố lượng: {quantity}"
    await update.message.reply_text(
        f"Xác nhận {view_order}\nThanh toán {price} VNĐ để tiếp tục?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def payment2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _guard_allow(update):
        return
    service_id = context.user_data.get('service_id')
    object_id = context.user_data.get('object_id')
    quantity = context.user_data.get('quantity')
    amount = chaysub.getServicePrice(service_id)
    if not amount:
        await update.message.reply_text("Lỗi: Không thể lấy giá dịch vụ.")
        return
    price = int(round(amount * int(quantity)))
    balance = getBalanceInfo(update.effective_user.id)
    if balance < price:
        await update.message.reply_text(
            f"Số dư của bạn không đủ. Số dư hiện tại: {balance} VNĐ, Giá dịch vụ: {price} VNĐ"
        )
        return
    context.user_data['new_balance'] = balance - price
    await update.message.reply_text(f"Thanh toán thành công {price} VNĐ cho đơn hàng:\nService: {service_id}\nLink: {object_id}\nSố lượng: {quantity}")
    updateBalance(update.effective_user.id, context.user_data.get('new_balance', balance))
    await buff(update, context, object_id, int(quantity))


# ================== USER INPUT ==================
async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _guard_allow(update):
        return

    if context.user_data.get('waiting_for_link'):
        object_ids = [ln.strip() for ln in update.message.text.strip().splitlines() if ln.strip()]
        if not object_ids:
            await update.message.reply_text("Link không hợp lệ. Vui lòng gửi lại danh sách link TikTok hợp lệ:")
            return
        if not all(("tiktok.com" in obj) for obj in object_ids):
            await update.message.reply_text("Link không hợp lệ. Vui lòng gửi lại danh sách link TikTok hợp lệ:")
            return
        context.user_data['waiting_for_link'] = False
        context.user_data['object_ids'] = object_ids
        await update.message.reply_text("Vui lòng gửi số lượng bạn muốn buff:")
        context.user_data['waiting_for_quantity'] = True

    elif context.user_data.get('waiting_for_quantity'):
        try:
            quantity = int(update.message.text.strip())
            if quantity <= 0:
                raise ValueError("Số lượng phải là số nguyên dương.")
            object_ids = context.user_data.get('object_ids')
            if not object_ids:
                await update.message.reply_text("Lỗi: Link không hợp lệ.")
                context.user_data['waiting_for_quantity'] = False
                return
            context.user_data['quantity'] = quantity
            # Thanh toán + tạo đơn cho từng link
            for object_id in object_ids:
                context.user_data['object_id'] = object_id
                await payment2(update, context)
                await asyncio.sleep(5)  # delay 5 giây giữa các đơn hàng
            context.user_data['waiting_for_quantity'] = False
        except ValueError:
            await update.message.reply_text("Số lượng không hợp lệ. Vui lòng gửi lại số lượng hợp lệ:")

    elif context.user_data.get('waiting_for_user_id'):
        try:
            new_user_id = int(update.message.text.strip())
            if new_user_id <= 0:
                raise ValueError
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
                raise ValueError
            target_user_id = context.user_data.get('target_user_id')
            if not target_user_id:
                await update.message.reply_text("Lỗi: ID người dùng không hợp lệ.")
                context.user_data['waiting_for_balance'] = False
                return
            # kiểm tra số dư bot trước khi nạp
            status, result = chaysub.getBalance()
            bot_balance = int(result.get("balance", 0)) if isinstance(result, dict) else 0
            if bot_balance < amount:
                await update.message.reply_text(
                    f"Số dư của bot không đủ để nạp số tiền này.\nSố dư hiện tại của bot: {bot_balance} VNĐ"
                )
                context.user_data['waiting_for_balance'] = False
                return
            if addBalance(target_user_id, amount):
                await update.message.reply_text(f"✅ Đã nạp {amount} VNĐ cho người dùng ID: {target_user_id}")
            else:
                await update.message.reply_text(f"⚠️ Không tìm thấy người dùng với ID: {target_user_id}.")
            context.user_data['waiting_for_balance'] = False
        except ValueError:
            await update.message.reply_text("Số tiền không hợp lệ. Vui lòng gửi lại số tiền hợp lệ:")

    else:
        await update.message.reply_text("Vui lòng nhấn /start để bắt đầu.")


# ================== ERROR HANDLER ==================
async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.exception("Exception while handling an update", exc_info=context.error)
    try:
        if update and hasattr(update, "effective_message") and update.effective_message:
            await update.effective_message.reply_text("❌ Có lỗi xảy ra. Mình đã ghi log để kiểm tra.")
    except Exception:
        pass


# ================== MAIN ==================
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("getid", getId))
    app.add_handler(CommandHandler("getservice", getService))

    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))

    app.add_error_handler(on_error)
    # Long-polling (Render → nên chạy kiểu Worker). Nếu bạn dùng Web Service, hãy chuyển qua webhook.
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
