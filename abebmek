const TelegramBot = require('node-telegram-bot-api');
const fs = require('fs');
const path = require('path');
const xlsx = require('xlsx');

// Masukkan token bot Anda di sini
const token = '7249788565:AAHZEEslPPykWAfkVtPNI9LJDfBzpc-Xyc8';
const ownerId = 7365835326; // Ganti dengan ID Telegram Anda
const bot = new TelegramBot(token, { polling: true });

const subscriptions = {};

bot.onText(/\/start/, (msg) => {
    bot.sendMessage(msg.chat.id, "Selamat datang! Kirimkan file TXT atau Excel yang berisi nomor telepon untuk dikonversi ke VCF.");
});

bot.on('message', (msg) => {
    if (msg.document) {
        const fileId = msg.document.file_id;
        const chatId = msg.chat.id;
        const fileName = msg.document.file_name;
        
        bot.downloadFile(fileId, './')
            .then(filePath => {
                if (fileName.endsWith('.txt')) {
                    convertTxtToVcf(filePath, chatId, fileName);
                } else if (fileName.endsWith('.xlsx')) {
                    convertXlsxToVcf(filePath, chatId, fileName);
                } else {
                    bot.sendMessage(chatId, "Format file tidak didukung. Silakan kirim file TXT atau Excel.");
                }
            })
            .catch(error => {
                bot.sendMessage(chatId, "Terjadi kesalahan saat mengunduh file.");
                console.error(error);
            });
    }
});

function convertTxtToVcf(filePath, chatId, originalFileName) {
    fs.readFile(filePath, 'utf8', (err, data) => {
        if (err) {
            bot.sendMessage(chatId, "Terjadi kesalahan saat membaca file.");
            console.error(err);
            return;
        }
        const lines = data.split('\n').filter(line => line.trim());
        const vcfData = lines.map((line, index) => createVcfContact(line, `Contact ${index + 1}`)).join('\n');
        const vcfFileName = originalFileName.replace('.txt', '.vcf');
        const vcfFilePath = path.join(__dirname, vcfFileName);
        
        fs.writeFile(vcfFilePath, vcfData, err => {
            if (err) {
                bot.sendMessage(chatId, "Terjadi kesalahan saat menulis file VCF.");
                console.error(err);
                return;
            }
            bot.sendDocument(chatId, vcfFilePath);
        });
    });
}

function convertXlsxToVcf(filePath, chatId, originalFileName) {
    const workbook = xlsx.readFile(filePath);
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    const jsonData = xlsx.utils.sheet_to_json(worksheet);
    const vcfData = jsonData.map((row, index) => createVcfContact(row['Phone'], `Contact ${index + 1}`)).join('\n');
    const vcfFileName = originalFileName.replace('.xlsx', '.vcf');
    const vcfFilePath = path.join(__dirname, vcfFileName);
    
    fs.writeFile(vcfFilePath, vcfData, err => {
        if (err) {
            bot.sendMessage(chatId, "Terjadi kesalahan saat menulis file VCF.");
            console.error(err);
            return;
        }
        bot.sendDocument(chatId, vcfFilePath);
    });
}

function createVcfContact(phoneNumber, contactName) {
    return `BEGIN:VCARD\nVERSION:3.0\nFN:${contactName}\nTEL:${phoneNumber}\nEND:VCARD`;
}

bot.onText(/\/subscribe (\d+)/, (msg, match) => {
    const chatId = msg.chat.id;
    const duration = parseInt(match[1]);
    const expirationDate = new Date();
    expirationDate.setDate(expirationDate.getDate() + duration);
    subscriptions[chatId] = expirationDate;
    bot.sendMessage(chatId, `Anda telah berlangganan selama ${duration} hari.`);
});

bot.onText(/\/unsubscribe/, (msg) => {
    const chatId = msg.chat.id;
    if (subscriptions[chatId]) {
        delete subscriptions[chatId];
        bot.sendMessage(chatId, "Langganan Anda telah dihentikan.");
    } else {
        bot.sendMessage(chatId, "Anda tidak memiliki langganan aktif.");
    }
});

