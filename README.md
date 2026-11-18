# ProGamble

A pocket casino that plays **European roulette with virtual points** (no real money). It runs on an
**Arduino Nano ESP32** programmed in MicroPython.

## Project goal

ProGamble is an interactive European roulette game:

- the device **wakes up when someone approaches** (PIR sensor),
- it **adjusts its screen brightness, LED brightness and sound volume to the room's light** (photoresistor),
- it **goes to sleep** when nobody is around.

The player places bets with **4 push buttons**. The wheel spins on the **TFT screen**, the **LED ring** and the
**buzzer**, and a **status LED** shows the device state.

## Team

- First Last (A): *to fill in*
- First Last (B): *to fill in*

GitHub repository: *to fill in*

## Hardware

| Qty | Component | Role |
|---|---|---|
| 1 | Arduino Nano ESP32 (ABX00083, ESP32-S3) | Main board |
| 1 | 2.8" SPI TFT display, ILI9341, 240×320 ([listing](https://www.aliexpress.com/item/32847628219.html)) | **New component**: game screen |
| 1 | WS2812B addressable RGB LED ring ([listing](https://www.aliexpress.com/item/1005005898995061.html)) | **New component**: wheel animation |
| 1 | Keyestudio photoresistor module (S, +, −) | **Analog** sensor: room light |
| 1 | Keyestudio PIR motion sensor (PYE-IR, S, +, −) | **Digital** sensor: presence |
| 1 | Passive buzzer | **PWM** output: sounds |
| 1 | Keyestudio LED module | **Digital** on/off output: status |
| 4 | 2-pin push buttons | Local controls (PREV, NEXT, SELECT, SPIN) |
| 1 | 330 Ω resistor | Protects the ring's data line (DIN) |
| 1 | ~470 µF electrolytic capacitor (≥ 10 V) | Absorbs the ring's power spikes |
| – | Breadboard and jumper wires | Solderless build |

> **Check your parts.** The AliExpress listings could not be checked automatically. This README assumes:
> - The display is the common red **2.8" ILI9341 SPI** module with 14 pins (VCC … T_IRQ) and an SD card
>   header. Check the chip name printed on the listing. If it is an **ST7789**, the wiring stays the same but
>   the driver changes.
> - The ring is a **WS2812B** (or a compatible SK6812 RGB). Count its LEDs (8, 12, 16 or 24) and set that
>   number in the code. It also affects the power budget below.
