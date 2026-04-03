# 🧠 LadderLogic-Gen Core Architecture

## 🔷 Core Idea
Convert natural language → structured Intermediate Representation (IR) → ladder logic

---

## 🧱 IR Design

The IR is the **heart of the system**.

It must be:
- human-readable
- machine-transformable
- PLC-agnostic

---

## 🔹 IR Schema (v0.1)

```json
{
  "inputs": ["start_button", "overload"],
  "outputs": ["motor"],
  "logic": [
    {
      "type": "rung",
      "id": 1,
      "conditions": [
        {"var": "start_button", "op": "NO"},
        {"var": "overload", "op": "NC"}
      ],
      "action": {"var": "motor", "state": "ON"}
    }
  ]
}
```

---

## 🔹 Concepts

- NO = Normally Open
- NC = Normally Closed
- Rung = single logic line

---

## 🔁 Pipeline

1. Input Parser → extracts entities
2. IR Builder → constructs logic tree
3. Generator → converts IR → ladder
4. Export Layer → PLC formats

---

## 🧪 Example Flow

Text:
"Start motor when button pressed and no overload"

↓

IR:
- conditions: start_button (NO), overload (NC)
- action: motor ON

↓

Ladder:
[ Start ] --[/ Overload ]----( Motor )

---

## 🔮 Future Extensions

- Timers (TON, TOFF)
- Counters
- Parallel branches
- Safety constraints
- Simulation validation

---

## ⚡ Philosophy

IR is NOT tied to any vendor.
It acts like a compiler layer for industrial logic.
