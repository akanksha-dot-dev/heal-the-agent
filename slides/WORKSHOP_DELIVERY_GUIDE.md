# 🎬 Workshop Delivery Package
## "Heal the Agent" — Complete Slides + Presenter Script

---

# PART 1: SLIDE DECK CONTENT

> Design rules for your slides:
> - Dark background (VS Code dark theme aesthetic)
> - One idea per slide. Slides are cheap; attention is scarce.
> - No bullet points. Use bold typography, diagrams, or single statements.
> - Code on slides: max 8 lines, syntax highlighted, 28pt+ font
> - Use JetBrains Mono or Fira Code for all code
> - Every slide should be readable from the back row in 3 seconds

---

## SLIDE 0 — TITLE (displayed while people settle in)

```
    🩺 HEAL THE AGENT

    Build an AI that fixes its own mistakes

    akanksha-dot-dev
    github.com/akanksha-dot-dev/heal-the-agent
```

No speaker notes. This is ambient. You're greeting people, helping with setup issues.

---

## SLIDE 1 — THE EQUATION (shown AFTER the live demo hook)

```
    Agent  =  Model  +  Harness

               │              │
        writes text     everything else
        (the brain)    (the skeleton, muscles,
                        immune system)
```

**Speaker notes:**
> "This is the one idea I want you to take home today. An AI agent isn't just a model. The model is the brain — it writes text, and that's it. Everything else — the tools, the error handling, the verification, the retry logic — that's the harness. And today you're going to learn that the harness is what separates a demo from a system that works at 3 AM."

---

## SLIDE 2 — CHATBOT vs AGENT

```
    Chatbot                     Agent
    ───────                     ─────

    You ask, it answers         It decides what to do

    Knows nothing               Has tools (hands)
    about the world

    Stops after one reply       Loops: Think → Act → Observe

    "What's the weather?"       Calls an API, reads the
    "I don't have access"       result, gives you the answer
```

**Speaker notes:**
> "When you use ChatGPT and ask 'what's the weather?' — it guesses. An agent actually calls a weather API, reads the response, and gives you the real answer. That's the difference: a chatbot talks, an agent acts."

---

## SLIDE 3 — WHAT GOES WRONG

```
    What goes wrong?


    APIs change their format       💥

    Models hallucinate             🤡

    Tools crash silently           🕳️

    Wrong answers look right       😱


    What if the agent could notice... and fix it?
```

**Speaker notes:**
> "In the real world, things break. Vendor APIs rename their fields overnight. Models return garbage when they're confused. And the scariest bugs? The ones that don't crash — they just return wrong answers that look right. What if your agent could detect all of these — including the silent ones — and fix them without waking up a human?"

---

## SLIDE 4 — THE SELF-HEALING LOOP

```
    The Self-Healing Loop

        ┌─────────┐
        │  SENSE  │──── Is the output correct?
        └────┬────┘     (exceptions + contracts)
             │ no
        ┌────▼─────┐
        │ DIAGNOSE │──── Show the AI the crash + code
        └────┬─────┘
             │
        ┌────▼─────┐
        │  VERIFY  │──── Test the fix. Trust no one.
        └────┬─────┘
             │ fail
        ┌────▼─────┐
        │   LOOP   │──── Remember what failed. Try again.
        └──────────┘     Escalate to a smarter model.
```

**Speaker notes:**
> "This is what you're building today. Four steps. SENSE — did the parser crash, or did it return a wrong answer? DIAGNOSE — show the AI the error, the code, and the data. VERIFY — never trust the AI's fix. Test it. Run it on old data too. LOOP — if the fix fails, remember WHY it failed, and try again with that memory. This is the harness."

---

## SLIDE 5 — TODAY'S SCENARIO

```
    🌤️ The Scenario

    You have a weather agent.
    It calls a vendor API to get temperatures.
    Your parser converts the response to a clean format.

    One morning, the vendor changes their API format.

       v1:  { "city": "Lisbon", "temp_c": 31.2 }
                       ↓ vendor update
       v2:  { "location": { "name": "Lisbon" },
              "current": { "temp": 31.2 } }          💥
                       ↓ sneakier update
       v3:  { ... "temp": 88.2, "unit": "F" }        😱

    Your parser breaks. Can the agent heal itself?
```

