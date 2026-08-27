# CivicFlow AI — Project Review (25 Aug 2026)

Mam ki Project 7 requirements ke against poore code ka audit. Har point code se verify kiya gaya hai.

---

## 1. Ek line ka verdict

**Product (UI/UX + domain idea): 9/10 — bohot strong aur unique.**
**Agentic AI core: 2/10 — abhi bilkul nahi hai.**

Aap ka `app.py` (1850 lines) ek professional municipal dashboard hai — 3 role portals, wizard,
Plotly map, HITL page, analytics, notifications. Ye sach much impressive hai.

Lekin jo cheez mam grade kar rahi hain — *Agentic AI workflow* — wo poori tarah missing hai.
Jo "AI agents" dikhte hain, wo asal mein `if keyword in text` hai. Ek bhi LLM call nahi hoti.

Agar mam ne `orchestrator_pipeline.py` khol ke poocha "yahan agent kahan hai?", to defend karna
mushkil ho jayega. Isi liye ye report seedhi baat karti hai.

---

## 2. Requirement-by-requirement mapping

| Mam ki requirement | Status | Code evidence |
|---|---|---|
| Python 3.10–3.12+ | ✅ | 3.14 pycache (3.14 par kuch libs abhi unstable — 3.12 recommended) |
| LLM (Groq/Gemini/Ollama/OpenRouter/HF) | ❌ | `llm_config.py` = `DummyLLM` jo `NotImplementedError` raise karta hai. `.env` mein `GROQ_API_KEY=` khaali |
| LangChain | ❌ | kahin import nahi; `requirements.txt` mein comment out |
| LangGraph | ❌ | koi `StateGraph`, node, edge, checkpointer nahi |
| ReAct pattern | ❌ | koi reasoning loop nahi |
| Tool / Function Calling | ❌ | ek bhi tool define nahi |
| Agentic RAG | ❌ | `run_rag_search()` ek hardcoded f-string return karta hai |
| Multi-Agent Workflow | ⚠️ | naam ke 5 "agents" — asal mein ek function ke andar 5 audit rows insert |
| Chroma Vector DB | ⚠️ | `database.py` mein collections ban jate hain, magar kabhi `.add()` nahi hota → memory hamesha khaali |
| Web search / info retrieval | ❌ | nahi |
| Streamlit UI | ✅ | bohot achhi, wizard + role-based nav |
| Playwright / SendGrid / Pushover | ❌ | notifications sirf DB rows hain, koi real email/push nahi |
| LangSmith tracing | ❌ | nahi |
| Pydantic structured outputs | ⚠️ | `schemas.py` mein 18 models likhe hain — magar unhe koi LLM fill nahi karta, sab hand-made |
| Guardrails (input/output validation, safety) | ⚠️ | sirf `len(desc) < 10` check; koi prompt-injection ya output validation nahi |
| Error handling | ⚠️ | 40+ jagah `except Exception: pass` — errors chup chaap gayab ho jate hain |
| Env vars, no committed secrets | ⚠️ | `.env` use hoti hai (achha) magar `.gitignore` nahi hai → repo push par leak ho jayegi |
| README (setup, architecture, usage) | ❌ | README file mojood nahi |
| Screenshots / demo | ❌ | nahi |
| Clean organized code | ⚠️ | `core_agents.py`, `routing_agents.py`, `operations_agents.py` **dead code** hain — `app.py` inhe import hi nahi karta |
| GitHub repo | ❌ | folder git repo nahi hai |

**Score: 2 full ✅ out of 21.**

---

## 3. Functional bugs (ye demo ke waqt pakre jayenge)

**A. Citizen ko apni tickets aur notifications nazar hi nahi ati.**
`app.py` login par: `username = email_clean.split("@")[0]` → `"citizen"`.
Pipeline ticket save karta hai `citizen_id="citizen"`, magar seed data mein
`citizen_id="citizen@civicflow.com"` hai (line 469). Aur notification header
`get_user_notifications(user_email)` = full email se dhoondta hai jabke
`create_notification(username)` = `"citizen"` se likhta hai. **Dono taraf mismatch.**
Fix: har jagah `user_email` (full email) ko single identity banayein.