setInterval(() => {
    const now = new Date();
    Object.keys(subscriptions).forEach(chatId => {
        if (subscriptions[chatId] < now) {
            delete subscriptions[chatId];
            bot.sendMessage(chatId, "Langganan Anda telah berakhir.");
        }
    });
}, 60 * 1000); // Periksa setiap menit

// Command khusus untuk owner
bot.onText(/\/split_vcf (.+)/, (msg, match) => {
    const chatId = msg.chat.id;
    if (chatId !== ownerId) {
        bot.sendMessage(chatId, "Anda tidak memiliki izin untuk menggunakan perintah ini.");
        return;
    }

    const [fileName, contactsPerFile] = match[1].split(',');
    const filePath = path.join(__dirname, fileName.trim());
    const contactsLimit = parseInt(contactsPerFile.trim());

    if (fs.existsSync(filePath) && !isNaN(contactsLimit)) {
        splitVcfFile(filePath, contactsLimit, chatId);
    } else {
        bot.sendMessage(chatId, "Format perintah salah atau file tidak ditemukan.");
    }
});

function splitVcfFile(filePath, contactsPerFile, chatId) {
    fs.readFile(filePath, 'utf8', (err, data) => {
        if (err) {
            bot.sendMessage(chatId, "Terjadi kesalahan saat membaca file.");
            console.error(err);
            return;
        }

        const contacts = data.split('END:VCARD').filter(contact => contact.trim()).map(contact => contact + 'END:VCARD');
        const totalContacts = contacts.length;
        const numberOfFiles = Math.ceil(totalContacts / contactsPerFile);

        for (let i = 0; i < numberOfFiles; i++) {
            const start = i * contactsPerFile;
            const end = start + contactsPerFile;
            const vcfPart = contacts.slice(start, end).join('\n');
            const vcfFileName = `${path.basename(filePath, '.vcf')}_part${i + 1}.vcf`;
            const vcfFilePath = path.join(__dirname, vcfFileName);

            fs.writeFile(vcfFilePath, vcfPart, err => {
                if (err) {
                    bot.sendMessage(chatId, `Terjadi kesalahan saat menulis file bagian ${i + 1}.`);
                    console.error(err);
                    return;
                }

                bot.sendDocument(chatId, vcfFilePath);
            });
        }
    });
}

bot.onText(/\/request_vcf (.+)/, (msg, match) => {
    const chatId = msg.chat.id;
    if (chatId !== ownerId) {
        bot.sendMessage(chatId, "Anda tidak memiliki izin untuk menggunakan perintah ini.");
        return;
    }

    const [fileName, contactName, contactsPerFile] = match[1].split(',');
    const filePath = path.join(__dirname, fileName.trim());
    const contactsLimit = parseInt(contactsPerFile.trim());

    if (fs.existsSync(filePath) && !isNaN(contactsLimit)) {
        requestVcfFile(filePath, contactName.trim(), contactsLimit, chatId);
    } else {
        bot.sendMessage(chatId, "Format perintah salah atau file tidak ditemukan.");
    }
});

function requestVcfFile(filePath, contactName, contactsPerFile, chatId) {
    fs.readFile(filePath, 'utf8', (err, data) => {
        if (err) {
            bot.sendMessage(chatId, "Terjadi kesalahan saat membaca file.");
            console.error(err);
            return;
        }

        const lines = data.split('\n').filter(line => line.trim());
        const totalContacts = lines.length;
        const numberOfFiles = Math.ceil(totalContacts / contactsPerFile);

        for (let i = 0; i < numberOfFiles; i++) {
            const start = i * contactsPerFile;
            const end = start + contactsPerFile;
            const vcfPart = lines.slice(start, end).map((line, index) => createVcfContact(line, `${contactName} ${start + index + 1}`)).join('\n');
            const vcfFileName = `${path.basename(filePath, path.extname(filePath))}_part${i + 1}.vcf`;
            const vcfFilePath = path.join(__dirname, vcfFileName);

            fs.writeFile(vcfFilePath, vcfPart, err => {
                if (err) {
                    bot.sendMessage(chatId, `Terjadi kesalahan saat
