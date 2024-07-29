import os
import asyncio
import vobject
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message

# Memuat variabel lingkungan dari file .env
load_dotenv()

# Konfigurasi bot dari environment variables
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')
owner_id = int(os.getenv('OWNER_ID'))

app = Client("bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Database untuk mengelola langganan
conn = sqlite3.connect('subscriptions.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (user_id INTEGER PRIMARY KEY, end_date TEXT)''')
conn.commit()

# Fungsi untuk memeriksa langganan
def check_subscription(user_id):
    c.execute('SELECT end_date FROM subscriptions WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    if result:
        end_date = datetime.fromisoformat(result[0])
        if datetime.now() <= end_date:
            return True
    return False

# Fungsi untuk menambahkan atau memperpanjang langganan
def add_subscription(user_id, days):
    end_date = datetime.now() + timedelta(days=days)
    c.execute('INSERT OR REPLACE INTO subscriptions (user_id, end_date) VALUES (?, ?, ?)', (user_id, end_date.isoformat()))
    conn.commit()

# Handler untuk mengkonversi file TXT atau Excel ke VCF
@app.on_message(filters.document & filters.private)
async def handle_document(client, message: Message):
    if not check_subscription(message.from_user.id):
        await message.reply("Langganan Anda telah habis. Silakan perbarui langganan Anda.")
        return

    file_path = await message.download()
    await asyncio.sleep(2)  # Simulasi waktu proses

    # Mengidentifikasi tipe file
    if file_path.endswith('.txt'):
        with open(file_path, 'r') as file:
            phone_numbers = [line.strip() for line in file.readlines()]
    elif file_path.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file_path)
        phone_numbers = df.iloc[:, 0].astype(str).tolist()
    else:
        await message.reply("Format file tidak didukung. Hanya mendukung file .txt dan .xls/.xlsx.")
        return

    vcf_path = file_path.rsplit('.', 1)[0] + '.vcf'
    with open(vcf_path, 'w') as vcf_file:
        for i, phone_number in enumerate(phone_numbers):
            vcard = vobject.vCard()
            vcard.add('fn').value = f"Contact {i+1}"
            vcard.add('tel').value = phone_number
            vcf_file.write(vcard.serialize())

    await message.reply_document(vcf_path)

# Handler untuk mengubah teks nomor telepon menjadi VCF
@app.on_message(filters.text & filters.private)
async def handle_text(client, message: Message):
    if not check_subscription(message.from_user.id):
        await message.reply("Langganan Anda telah habis. Silakan perbarui langganan Anda.")
        return

    # Format pesan: nama_file,nama_kontak1,nomor1,nama_kontak2,nomor2,...,kontak_per_file
    try:
        parts = message.text.split(',')
        file_name = parts[0]
        contact_numbers = parts[1:-1]
        contacts_per_file = int(parts[-1])
    except (IndexError, ValueError):
        await message.reply("Format tidak valid. Gunakan format: nama_file,nama_kontak1,nomor1,nama_kontak2,nomor2,...,kontak_per_file")
        return

    vcards = []
    for i in range(0, len(contact_numbers), 2):
        contact_name = contact_numbers[i]
        phone_number = contact_numbers[i + 1]
        vcard = vobject.vCard()
        vcard.add('fn').value = contact_name
        vcard.add('tel').value = phone_number
        vcards.append(vcard)

    # Membagi vCards menjadi beberapa file jika melebihi kontak_per_file
    for i in range(0, len(vcards), contacts_per_file):
        vcf_path = f'{file_name}_{i//contacts_per_file + 1}.vcf'
        with open(vcf_path, 'w') as f:
            for vcard in vcards[i:i + contacts_per_file]:
                f.write(vcard.serialize())
        await message.reply_document(vcf_path)

# Command untuk menambahkan langganan oleh owner
@app.on_message(filters.command("addsub") & filters.user(owner_id))
async def add_subscription_command(client, message: Message):
    try:
        user_id = int(message.command[1])
        days = int(message.command[2])
        add_subscription(user_id, days)
        await message.reply(f"Langganan untuk user {user_id} telah ditambahkan selama {days} hari.")
    except (IndexError, ValueError):
        await message.reply("Gunakan format: /addsub <user_id> <days>")

# Menjalankan bot
app.run()
