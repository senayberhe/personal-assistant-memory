import logging

import speech_recognition as sr
import yfinance as yf

# Hide yfinance's own warnings (e.g. "HTTP Error 404") for symbols that don't exist
logging.getLogger("yfinance").setLevel(logging.CRITICAL)


def get_price(ticker):
    try:
        return yf.Ticker(ticker).fast_info["last_price"]
    except Exception:
        return None


def find_ticker(name):
    # Look up a ticker from a company name, e.g. "ford motor" -> "F"
    results = yf.Search(name, max_results=1).quotes
    if results:
        return results[0]["symbol"], results[0].get("shortname", "")
    return None, None


recognizer = sr.Recognizer()


def listen():
    # Record one phrase from the microphone and turn it into text
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
    except sr.WaitTimeoutError:
        print("I didn't hear anything.")
        return None
    except (OSError, AttributeError):
        print("Microphone is unavailable. Type your answer instead.")
        return None

    try:
        text = recognizer.recognize_google(audio).strip()
    except sr.UnknownValueError:
        print("I couldn't understand that.")
        return None
    except sr.RequestError:
        print("Speech recognition service is unavailable. Type your answer instead.")
        return None
    print(f"You said: {text}")
    return text


while True:
    # Obtain ticker symbol (or company name) from you, typed or spoken
    query = input(
        "Which stock (ticker symbol or company name) are you looking for?\n"
        "(Type it, or just press Enter to speak. Say or type 'done' to quit.)\n"
    ).strip()
    if not query:
        query = listen()
        if not query:
            continue
    if query.lower() in ("done", "stop", "quit", "exit"):
        break

    # Ticker symbols never contain spaces, so only try it as a ticker if it has none
    price = None
    name = ""
    if " " not in query:
        ticker = query.upper()
        price = get_price(ticker)
    if price is None:
        ticker, name = find_ticker(query)
        if ticker:
            price = get_price(ticker)

    if price is None:
        print(f"Couldn't find a price for {query!r}. Check the name or symbol and try again.")
    else:
        label = f"{name} ({ticker})" if name else ticker
        print(f"The current price of {label} is {price:.2f}")
