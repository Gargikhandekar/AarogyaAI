# Interview notes: Aarogya AI

Notes for explaining the project: the design decisions, what the evaluation showed, and
likely questions.

## The 30-second pitch

"Aarogya AI is a retrieval-augmented medical Q&A assistant over MedQuAD, 16k NIH
question-answer pairs. It retrieves the most relevant passages, has a local Llama 3.1 or
Qwen2.5 model answer **only** from them with numbered citations, and **declines** when
retrieval finds nothing relevant. I evaluated it on held-out MedQuAD questions: retrieval
finds the right topic about 90% of the time, and the relevance gate keeps 95% of medical
questions while declining 90% of off-topic ones. The stack is FastAPI, LangChain and React,
with tests and CI."

## One question end to end (with file pointers)

1. **Frontend:** `frontend/src/hooks/useChat.ts` posts to `/api/chat/stream` and reads
   server-sent events.
2. **API:** `backend/app/api/chat.py:71` (`chat_stream`). It's a plain `def`, so FastAPI runs
   it in a thread pool; retrieval, SQLite and the Ollama client are all blocking.
3. **Service:** `services/chat_service.py` (`prepare_stream_chat`). It checks the knowledge
   base is loaded (503 otherwise), runs emergency detection (`utils/helpers.py:128`), and saves
   the user message.
4. **Retrieve:** `rag/pipeline.py:100` (`plan`) calls `retrieve` (top-4 chunks with cosine
   scores) → `is_relevant` (top score ≥ 0.45?) → checks Ollama health.
   - Not relevant → decline. Ollama down → quoted passages (`_fallback`).
5. **Stream:** the API sends a `meta` event with the sources. `pipeline.stream` yields LLM
   tokens from the LangChain chain `RAG_PROMPT | ChatOllama | StrOutputParser`.
6. **Finalise:** `finalize` checks whether the model refused, and parses which `[n]` it cited
   (`prompts.py:44`). The answer is saved and a `done` event carries the final sources.

Indexing happens once at startup (`initialize`):
- **Load:** `documents.py` loads the JSON and splits answers with
  `RecursiveCharacterTextSplitter`.
- **Index:** `retrievers.py` builds TF-IDF, or FAISS when `RETRIEVER=faiss`.

## Design decisions and why