**B. `ensure_demo_data()` sirf Authority/Admin ke liye chalta hai** (lines 1257, 1503) —
Citizen portal pehli dafa khaali dikhta hai.

**C. Telemetry page 100% jhooth hai.** `latency`, `throughput`, `cache_hit` hardcoded arrays hain
(lines 1748–1750), "System Health 99.8%", "AI Agents Active 6", "Avg Routing SLA 1.4s" bhi
hardcoded. Ye academic integrity ka risk hai — inhe real DB/LangSmith numbers se replace karein
ya saaf-saaf "Simulated" label lagayein.

**D. Duplicate detection bohot naive hai** (line 994): 4 se lambe kisi bhi word ka substring match.
"water" har water complaint ko duplicate bata dega. Ye kaam Chroma embeddings ka hai.

**E. `Auth.py` `verify_password()` plaintext password ko bhi accept karta hai** (line 26):
`plain_password == hashed_password`. Ye security hole hai — hata dein.

**F. Duplicate artifacts:** `civicflow.db` + `civic_ai.db`, aur `chroma_store/` + `chroma_db_store/`.
Aur ek aawara file `Auth screens snippet · PY`. Cleanup chahiye.

**G. `_evaluate_risk_and_sla` app.py line 1026 mein SLA hours dubara hardcode karta hai** —
single source of truth toot gaya.

---

## 4. Jo add karna zaroori hai (requirement-level, optional nahi)

1. **Real LLM** — `langchain-groq` + `ChatGroq` (llama-3.3-70b-versatile). Groq free hai.
   `llm_config.py` ka `DummyLLM` delete.
2. **LangGraph `StateGraph`** — asli nodes: `intake → classify → verify_evidence → retrieve_memory
   → dedupe → risk_assess → rag_sop → route_department → hitl_gate → notify → close`,
   with conditional edges (emergency fast-track vs normal), aur `SqliteSaver` checkpointer.
3. **Pydantic structured outputs** — aap ke `schemas.py` models ko
   `llm.with_structured_output(ProblemUnderstanding)` se fill karayein. Ye already likhe hue hain,
   sirf wire karna hai.
4. **Agentic RAG** — municipal SOP documents (PDF/MD) Chroma mein ingest karein, phir
   `sop_vector_collection` se retrieve kar ke resolution plan generate karein. Ek
   `ingest_sops.py` script chahiye.
5. **Tool calling** — 4–6 real tools: `get_weather(lat, lon)` (OpenWeather key already `.env` mein),
   `search_similar_tickets()`, `lookup_department_sop()`, `create_ticket()`, `send_notification()`,
   `web_search()`. LLM khud decide kare kaunsa tool chalana hai.
6. **LangSmith tracing** — 4 env vars (`LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`,
   `LANGCHAIN_PROJECT`, endpoint). Phir Telemetry page real traces dikhaye.
7. **Guardrails module** — `guardrails.py`: input length/PII/abuse check, prompt-injection filter,
   output schema validation, LLM fail hone par safe fallback, aur "off-topic complaint" reject.
8. **README.md + .gitignore + .env.example + architecture diagram (Mermaid)** + screenshots.
9. **Dead code delete** ya properly wire karein — `routing_agents.py`, `operations_agents.py`.

---

## 5. Unique / advance features — jo aap ko baqi sab se alag karengi

Ye wo cheezein hain jo class ke kisi aur project mein shayad na hon. 3–4 chun lein, sab nahi.

**1. Self-critique / Reflection loop (LangGraph cycle).**
Ek `Critic` node jo Router agent ke faisle ko dobara check kare: "kya ye department sahi hai?
kya risk score justified hai?" Agar confidence < 0.7 to graph wapis `classify` node par jaye
(max 2 retries). Ye asli agentic behaviour hai — most students ke paas linear chain hoti hai.

**2. Confidence-gated HITL (real, not decorative).**
Aap ke paas HITL page already hai. Isko LLM ki `confidence_score` se drive karein:
`confidence < 0.65 OR is_emergency` → `interrupt()` par graph *ruk jaye* (LangGraph checkpointer +
`interrupt_before`), Admin approve kare, phir wahi state resume ho. Ye textbook production pattern hai.