**Speaker notes:**
> "Here's the real-world scenario. You've got a weather agent. Everything works great. Then one morning — no email, no warning — the vendor changes their API format. Your parser crashes. That's v2. But v3 is worse — it doesn't crash at all. It just switches to Fahrenheit, and your parser happily reports 88 degrees Celsius. No error. Just a wrong answer. That's the kind of bug that burns you."

---

## SLIDE 6 — YOUR TOOLKIT

```
    Your Toolkit

    🔧  Google ADK         Agent framework (Python)
                            Your agent calls tools

    🧠  Gemini Flash       Cloud model — the "doctor"
                            Diagnoses and writes fixes

    🏠  Ollama (optional)   Local model on YOUR laptop
                            Same job, no internet needed

    📋  The Harness         The code YOU write today
                            Sense → Diagnose → Verify → Loop
```

**Speaker notes:**
> "Three tools. Google ADK — an open-source framework for building agents. Gemini — a cloud model that will be our 'doctor', diagnosing crashes and writing fixes. And optionally, Ollama — the same thing but running locally on your laptop, no internet needed. But the star of the show isn't any model — it's the harness. That's the Python code you're going to write."

---

## SLIDE 7 — SETUP CHECK

```
    ⏸️ Setup Check — 2 minutes

    Run this now:

       python check_setup.py

    You need:
       ✅  Python 3.11+
       ✅  google-adk installed
       ✅  GOOGLE_API_KEY in your .env
       ✅  A Gemini model responds

    Stuck? → cp solutions/healer.py harness/healer.py
             catches you up at any point
```

---

## SLIDE 8 — EXERCISES (reference slide, stays up during coding)

```
    4 Exercises in harness/healer.py

    Ex 1 │ SENSE     Did it crash? Is the answer wrong?
    Ex 2 │ EXTRACT   Pull code from the model's reply
    Ex 3 │ VERIFY    Test the fix. Check for regressions.
    Ex 4 │ LOOP      Retry with memory + model escalation

    After 1-3:  python run_demo.py --api v2    → heals!
    After 4:    python run_demo.py --api v3    → heals v3!
```

---

## SLIDE 9 — WHAT'S NEXT (closing)

```
    What's Next?

    📚  ADK docs              adk.dev
    🧪  ADK recipes           github.com/google/adk-recipes
    🎓  ADK masterclass       20-module deep-dive
    🩺  Today's code          github.com/akanksha-dot-dev/
                              heal-the-agent

    Concepts to explore:
    • Memory and sessions     • MCP (Model Context Protocol)
    • Guardrails at scale     • Multi-agent orchestration
    • Deploying to Cloud Run

           The model writes text.
           The harness does everything else.
           Go build harnesses. 🔧
```

---

---

# PART 2: MINUTE-BY-MINUTE PRESENTER SCRIPT

**How to use this script:**
- ⏸️ = Physical pause. Stop talking. Count to 3 in your head. Let it land.
- 🎯 = Checkpoint. Everyone should be at this state before moving on.
- 🚨 = Escape hatch. What to do if you're behind schedule.
- 💬 = Exact words to say (you can paraphrase, but the structure matters)
- 👀 = Look at the audience, not the screen

---

## 0:00 – 0:03 | 🎬 THE HOOK (No slides. Terminal only.)

**Option A: Terminal hook** (classic, dramatic)

Your screen: a terminal, font size cranked up. Title slide was visible while people settled. Now switch to terminal.

**Option B: Dashboard hook** (visual, audience-friendly — RECOMMENDED for large rooms)

Open `python dashboard.py` beforehand. The audience sees the beautiful dark UI. Select v2, click **Break It** → red crash appears. Then click **Heal It** → pipeline lights up step by step → green HEALED banner. Way more visual than a terminal.

**Either way, here's the script:**

💬 **Say:**
> "Let me show you something before we start."

Run:
```bash
python reset.py
python run_unprotected.py
```

💬 **Say:**
> "This is a weather agent. It calls a vendor API, parses the response, gives you the temperature. Working great. Now watch what happens when the vendor changes their API format — which, by the way, happens all the time in production."

Run:
```bash
python run_unprotected.py --api v2
```

The screen shows a crash: `KeyError: 'city'`. Red traceback.

⏸️ Let the crash sit on screen for 2 full seconds.

💬 **Say:**
> "Dead. The vendor renamed their fields. Our parser had no idea. In the real world, this is a 3 AM pager alert."

⏸️

💬 **Say:**
> "Now watch this."

