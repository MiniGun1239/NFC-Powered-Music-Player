# --- IMPORTS ---
import board
import busio
from adafruit_hid import keyboard

from adafruit_pn532 import PN532_I2C

import time
import pygame

# ---


# --- DEBUG ---
DEBUG = True
# ---


# --- AUDIO SETUP ---
pygame.mixer.init()

audioPath = "/home/PLACEHOLDER_USER/audio/"

audioFileMapping = {
    "failure"         : "womp_womp.mp3",

    # "keyword_on_the_nfc_card" : "audio_file_name"
}

FAILURE = "failure"
# ---


# --- NFC SETUP ---
i2c = busio.I2C(board.SCL, board.SDA)
pn532 = PN532_I2C(i2c)
pn532.SAM_configuration()

ic, ver, rev, support = pn532.firmware_version
# ---


# --- VAR INIT ---
uid = None
keyword = None
PREVIOUS_KEYWORD = None
# ---


if DEBUG:
    print("[DEBUG] Connected to PN532")
    print(f"[DEBUG] Firmware: IC: {ic}, VER: {ver}, REV: {rev}, SUPPORT: {support}")
    print("[DEBUG] Scan a card")


# Gets board uid to check if board exists
def getBoardUID():
    try:
        uid_local = pn532.read_passive_target(timeout=0.5)
        if DEBUG:
            print("[DEBUG] Reading for Card")

    except Exception as e:
        if DEBUG:
            print("[DEBUG] Error reading card: ", e)
        return 1, None
    return 0, uid_local


# Reads for a nfc tag
def readNFC():
    try:
        raw = pn532.mifare_classic_read_block(4)

        if raw is None:
            if DEBUG:
                print("[DEBUG] Error reading NFC (Mifare)")

            raw = pn532.ntag2xx_read_block(4)

            if raw is None:
                if DEBUG:
                    print("[DEBUG] Error reading NFC (NTAG)")
                return 1, None

        if DEBUG:
            print("[DEBUG] Raw Data: ", raw)

    except Exception as e:
        if DEBUG:
            print("[DEBUG] Error retrieving card info: ", e)
        return 1, None
    return 0, raw


# strips just the keyword and returns it from the raw text
def stripKeyword(data) -> str:
    if len(data) > 7:
        return data[7:].decode("UTF-8").strip('\x00')
    return data.decode("UTF-8").strip('\x00')


def playAudio(name):
    filename = audioFileMapping.get(name)

    # --- Mapping some tags for IO control ---
    if name == "stop":
        pygame.mixer.music.stop()
        return

    if name == "pause":
        pygame.mixer.music.pause()
        return

    if name == "resume":
        pygame.mixer.music.unpause()
        return
    # ---

    # --- Play Audio ---
    if filename:
        pygame.mixer.music.load(audioPath + filename)
        pygame.mixer.music.play()

    else: # if not filename
        if DEBUG:
            print("[DEBUG] File not found")
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.load(audioPath + audioFileMapping.get(FAILURE))
        else:
            pass
    # ---


while True:
    # Check if board exists
    getBoardUID_error, uid = getBoardUID()
    if getBoardUID_error == 1:
        continue

    # If board exists, then read for NFC data
    if uid:
        readNFC_error, rawData = readNFC()
        if readNFC_error == 1:
            continue

        # If NFC data exists, then
        if rawData:
            keyword = stripKeyword(rawData)
            if DEBUG:
                print("[DEBUG] Keyword: ", keyword)

    if not keyword and PREVIOUS_KEYWORD is not None:
        if PREVIOUS_KEYWORD in ["stop", "pause", "resume"]:
            continue

    if keyword:
        if PREVIOUS_KEYWORD in ["stop", "pause", "resume"] and keyword == PREVIOUS_KEYWORD:
            continue

        if keyword != PREVIOUS_KEYWORD:
            if DEBUG:
                print("[DEBUG] Playing Audio")
            PREVIOUS_KEYWORD = keyword
            playAudio(keyword)
        else:
            if DEBUG:
                print("[DEBUG] Same Keyword")
            pass

    # --- RESET ---
    uid = None
    keyword = None
    # ---

    time.sleep(2)
