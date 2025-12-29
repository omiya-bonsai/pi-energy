# Pi ENERGY

**Pi ENERGY** is a small experimental project for **Raspberry Pi Pico 2** that visualizes  
*the cost of computing each digit of π* rather than the value of π itself.

This project intentionally consists of only **two files**:

- `main.py` — the complete executable (including display control)
- `README.md` — this document

No external libraries or drivers are required.

---

## Concept

When π computation is discussed in the news, the focus is usually on:

> “How many digits were computed?”

However, what is rarely shown is:

- how much **time**
- how much **computation**
- and how much **effort**

is required to obtain *each additional digit*.

**Pi ENERGY** is designed to make that invisible cost visible.

The display does **not** show the digits of π.  
Instead, it shows how difficult the *next digit* really is.

---

## Hardware & Software

- Raspberry Pi Pico 2  
- Waveshare Pico‑OLED‑1.3 (128×64, SH1107, SPI)  
- MicroPython  

All display control code for the SH1107 OLED is embedded directly in `main.py`.
No external driver files are used.

---

## Algorithm

The computation uses the **Nilakantha series**:

```
π = 3 + 4/(2·3·4) − 4/(4·5·6) + 4/(6·7·8) − ...
```

This algorithm was chosen deliberately:

- It is simple and easy to understand
- It converges slowly
- Each additional digit becomes significantly more expensive

This makes it ideal for visualizing *computational effort* rather than performance.

Floating‑point arithmetic (`float`) is used, so the project naturally reaches a
practical limit at around **6–7 reliable decimal digits**.

This limitation is not a flaw — it is part of the message.

---

## Display Layout

The OLED is used in **landscape orientation (128×64)**.

```
Pi ENERGY
digits : 6
time   : 06:12
digits/min : 0.0
energy
[==========      ]
```

Only four pieces of information are shown.

---

## Display Explanation

### digits

```
digits : 6
```

The number of **reliable decimal digits** after the decimal point.

This is estimated from the current error:

```
error ≈ |π_estimated − π|
digits ≈ floor(−log10(error))
```

It answers the question:

> “How many digits can we trust right now?”

---

### time

```
time : 06:12
```

Elapsed time since the program started.

This provides the context:

> “How long did it take to reach this number of digits?”

---

### digits/min

```
digits/min : 0.0
```

The average increase in reliable digits over the last 60 seconds.

- A value greater than 0 means digits are still increasing
- `0.0` means no new digit has been achieved recently

When this stays at `0.0`, the system is pushing hard but has not yet crossed the
threshold for the next digit.

---

### energy bar

```
[==========      ]
```

A visual indicator of **computational energy**.

- It represents the current computation speed relative to recent peak speed
- It does **not** represent progress toward the next digit
- It is intentionally abstract

The bar exists to convey *effort*, not precision.

---

## Why the Display Often “Does Not Change”

It is completely normal for:

- `digits` to stay constant for many minutes
- `digits/min` to remain at `0.0`
- the energy bar to stay active

This indicates:

> Massive computation is occurring,  
> but the next digit is still out of reach.

This behavior reflects the true nature of π computation:
each additional digit costs dramatically more energy than the previous one.

---

## What This Project Is (and Is Not)

**This project is:**

- A visualization of computational cost
- A physical demonstration of diminishing returns
- A tool for intuition, not benchmarking

**This project is not:**

- A fast π calculator
- A precision arithmetic library
- A performance contest

---

## Files

```
/
├── main.py
└── README.md
```

That is the entire project.

---

## Closing Thought

If a Raspberry Pi Pico 2 needs minutes to gain a single digit,
then:

> **Supercomputers computing trillions of digits of π are truly amazing.**

