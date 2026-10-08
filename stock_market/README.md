# Live stock price lookup

A small command-line tool that tells you the current price of a
stock. Type a ticker symbol or a company name, or just speak it.

```
Which stock (ticker symbol or company name) are you looking for?
(Type it, or just press Enter to speak. Say or type 'done' to quit.)
ford motor
The current price of Ford Motor Company (F) is 11.42

AAPL
The current price of AAPL is 228.10
```

## Run it

From the repository root:

```bash
uv sync
uv run python stock_market/live_price.py
```

Speaking needs a microphone and PortAudio (`brew install portaudio`).
Type `done`, `stop`, `quit` or `exit` to leave.

## How it works

1. **Input:** you type a query, or press Enter to say it. Speech is
   turned into text with Google's speech recognition
   (`SpeechRecognition`).
2. **Ticker first:** a query without spaces, such as `aapl`, is tried
   as a ticker symbol, because ticker symbols never contain spaces.
3. **Name search:** if that finds no price, the query is searched on
   Yahoo Finance (`yf.Search`) and the best match is priced.
4. **Price:** read from `yfinance`'s `fast_info["last_price"]`.

## Error handling

Each failure gets a clear message, and the program keeps running:

| Situation                       | What happens                          |
| ------------------------------- | ------------------------------------- |
| No microphone                   | Asks you to type instead              |
| Nothing said within 5 seconds   | "I didn't hear anything."             |
| Speech not understood           | "I couldn't understand that."         |
| Speech service unreachable      | Asks you to type instead              |
| Unknown symbol or company       | Says no price was found               |

`yfinance` prints its own warnings (for example `HTTP Error 404`)
for symbols that do not exist; these are silenced so only the
tool's own messages appear.

## Ideas for next steps

- Add it as a tool for the assistant in `chatting/`, so you can ask
  "what's Apple trading at?"
- Build a Streamlit dashboard with a price chart (`streamlit` is
  already a dependency).
- Show the day's change and percentage next to the price.