Run:
```bash
python run_demo.py --api v2
```

The screen shows: 🔴 SENSE → 🩺 DIAGNOSE → 🧪 VERIFY → 💊 PATCH → ✅ HEALED

⏸️ Let people read the output. Give it 3-4 seconds.

💬 **Say** (slowly):
> "An AI just read a crash log... diagnosed what went wrong... wrote a fix... tested it... and applied it. No human involved. In the next 55 minutes, you're going to build the thing that made that happen."

⏸️ ⏸️ Long pause. This is the moment. Let it land.

👀 Make eye contact with someone in the audience.

💬 **Say:**
> "Let's talk about what just happened."

Switch to Slide 1: Agent = Model + Harness

---

## 0:03 – 0:10 | 📊 CONCEPT SLIDES (Slides 1–6)

**Pace: ~1 minute per slide. Keep it moving.**

Slide 1 → Slide 2 → Slide 3 → Slide 4 → Slide 5 → Slide 6

Use the speaker notes above for each. Key transitions:

- **Slide 1 → 2:** "So what IS an agent compared to a chatbot?"
- **Slide 2 → 3:** "Agents act. But when they act, things go wrong."
- **Slide 3 → 4:** "That's why we need the self-healing loop."
- **Slide 4 → 5:** "Let me show you the specific scenario you're building for."
- **Slide 5 → 6:** "And here are your tools."

> **Don't linger on slides.** Developers hate slide decks. The slides exist to frame the concept — the demo already did the convincing. Get through these in 7 minutes max.

---

## 0:10 – 0:12 | 🔧 SETUP CHECK (Slide 7)

💬 **Say:**
> "Quick setup check. Everyone run this now."

```bash
python check_setup.py
```

💬 **Say:**
> "You need four green checkmarks. The Ollama one is optional — it's fine if it's a warning. If you've got four greens, you're ready."

Walk around. Help anyone stuck. Give it 90 seconds max.

🚨 **If someone can't get it working:**
> "No worries — follow along on my screen for now. We'll debug yours during Exercise 1."

🎯 **Checkpoint:** Most people see four greens.

---

## 0:12 – 0:22 | 📝 EXERCISE 1: SENSE (10 min)

Slide 8 stays up as reference. You switch to your editor showing `harness/healer.py`.

💬 **Say:**
> "Open `harness/healer.py`. This is the harness. Everything you build today goes in this one file. Scroll to line 41 — the `sense()` function."

⏸️ Give people 15 seconds to find it.

💬 **Say:**
> "The sense function runs the parser in a sandbox and reports what happened. Your job: look at the outcome and return the right status. There are three cases."

Point to the screen and walk through each case:

💬 **Say:**
> "Case 1: it timed out or couldn't even load — that's an exception. Case 2: it ran but the contract check found problems — like temperature being 88 degrees Celsius. That's wrong, but it didn't crash. Case 3: everything's fine — return ok."

💬 **Say:**
> "The TODO comment tells you exactly what to check. Give it a shot — you have about 6 minutes."

Walk around. Peek at screens. Help anyone stuck.

🚨 **If someone is lost:** 
> "Look at the `outcome` dictionary. Check for 'timeout', then 'load_error', then check if `outcome['results'][0]['ok']` is False. If none of those, run `contract_violations()` on the result."

**At 0:20 (8 min in):**

💬 **Say:**
> "Alright, let's look at this together."

Show the solution on YOUR screen. Walk through it:

```python
if "timeout" in outcome:
    return {"ok": False, "kind": "timeout", "detail": "..."}
if "load_error" in outcome:
    return {"ok": False, "kind": "exception", "detail": outcome["load_error"]}
first = outcome["results"][0]
if not first["ok"]:
    return {"ok": False, "kind": "exception", "detail": first["traceback"]}
problems = contract_violations(first["result"])
if problems:
    return {"ok": False, "kind": "contract violation", "detail": "; ".join(problems)}
return {"ok": True, "result": first["result"]}
```

💬 **Say** (this is the key insight):
> "Notice the contract check. Most people would stop at 'did it crash?' But the contract catches something exceptions can't — a WRONG answer that looks right. That's the difference between a toy and a system."

⏸️

---

## 0:22 – 0:28 | 📝 EXERCISE 2: EXTRACT (6 min)

💬 **Say:**
> "Exercise 2 — line 69. The model is chatty. It writes a diagnosis in plain English, then wraps its code fix in a python code block. Your job: pull out just the code."