| Decision | Why | Trade-off |
|---|---|---|
| **Local LLM via Ollama** | Health questions are sensitive. No data leaves the machine, no API cost, and it works offline. | 7–8B models are weaker than hosted ones and slow on CPU. |
| **LangChain for the plumbing only** (prompt template, splitter, `ChatOllama`, FAISS store) | Standard, swappable components. Switching Ollama to another provider changes one function. | I kept the control flow (gate, fallback, citations) in plain Python so it's easy to read and test. A LangChain "agent" would hide it. |
| **TF-IDF default, FAISS optional** | TF-IDF needs no 1–2 GB PyTorch download, starts in seconds, is fully explainable, and makes CI fast. FAISS + MiniLM handles synonyms. | TF-IDF misses paraphrases and can be fooled by rare words ("good morning" → "Good syndrome"). |
| **Inverted index in TF-IDF** | A query only scores chunks that share a term with it, instead of looping over all 54k chunks. Document norms are precomputed. | A bit more code than the naive loop. |
| **Stopwords** | Without them, "What is the capital of France?" matched medical answers on "what/is/the". This was the original bug: every off-topic question got a confident answer. | A fixed English list; domain words like "pain" are kept. |
| **Chunking: 500 chars, 50 overlap** | MedQuAD answers have a median of about 880 and up to 27,000 characters. Smaller chunks give more precise passages and fit more of them in the context. Chosen on the dev split: best topic@5 (0.97) and hit@5 (0.78). | Short leftover chunks at the end of an answer; more chunks to index. |
| **Index answers only, with a topic header** ("Glaucoma: …") | Indexing the questions would let eval questions match themselves verbatim (leakage). The header keeps mid-answer chunks on topic. | In production, matching against stored questions would help; see next steps. |
| **Two-layer decline** | Layer 1: the retrieval score gate skips the LLM entirely, which is cheap and deterministic. Layer 2: the prompt makes the model reply with a fixed sentence when the passages don't answer, and the code detects it. | Both can be wrong. Layer 2 relies on the model following instructions. |
| **Threshold 0.45, not the dev "optimum" 0.54** | A wrongly kept off-topic question still hits layer 2, but a wrongly declined medical question gets no second chance. So I chose a slightly lenient threshold: it keeps 39/40 dev questions and declines 9/10 off-topic ones. | It is specific to TF-IDF with 500-char chunks; recalibrate if either changes. |
| **Numbered citations `[n]`** | The user can check every claim against the NIH source; the UI links to it. | The code checks a citation points at a real passage, not that the passage supports the sentence (that's what the eval judge measures). |
| **Fallback to quoted passages when Ollama fails** | Fails visibly instead of a 500 or a silent change in behaviour. The note tells the user why. | The quoted text is less readable than a generated answer. |
| **Health check cached 30 s** | The old code cached "Ollama is down" forever, so starting Ollama after the API never took effect. The 30 s cache avoids a check on every request. | Up to 30 s before a recovery is noticed. A failed call marks Ollama down immediately. |
| **Timeouts: 5 s connect, 120 s read** | Connect fails fast when Ollama isn't running. The read timeout is per token gap, so long answers still stream. | 120 s is generous for slow CPUs. |
| **Emergency detection before RAG** | Safety first: a model must never "explain" chest pain to someone having a heart attack. Situational patterns need a personal or right-now cue, so general questions aren't blocked. | Regex. It errs towards false alarms ("can a baby have a seizure?"). |
| **SSE streaming** | Time to first token matters with local models. SSE is plain HTTP and works through nginx with buffering off. | One-way only, which is all chat needs. |
| **Tests with a fake LLM** | `FakeListChatModel` makes the tests deterministic and fast (4 s), with no Ollama in CI. | Real model behaviour is only covered by the eval script. |

## What the evaluation showed

Setup:
- **Data:** 40 MedQuAD test questions from 40 different documents, plus 10 off-topic questions.
- **Leakage control:** settings were tuned only on a separate dev split of the same shape.

Results (test split, TF-IDF):
- **Topic-level retrieval is good:** topic@5 = 0.90 at 500 chars. The right disease page is
  almost always retrieved.
- **The exact answer is harder:** hit@1 is about 0.3 and hit@5 = 0.62. Each disease has 5–10
  templated questions ("symptoms of X", "treatment of X") with overlapping answers, so the
  "Symptoms" passage often outranks the gold "What is X?" passage. For a chatbot this matters
  less than it sounds, because the passages it finds are usually still on topic.
- **Chunk size:**
  - On dev, 500-char chunks clearly beat 1000 and whole answers on topic recall (0.97 vs
    0.90). On test the differences are within noise (one question = 0.025).
  - The bigger lesson is that **scores shift with chunk size**: shorter chunks give higher
    cosine scores. So the decline threshold must be recalibrated whenever chunking changes.
- **Decline gate:** keeps 95% of in-domain test questions and declines 90% of off-topic ones.
  - **False keep:** "Translate 'good morning'" (lexical match to "Good syndrome").
  - **False declines:** "What is (are) Good syndrome?" and "Do you have information about
    Coping with Disasters".
  - The old threshold (0.15, never calibrated) declined at most 4 of 10 off-topic questions.
- **Not measured yet:** Llama 3.1 vs Qwen2.5 faithfulness, and the FAISS retriever. Both are
  one command away (`eval/README.md`). I wrote the judge pipeline and tested it with fake
  models, but I couldn't run the 8B models where this was built. **Say so if asked; don't
  quote numbers that weren't measured.**

## What I'd do next (in order)

1. **Run the LLM comparison** (faithfulness, citation rate, latency) and the FAISS eval, then
   calibrate `MIN_RELEVANCE_FAISS`.
2. **Hybrid retrieval:** BM25 + dense embeddings with reciprocal rank fusion, then a
   cross-encoder reranker on the top 20. That's the usual fix for both the lexical false
   matches and the exact-answer ranking problem.
3. **Index the questions as well,** and evaluate with *paraphrased* user-style questions
   (e.g. LiveQA-Med, which MedQuAD ships judgments for), not MedQuAD's own templates.
4. **Verify citations at answer time** with an NLI model: drop or flag sentences whose cited
   passage doesn't entail them.
5. **Chunking:** merge tiny trailing chunks; split on MedQuAD's section headings.
6. **Conversation memory:** rewrite follow-ups ("what about in children?") into standalone
   questions before retrieval.
7. **Production:** Postgres, a persistent vector store, request tracing, and feedback (👍/👎
   is already stored) feeding an eval set.

## 10 likely questions, with short answers

1. **Why RAG instead of fine-tuning?** Medical facts change and must be traceable. RAG lets me
   cite the source, update knowledge by re-indexing, and decline when there's no source.
   Fine-tuning bakes facts into weights with no citation and still hallucinates.

2. **How do you reduce hallucination?**
   - Retrieval gate (no relevant passage → no LLM call).
   - Prompt restricted to the numbered passages, with a mandatory citation per sentence.
   - A fixed refusal sentence the code detects.
   - Low temperature (0.1).
   - Offline: an LLM judge measures faithfulness.
   It's reduced, not eliminated; next step is NLI-based citation checking.

3. **How did you choose chunk size and top-k?** I evaluated 500, 1000 and whole-answer chunks
   on a dev split with hit@k and topic@k, and chose 500. Top-4 × 500 chars is about 600 tokens
   of context: enough recall without diluting the prompt for an 8B model with a 4k context.

4. **How did you set the decline threshold?** Scores of in-domain and off-topic dev questions
   overlap a little. I swept thresholds for balanced accuracy (optimum 0.54), then chose 0.45
   on purpose: a false keep still meets the LLM's refusal instruction, but a false decline
   loses a real answer.

5. **TF-IDF vs embeddings: when would you use which?**
   - TF-IDF: exact medical terms (rare disease names) and zero setup. It fails on synonyms and
     paraphrases.
   - Embeddings: handle meaning, but can blur specific drug or disease names.
   - In production: hybrid plus a reranker.

6. **How do you know the evaluation isn't leaking?**
   - Dev and test splits are disjoint, and settings were tuned only on dev.
   - Only answer text is indexed, so a test question can't match its own stored question.
   - One question per document, so a split isn't dominated by one topic.
   - Limitation: the questions are MedQuAD's templates, not real users.

7. **What's the weakness of LLM-as-judge here?** The judge is a small local model. It can be
   lenient, especially when judging its own family's output, and it isn't calibrated against
   human labels. I'd mitigate by using a different model as judge, spot-checking around 20
   verdicts by hand, and reporting agreement.

8. **What happens when Ollama is down or slow?**
   - Health is probed with a 2 s timeout and cached for 30 s.
   - If it's down, the user gets the top passages quoted verbatim with a warning.
   - Calls use a 5 s connect and 120 s read timeout. A failure mid-stream appends a "cut off"
     note, and a failure before the first token falls back.
   - `/api/health` reports "degraded" with the reason. Tests cover each of these paths.

9. **How does it handle emergencies and safety?**
   - Regex checks run before RAG: self-harm and breathing problems always trigger; other
     conditions need a personal or right-now cue.
   - Emergencies get local emergency numbers and helplines, and no LLM call.
   - The disclaimer is on every answer, and the prompt forbids diagnosing or prescribing.
   - Keyword matching misses unusual phrasings, so I'd add a small classifier.

10. **How would you scale this to many users?**
    - Run Ollama or vLLM on a GPU behind a queue, with several API workers.
    - Postgres instead of SQLite, and a vector DB (pgvector/Qdrant) instead of the in-process
      index.
    - Cache answers for frequent questions, and add rate limiting (already on, via SlowAPI)
      and tracing.
    - The retrieval and pipeline code doesn't change; only the components behind the
      interfaces do.

## Bugs found and fixed (good "tell me about a bug" stories)

- **Off-topic questions got confident wrong answers.** "What is glaucoma?" and "capital of
  France?" both returned the postpartum-depression answer. Causes: no stopwords and an
  uncalibrated threshold. Fix: stopwords, a calibrated gate, and the decline path. I measured
  the before/after on the eval set.
- **History, rename, delete and feedback endpoints returned 500.** The API called service
  functions that didn't exist.
- **"Ollama down" was cached forever.** Starting Ollama after the API had no effect until a
  restart.
- **Rate limiting was configured but never applied.** The SlowAPI middleware wasn't installed.
- **Informational questions triggered the emergency banner** ("what is a heart attack?"), and
  a typo ("analphylaxis") meant anaphylaxis never matched.
- **Docker and the frontend didn't build from a clean clone** (missing type files, a missing
  `vector_db/` folder), and the local database with user accounts had been committed.

_Note: the git history shows this refactor was done with an AI coding assistant (commits
are co-authored). Be upfront about that if asked. What matters is that you can explain
every decision above._
