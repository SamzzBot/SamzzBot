const TelegramBot = require('node-telegram-bot-api');
const fs = require('fs');

// Ganti dengan token bot Telegram Anda
const token = '7249788565:AAHZEEslPPykWAfkVtPNI9LJDfBzpc-Xyc8';
// Ganti dengan chat ID owner
const ownerChatId = '7365835326';

const bot = new TelegramBot(token, { polling: true });

const subscribers = new Set();
const fileNames = {};

bot.onText(/\/start/, (msg) => {
    const chatId = msg.chat.id;
    bot.sendMessage(chatId, 'Selamat datang! Anda dapat mengirim teks dengan format NAMA_KONTAK,NOMOR untuk diubah menjadi file VCF. Gunakan /filename [nama file] untuk mengatur nama file.');
});

bot.onText(/\/subscribe (.+)/, (msg, match) => {
    const chatId = msg.chat.id;
    if (chatId === ownerChatId) {
        const targetChatId = match[1].trim();
        subscribers.add(targetChatId);
        bot.sendMessage(chatId, `Pengguna ${targetChatId} telah berlangganan.`);
        bot.sendMessage(targetChatId, 'Anda telah berlangganan.');
    } else {
        bot.sendMessage(chatId, 'Hanya owner yang dapat mengatur langganan.');
    }
});

bot.onText(/\/unsubscribe (.+)/, (msg, match) => {
    const chatId = msg.chat.id;
    if (chatId === ownerChatId) {
        const targetChatId = match[1].trim();
        subscribers.delete(targetChatId);
        bot.sendMessage(chatId, `Pengguna ${targetChatId} telah berhenti berlangganan.`);
        bot.sendMessage(targetChatId, 'Anda telah berhenti berlangganan.');
    } else {
        bot.sendMessage(chatId, 'Hanya owner yang dapat mengatur langganan.');
    }
});

bot.onText(/\/filename (.+)/, (msg, match) => {
    const chatId = msg.chat.id;
    if (chatId === ownerChatId || subscribers.has(chatId)) {
        const fileName = match[1].trim();
        fileNames[chatId] = fileName;
        bot.sendMessage(chatId, `Nama file diatur ke: ${fileName}`);
    } else {
        bot.sendMessage(chatId, 'Anda harus berlangganan untuk menggunakan bot ini.');
    }
});

bot.on('message', (msg) => {
    const chatId = msg.chat.id;

    // Lewati jika pesan adalah perintah
    if (msg.text.startsWith('/')) {
        return;
    }

    if (chatId !== ownerChatId && !subscribers.has(chatId)) {
        bot.sendMessage(chatId, 'Anda harus berlangganan untuk menggunakan bot ini.');
        return;
    }

    const text = msg.text;
    const lines = text.split('\n');
    const contacts = lines.map(line => line.split(','));

    if (contacts.every(contact => contact.length === 2)) {
        const vcfContent = contacts.map(([name, number]) => 
            `BEGIN:VCARD
VERSION:3.0
FN:${name}
TEL;TYPE=CELL:${number}
END:VCARD`).join('\n');

        const fileName = fileNames[chatId] ? `${fileNames[chatId]}.vcf` : `contacts_${chatId}.vcf`;
        fs.writeFileSync(fileName, vcfContent);

        bot.sendDocument(chatId, fileName)
            .then(() => fs.unlinkSync(fileName))
            .catch(err => console.error(err));
    } else {
        bot.sendMessage(chatId, 'Format pesan tidak valid. Harap gunakan format: NAMA_KONTAK,NOMOR');
    }
});