💬 **Say:**
> "This is literally one line of regex. Find the text between triple-backtick-python and triple-backtick. If there's no code block, return None."

Give them 4 minutes. This is the easy one.

💬 **Say (showing the answer):**

```python
match = re.search(r"```(?:python|py)?\s*\n(.*?)```", reply, re.DOTALL)
return match.group(1).strip() + "\n" if match else None
```

💬 **Say:**
> "Simple, but important. The model doesn't know it's writing to a file. It thinks it's in a conversation. The harness is the one that takes its chatty reply and surgically extracts the useful part."

---

## 0:28 – 0:40 | 📝 EXERCISE 3: VERIFY (12 min)

💬 **Say:**
> "This is the most important exercise. Line 81. The `verify()` function. The model just proposed a fix. Do you trust it?"

👀 Look at the audience.

💬 **Say:**
> "No. You never trust model output. You test it."

💬 **Say:**
> "Four checks. First: `static_check()` — does the code have forbidden imports like `import os`? The model might try. Second: run it in the sandbox on the NEW payload that broke. Did it crash? Third: check the result against the contract — is the temperature in a plausible range? Fourth — and this is the one most people miss — run it on the OLD payloads too. A fix that breaks existing behavior is worse than no fix. That's a regression."

Give them 8 minutes.

🚨 **If running behind:** Cut this to 6 minutes. Show the solution after 5 and explain it.

💬 **Showing the solution:**

```python
problems = static_check(candidate)
if problems:
    return problems
payloads = [raw] + [old_raw for old_raw, _ in KNOWN_GOOD]
out = run_sandboxed(candidate, payloads)
# ... check timeout, load_error, new result contract, old regressions
```

💬 **Key insight:**
> "The v3 scenario is where this shines. The first fix attempt will NOT crash. It'll parse the nested format correctly. But it'll report 88.2 as Celsius — because the model didn't notice the unit field. Your contract catches that. Temperature outside -90 to 60? Rejected. THAT is why contracts matter."

---

## 0:40 – 0:42 | 🎯 THE FIRST MAGIC MOMENT

💬 **Say:**
> "If you've finished exercises 1, 2, and 3 — run this now."

```bash
python reset.py
python run_demo.py --api v2
```

On your screen, show it running. The room watches the SENSE → DIAGNOSE → VERIFY → HEALED sequence.

⏸️ Let people react. Some will gasp. Some will grin.

💬 **Say:**
> "Your agent just healed itself. The parser crashed. The model wrote a fix. Your verifier approved it. The parser file on disk was rewritten. And the agent got a correct answer."

🚨 **If someone's behind:** 
> "Run `cp solutions/healer.py harness/healer.py` to catch up. Then run the demo."

---

## 0:42 – 0:50 | 📝 EXERCISE 4: THE LOOP (8 min)

💬 **Say:**
> "One more. Line 92. Right now the healer tries once and gives up. That worked for v2 — the first fix was correct. But watch what happens with v3."

```bash
python reset.py
python run_demo.py --api v3
```

It tries once. The fix looks right. But the contract rejects it — temp_c=88.2 is not Celsius. It gives up.

💬 **Say:**
> "See? The first fix handled the nested format but ignored the Fahrenheit conversion. The verifier caught it. But then... it gave up. Exercise 4: turn this one-shot into a loop. Retry up to MAX_ATTEMPTS times. Feed the rejection reason BACK into the prompt — so the model doesn't make the same mistake twice. And if the current model fails, escalate to the next one in the cascade."

Give them 6 minutes.

💬 **Key structure:**
> "Turn the single-attempt into a `while attempt < MAX_ATTEMPTS and cascade:` loop. After a rejection, append the reason to the `failures` list — it's already fed into the prompt. Pop the current model from the cascade to escalate."

---

## 0:50 – 0:52 | 🎯 THE BIG MOMENT

💬 **Say:**
> "Now run v3 again."

```bash
python reset.py
python run_demo.py --api v3
```

Attempt 1: fix rejected (temp_c=88.2 out of range). Attempt 2: model reads the failure memory, notices the unit field, adds F-to-C conversion. Verified. HEALED.

⏸️ ⏸️ ⏸️ This is THE moment. Give it a full 5 seconds of silence.

