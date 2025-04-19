import os
import cv2
import asyncio
import numpy as np
import face_recognition
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Directory to store known faces
KNOWN_FACES_DIR = "faces"
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

# Store in-memory session states
user_states = {}
TEMP_PHOTO = {}

# Bot buttons
main_menu = ReplyKeyboardMarkup([["Add face", "Recognize faces", "Reset faces"]], resize_keyboard=True)

# --- COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Choose an option:", reply_markup=main_menu)

# --- STATES ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text
    state = user_states.get(chat_id)

    # If user was expected to send a name
    if state == "AWAITING_NAME":
        await handle_name(update, context)
        return

    if text == "Add face":
        user_states[chat_id] = "AWAITING_FACE_IMAGE"
        await update.message.reply_text(
            "Upload an image with a single face.",
            reply_markup=ReplyKeyboardRemove()
        )

    elif text == "Recognize faces":
        user_states[chat_id] = "AWAITING_RECOGNITION_IMAGE"
        await update.message.reply_text(
            "Upload an image and I'll recognize known faces.",
            reply_markup=ReplyKeyboardRemove()
        )

    elif text == "Reset faces":
        for file in os.listdir(KNOWN_FACES_DIR):
            os.remove(os.path.join(KNOWN_FACES_DIR, file))
        await update.message.reply_text("All known faces have been reset.")
        await update.message.reply_text("Choose an option:", reply_markup=main_menu)

    else:
        await update.message.reply_text("Choose a valid option.", reply_markup=main_menu)

# --- IMAGE HANDLING ---
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    state = user_states.get(chat_id)

    if not update.message.photo:
        await update.message.reply_text("Please send a photo.")
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()
    photo_path = f"temp_{chat_id}.jpg"
    await file.download_to_drive(photo_path)

    if state == "AWAITING_FACE_IMAGE":
        TEMP_PHOTO[chat_id] = photo_path
        user_states[chat_id] = "AWAITING_NAME"
        await update.message.reply_text("Great! What is the name of the person in this image?")

    elif state == "AWAITING_RECOGNITION_IMAGE":
        await recognize_faces(photo_path, update)
        os.remove(photo_path)
        user_states[chat_id] = None
        await asyncio.sleep(0.5)
        await update.message.reply_text("Choose an option:", reply_markup=main_menu)

# --- NAME HANDLING ---
async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id not in TEMP_PHOTO:
        return

    name = update.message.text
    photo_path = TEMP_PHOTO.pop(chat_id)
    image = face_recognition.load_image_file(photo_path)
    encodings = face_recognition.face_encodings(image)

    if not encodings:
        await update.message.reply_text("No face found in that image. Try again.")
    else:
        encoding = encodings[0]
        np.save(os.path.join(KNOWN_FACES_DIR, f"{name}.npy"), encoding)
        await update.message.reply_text(f"Face saved as '{name}'!")

    os.remove(photo_path)
    user_states[chat_id] = None
    await update.message.reply_text("Choose an option:", reply_markup=main_menu)

# --- RECOGNITION LOGIC ---
async def recognize_faces(photo_path, update):
    image = face_recognition.load_image_file(photo_path)
    unknown_encodings = face_recognition.face_encodings(image)
    face_locations = face_recognition.face_locations(image)

    if not unknown_encodings:
        await update.message.reply_text("No faces found.")
        return

    known_encodings = []
    known_names = []
    for file in os.listdir(KNOWN_FACES_DIR):
        if file.endswith(".npy"):
            encoding = np.load(os.path.join(KNOWN_FACES_DIR, file))
            known_encodings.append(encoding)
            known_names.append(file.replace(".npy", ""))

    recognized_names = []

    image_cv = cv2.imread(photo_path)
    for encoding, loc in zip(unknown_encodings, face_locations):
        matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.45)
        name = "Unknown"
        if True in matches:
            name = known_names[matches.index(True)]
            recognized_names.append(name)

        # Draw box
        top, right, bottom, left = loc
        cv2.rectangle(image_cv, (left, top), (right, bottom), (255, 0, 0), 2)
        cv2.putText(image_cv, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    # Save annotated image
    result_path = f"result_{update.message.chat_id}.jpg"
    cv2.imwrite(result_path, image_cv)
    await update.message.reply_photo(photo=open(result_path, "rb"))
    os.remove(result_path)

    if recognized_names:
        await update.message.reply_text(f"I found: {', '.join(recognized_names)}")
    else:
        await update.message.reply_text("I don't recognize anyone in this image.")

# --- MAIN ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^[A-Za-z0-9 _-]+$"), handle_name))

    print("Bot running...")
    app.run_polling()