**3. Geo-temporal hotspot prediction agent.**
Chroma embeddings + lat/lon clustering se: "Gulberg mein pichle 30 din mein 7 water complaints —
83% probability agle 2 hafton mein pipeline failure." Ye *predictive* hai, sirf reactive nahi.
Isse aap ka project "complaint form" se "city intelligence system" ban jata hai.

**4. Evidence vision verification (multimodal).**
Groq par `llama-3.2-90b-vision` free hai. Uploaded photo ko actually dekhein aur text ke sath
cross-verify karein: "text says pothole, image shows garbage → conflict_detected=True".
Aap ka `EvidenceIntelligence` schema is ke liye pehle se ready hai. Fake complaint detection.

**5. Multilingual intake (Urdu/Roman Urdu → English).**
Citizen Urdu mein likhe, agent normalize kar ke English structured output de. Pakistan ke
context mein ye real-world value hai aur demo mein turant nazar aata hai.

**6. Cost & token dashboard.**
Har pipeline run ke tokens + latency DB mein save karein, Telemetry page par *real* numbers dikhayein.
Ye directly aap ke fake telemetry problem ko strength mein badal deta hai.

**7. SLA breach watchdog agent (scheduled).**
Background job jo SLA deadline cross hone par khud escalate kare (Tier 1 → Tier 2) aur
Pushover/SendGrid se notify kare. Autonomy ka clear demonstration.

**8. "Explain this decision" button.**
Har ticket par ek button jo us ticket ke saare LangGraph node traces + reasoning dikhaye
(explainable AI). Aap ka `audit_logs` table already ye support karta hai — sirf real reasoning
bharna hai.

---

## 6. Recommended order (agar time kam hai)

**Phase 1 — must, warna requirement fail (highest priority):**
Groq LLM wire karna → LangGraph StateGraph → Pydantic structured outputs → guardrails.py →
README + .gitignore + .env.example → citizen_id bug fix.

**Phase 2 — requirement complete karta hai:**
Chroma RAG (SOP ingestion) → tool calling (4–6 tools) → LangSmith tracing → real telemetry.

**Phase 3 — "unique advance" wala tarka:**
Reflection loop + confidence-gated HITL interrupt + vision evidence check + hotspot prediction.

**Phase 4 — polish:**
Dead code cleanup, duplicate db/chroma folders hatana, screenshots, Mermaid architecture diagram,
`pytest` se 5–10 tests (guardrails + routing), Streamlit Cloud par deploy.

---

## 7. Rubric compliance — mam ke section 5 se 9 tak

**Jawab: Nahi, abhi requirements fulfill nahi hoti. Changes ki need hai — sirf polish nahi,
core banana hai.** Total 33 checkable items mein se **5 pass**, 10 partial, 18 fail.

### Section 5 — Project 7 definition (6 items: 2 pass)

| Requirement | Status | Wajah |
|---|---|---|
| Pehle 6 projects se substantially different | ✅ | Telegram bot / email agent se bilkul alag domain — civic complaint routing. Ye aap ki strength hai |
| Student problem, users, workflow, agent roles, data sources, expected output define kare | ⚠️ | Code mein implied hai, magar kahin *documented* nahi (README missing) |
| Course ke multiple concepts combine kare | ❌ | LangGraph, RAG, tools, LangSmith — ek bhi nahi. Sirf Streamlit + SQLite |
| Existing GitHub repo / tutorial ka copy na ho | ✅ | Code original lagta hai, custom CSS aur schema aap ka apna |
| Complete, working, **production-oriented Agentic AI workflow** demonstrate kare | ❌ | Koi agentic workflow mojood nahi — `if keyword in text` hai |
| Same GitHub repo mein Project 7 ke tor par add ho | ❌ | Folder git repo hi nahi hai |

### Section 6 — Technologies & Concepts (9 rows: 1 pass)

Detail section 2 ki table mein hai. Summary: sirf **Streamlit** ✅.
Python version ⚠️ (aap 3.14 par hain — `chromadb` aur `sentence-transformers` wahan abhi
reliably build nahi hote, **3.12 recommended**). LLMs, LangChain/LangGraph, ReAct/Tool-calling/
Agentic RAG/Multi-agent, Playwright/SendGrid/Pushover, LangSmith — sab ❌.
Chroma ⚠️ (collections ban jate hain magar `.add()` kabhi call nahi hota → hamesha khaali).
Pydantic ⚠️ (18 models likhe hain, koi LLM unhe fill nahi karta). Guardrails ⚠️ (sirf `len < 10`).