💬 **Say** (slowly, deliberately):
> "The first attempt failed. The verifier said: temperature 88.2 is outside the plausible Celsius range. The model remembered that. On the second attempt, it read the 'unit: F' field and added a Fahrenheit-to-Celsius conversion. It learned from its own mistake."

⏸️

💬 **Say:**
> "That's the harness. The model didn't get smarter. The harness gave it memory, verification, and a second chance. That's harness engineering."

---

## 0:52 – 0:55 | 🔮 CLOSING (No slides or Slide 9)

💬 **Say** (walk away from the screen, toward the audience):
> "What you built today is simplified. But the pattern is real. In production..."

> "The 'vendor API change' is any external dependency breaking — a schema migration, a rate limit, a timeout."

> "The 'contract' is your test suite, your invariants, your observability layer."

> "The 'doctor' is any model — local or cloud — that can reason about code."

> "And the 'harness' — the sense-diagnose-verify-loop — that's the architecture that ties it all together."

⏸️

💬 **Say:**
> "The model writes text. The harness does everything else. If you remember one thing from today, remember that."

Show Slide 9: What's Next + resources

💬 **Say:**
> "The repo is live — github.com/akanksha-dot-dev/heal-the-agent. The solutions folder has the complete code if you want to play with it later. The ADK docs and masterclass links are on this slide."

---

## 0:55 – 1:00 | ❓ Q&A

💬 **Say:**
> "Questions?"

### Pre-scripted answers:

| Likely Question | Your Answer |
|---|---|
| "How is this different from ChatGPT?" | "ChatGPT answers questions. This takes actions — it calls APIs, reads files, writes code. And it does it in a loop, without you asking. The harness is the thing that makes that loop safe." |
| "Could the fix introduce new bugs?" | "Yes! That's exactly why the verifier exists. It runs the fix on old data too — if it breaks anything that used to work, it's rejected. In production you'd also run your full test suite." |
| "Why not just use one model?" | "You could. The cascade is about cost and reliability. Try the cheap local model first. If it fails, escalate to a smarter cloud model. Mix them based on the task." |
| "What if the model writes malicious code?" | "Good question. Check out guardrails.py. There's an AST allow-list that blocks import os, exec, open, etc. And the code runs in a subprocess sandbox. It's a speed bump, not Fort Knox — but for a workshop it's real." |
| "Can this work fully offline?" | "The weather API is already fake — fully offline. For the doctor, you can use Ollama with a local model, or the replay cassettes — pre-recorded answers. The selftest runs fully offline." |
| "What about larger codebases?" | "This parser is 10 lines. For larger code, you'd need AST-level patching, structured diffs, and chunking. But the sense-diagnose-verify-loop pattern scales — it's the same architecture." |

### Closing line:

💬 **Say:**
> "You walked in knowing how to USE AI. You're walking out knowing how to build AI that fixes itself. Go break things."

👀 Smile. Nod. Done.

---

---

# PART 3: PRESENTER CHEAT SHEET (print this on a single page)

```
BEFORE THE WORKSHOP
────────────────────
□ python selftest.py           → ALL GREEN?
□ python check_setup.py        → ALL GREEN?
□ python reset.py              → parser reset?
□ python dashboard.py          → opens in browser?
□ Font size cranked up (28pt+)
□ Desktop notifications OFF
□ .env has a working API key
□ solutions/healer.py untouched

THE TIMELINE (keep this visible to yourself)
─────────────────────────────────────────────
 0:00  Hook: unprotected crash → healed demo
 0:03  Slides 1–6 (7 min, keep moving)
 0:10  Setup check (2 min)
 0:12  Exercise 1: SENSE (10 min)
 0:22  Exercise 2: EXTRACT (6 min)
 0:28  Exercise 3: VERIFY (12 min)
 0:40  ★ Checkpoint: run_demo.py --api v2
 0:42  Exercise 4: LOOP (8 min)
 0:50  ★ BIG MOMENT: run_demo.py --api v3
 0:52  Closing talk (3 min)
 0:55  Q&A (5 min)

ESCAPE HATCHES
──────────────
Behind by 5+ min → skip Exercise 4, demo v3 yourself
Someone stuck    → "cp solutions/healer.py harness/healer.py"
Demo fails       → "See? Even our demo broke. That's why we need healing!"
Deep question    → "Great question. Let's chat after — I have a link."
Nervous          → Breathe. Pause. Slow down. You're faster than you think.

THE ONE LINE
────────────
"The model writes text. The harness does everything else."
```
