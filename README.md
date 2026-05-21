# 🔬 Deep Research Agent v1

An autonomous research agent that takes a topic, searches the web, reads pages, 
builds a knowledge base, and produces a structured research report with citations 
and self-reflection.

## 🧠 Skills Demonstrated

| Skill | Implementation |
|---|---|
| **ReAct** | `agent/research_agent.py` — Thought → Action → Observation loop |
| **Tools** | Web search (DuckDuckGo) + Page reader + RAG store |
| **Memory** | Findings, visited URLs, ReAct steps all tracked in `ResearchMemory` |
| **RAG** | Research findings embedded in ChromaDB for semantic retrieval during writing |
| **Structured Output** | Pydantic `ResearchReport` with typed sections, citations, scores |
| **Reflection** | Agent self-critiques its own report and scores it 1-10 |

## 🔄 How It Works

```
User gives topic
      ↓
[ReAct Loop]
  Thought → what to search next?
  Action  → web_search("query")
  Observe → 5 results returned
  
  Thought → which page to read?
  Action  → read_page("url")
  Observe → page content extracted + summarized + stored in RAG
  
  ...repeat until 3+ sources gathered...
  
  Action  → synthesize()
      ↓
[Report Generation]
  RAG retrieval per section → Gemini writes each section with citations
  Executive summary + key findings synthesized
      ↓
[Reflection]
  Agent scores own report: coverage, depth, citations, clarity
      ↓
[Output]
  report.md + report.html + report.json saved to reports/
```

## 📁 Project Structure

```
deep-research-agent/
├── .env                          # GEMINI_API_KEY
├── main.py                       # Entry point
├── requirements.txt
├── agent/
│   ├── research_agent.py         # ReAct loop orchestrator
│   ├── memory.py                 # Research memory (findings + steps)
│   └── reflection.py             # Self-critique module
├── tools/
│   ├── web_search.py             # DuckDuckGo search (free, no key)
│   ├── page_reader.py            # Web page text extraction
│   └── rag_store.py              # ChromaDB in-memory RAG store
├── output/
│   └── structured_report.py      # Pydantic report models + HTML/MD export
└── reports/                      # Generated reports saved here
```

## 🚀 Setup & Run

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Gemini API key
echo GEMINI_API_KEY=your-key-here > .env

# 4. Run
python main.py
```

## 📄 Sample Output

```
🔬 DEEP RESEARCH AGENT v1
Topic: The impact of large language models on software engineering

[Step 1]
  💭 Thought: I should start with a broad overview search...
  🔧 Action : web_search("LLMs impact software engineering 2024")
  👁️  Observe: Found 4 results...

[Step 2]
  💭 Thought: Let me read the most relevant page...
  🔧 Action : read_page("https://...")
  👁️  Observe: Read 'GitHub Copilot Study': AI coding tools increase...

...

  📝 Generating structured report...
  🔍 Self-reflecting on report quality...
  📊 Reflection score: 7.8/10

📋 RESEARCH REPORT SUMMARY
  Sources  : 4
  Sections : 5
  Citations: 4
  Score    : 7.8/10
```

## 🔧 Technical Notes

- **API**: Gemini API (substituted for OpenAI — identical architecture)
- **Embeddings**: `gemini-embedding-001` via ChromaDB in-memory store
- **Web search**: DuckDuckGo lite (free, no API key required)
- **Report formats**: Markdown + HTML + JSON

## 📚 References

- [ReAct Paper — Yao et al. 2022](https://arxiv.org/abs/2210.03629)
- [Reflexion Paper — Shinn et al. 2023](https://arxiv.org/abs/2303.11366)
- [Anthropic — Building Effective Agents](https://docs.anthropic.com)
- [NirDiamant/GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents)

## 👨‍💻 Author

**Jubelin Joji** — Agentic AI Internship Week 2 Project