### Section 7 — Production-Level Expectations (10 items: 2 pass)

| Requirement | Status | Wajah |
|---|---|---|
| Clear problem solve kare, sirf technology demo na ho | ✅ | Ye aap ka sab se strong point hai — real Pakistani municipal problem |
| Appropriate agent architecture + **explain why selected** | ❌ | Architecture hi nahi, is liye justification bhi nahi |
| Meaningful error handling aur validation | ❌ | 40+ `except Exception: pass` — errors chup chaap gayab |
| API keys env vars mein, credentials never committed | ⚠️ | `.env` use hoti hai (achha) magar `.gitignore` nahi → push par leak. Filhal keys khaali hain to nuksan nahi hua |
| Structured outputs jahan predictable data chahiye | ⚠️ | Schemas ready, wiring missing |
| Functional Streamlit UI | ✅ | 1847 lines, 3 portals — requirement se zyada |
| Clear README: setup, architecture, technologies, usage examples | ❌ | README file mojood nahi |
| Screenshots ya short demonstration | ❌ | Nahi |
| Code organized, readable, reusable | ⚠️ | Naming achhi, magar 3 modules dead code + `app.py` monolith + SLA logic 2 jagah duplicate |
| Instructor kisi bhi part ko explain karne ko keh sakti hai | ⚠️ | **Yahan sab se bara risk** — `orchestrator_pipeline.py` khol ke "agent kahan hai?" ka jawab mushkil |

### Section 8 — Originality & Academic Integrity (3 items: 2 pass, 1 risk)

Plagiarism ka masla **nahi** hai — code aap ka apna lagta hai, downloaded project nahi. ✅
Lekin ek risk hai: UI par likha hai "AI Agents Active: 6", "System Health 99.8%",
"Avg Routing SLA 1.4s", aur Telemetry ke saare charts hardcoded arrays se bante hain
(`latency = [0.62, 0.78, ...]`). Keyword matching ko "5 AI Agents" kehna aur fake metrics ko
real dikhana — ye "students must understand and be able to explain their own code" clause ke
neeche awkward situation ban sakti hai. Ya inhe real karein, ya UI par "Simulated" label lagayein.

### Section 9 — Submission Checklist (9 items: 0 confirmed pass)

Ek public GitHub repo ❌ (git init hi nahi hua) • Projects 1–7 separate folders mein ❓ (main sirf
ye folder dekh saka) • Project 7 as final project ❌ • Har project ka README ❌ • Apps publicly
accessible/published ❌ (Streamlit Cloud par deploy nahi) • Keys remove before publishing
⚠️ (`.gitignore` pehle banayein) • Repo link Classroom par share ❓ • Attendance ❓ • Har project
explain karne ke liye tayyar ❓

Ek chhoti magar zaroori cheez: folder ka naam **"no name"** hai aur `C:\xampp\htdocs` ke andar
para hai. Repo ke liye isko `civicflow-ai` rename kar ke projects folder mein shift karein.

### Pass hone ka minimum bar

Agar waqt bohot kam hai, ye 7 cheezein *lazmi* hain (baqi sab optional):
real Groq LLM + LangGraph StateGraph + Pydantic structured outputs + `guardrails.py` +
README.md + .gitignore + git repo & deploy. Ye `ARCHITECTURE_PLAN.md` ka **Phase 1** hai,
takreeban ek din ka kaam.

### Aap ki strength (ise zaya na karein)

Section 7 ka pehla bullet — "solve a clear problem rather than only demonstrate a technology" —
90% students yahan kamzor hote hain, aap yahan sab se strong hain. Domain, 3 role portals,
SLA concept, HITL page, feedback loop: ye sab *soch* ke banaye gaye hain. Kuch bhi delete karne
ki zarurat nahi. Sirf peechhe se fake engine nikaal ke real agentic engine daalni hai —
UI waisi hi rehti hai, bas usmein asli data behta hai.
