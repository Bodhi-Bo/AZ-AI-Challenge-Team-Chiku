# Chiku — Personal Executive Assistant 🧠✨

![Status](https://img.shields.io/badge/Status-Semi%20Finalist-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Azure%20AI%20Challenge-purple)

> **A compassionate AI executive assistant designed specifically for neurodivergent individuals with ADHD**

Chiku combines intelligent task decomposition, smart calendar integration, and natural voice/text interaction to help people with ADHD manage their time and tasks with less cognitive load and more emotional support.

---

## 🎯 The Problem

**92%** of people with ADHD struggle with memory and concentration
**83%** have difficulties with organizational skills
**78%** face challenges with time management

Existing solutions fall short:

- **Generic tools** (Google Calendar, Todoist) don't break down overwhelming tasks
- **ADHD-specific apps** lack intelligent scheduling and task decomposition
- **No tool combines** conversation, decomposition, and calendar management

---

## 💡 Our Solution

**Chiku** is your personal executive assistant that:

- 🧩 **Breaks Down Tasks** — Converts overwhelming projects into atomic, actionable steps
- 📅 **Schedules Smartly** — Automatically finds time slots and creates calendar events
- 💬 **Talks Naturally** — Voice & text conversation for effortless task capture
- 💖 **Supports Compassionately** — Encouraging, non-judgmental, ADHD-aware communication
- 🧠 **Understands Context** — Considers energy levels, deadlines, and personal preferences

### What Makes Chiku Different

**Unlike other tools, Chiku:**

- Acts like a **coach** (breaking down tasks with guidance)
- Works like a **calendar** (scheduling intelligently with real-time availability)
- Follows through like a **friend** (compassionate reminders and celebrations)

---

## ✨ Key Features

### 🎤 Voice & Text Interaction

- Natural language processing for task capture
- ElevenLabs voice streaming for hands-free use
- Real-time WebSocket communication
- Seamless mode switching

### 🧩 Intelligent Task Decomposition

- Autonomous AI agent breaks complex tasks into subtasks
- Asks clarifying questions in efficient batches
- Considers cognitive load, energy levels, and dependencies
- Provides quick wins and break suggestions

### 📅 Smart Calendar Integration

- Automatic event creation from conversation
- Availability checking before scheduling
- Conflict detection and resolution
- Visual calendar with drag-and-drop support

### 💖 Compassionate Follow-ups

- Context-aware reminders
- Encouraging messages that adapt to progress
- Non-judgmental tone throughout
- Celebrates achievements, no matter how small

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│              Frontend (Next.js + TypeScript)            │
│  Voice UI │ Chat Interface │ Calendar Widget            │
└──────────────────────┬──────────────────────────────────┘
                       │ WebSocket
┌──────────────────────┴──────────────────────────────────┐
│            Backend (FastAPI + Python)                   │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │        ReAct Orchestrator Agent                │    │
│  │  • Intent classification                       │    │
│  │  • Tool selection & parallel execution         │    │
│  │  • State management                            │    │
│  └────┬───────────────────────────────────────────┘    │
│       │                                                 │
│  ┌────┴──────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │  Decomposer   │  │  Calendar   │  │  Reminders   │ │
│  │     Agent     │  │   Manager   │  │  & Queries   │ │
│  └───────────────┘  └─────────────┘  └──────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────┐
│         Data Layer (MongoDB + Redis)                    │
│  Events │ Reminders │ Messages │ State │ LLM Pool       │
└─────────────────────────────────────────────────────────┘
```

### Multi-Agent AI System

**ReAct Orchestrator** — The "brain" that:

- Classifies user intent
- Selects and executes tools in parallel
- Maintains conversation context
- Manages emotional awareness

**Decomposer Agent** — The "planner" that:

- Breaks complex tasks into subtasks
- Asks efficient batch questions
- Considers ADHD-specific factors (energy, breaks, quick wins)
- Uses world knowledge for realistic planning

**Tool Architecture** — 20+ specialized tools for:

- Calendar operations (query, create, update, delete)
- Availability checking and slot finding
- Reminder management
- State tracking and conversation flow
- User messaging

---

## 🛠️ Tech Stack

| Layer              | Technologies                                                 |
| ------------------ | ------------------------------------------------------------ |
| **Frontend**       | Next.js 14, TypeScript, Tailwind CSS, Framer Motion, Zustand |
| **Backend**        | FastAPI, Python 3.11+, LangGraph, LangChain                  |
| **AI/LLM**         | OpenAI GPT-4o, Function Calling, ElevenLabs Voice API        |
| **Database**       | MongoDB (Beanie ODM), Redis (caching + key pool)             |
| **Infrastructure** | Azure, Docker, WebSocket, OAuth 2.0                          |

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- MongoDB (local or Atlas)
- Redis (local or cloud)
- OpenAI API key (GPT-4o access)
- ElevenLabs API key (optional, for voice)

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and database URLs

# Seed OpenAI key pool (if using)
python app/seeds/openai_key_seed.py

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: `http://localhost:8000`
API docs: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install  # or npm install / yarn install

# Configure environment
cp .env.example .env.local
# Edit .env.local with backend URL and API keys

# Start dev server
pnpm dev  # or npm run dev / yarn dev
```

Frontend runs at: `http://localhost:3000`

### Verify Installation

```bash
# Check backend health
curl http://localhost:8000/api/health

# Open frontend
open http://localhost:3000

# Test chat: "What's on my schedule today?"
```

---

## 📖 Usage Examples

### Text Conversation

```
You: "I need to study for my biology exam next week"

Chiku: "I can help you prepare! Let me gather some info:

1. What's the exact date and time of your exam?
2. Which topics or chapters will it cover?
3. How confident do you feel with the material (1-10)?

You can answer all at once!"

You: "Next Tuesday at 2 PM, chapters 5-8, I'm at a 6"

Chiku: "Got it! Here's a realistic study plan:

Quick Wins:
• Organize notes (10 min)
• Create flashcards (15 min)

Study Blocks:
1. Review Chapter 5 (45 min) — Tomorrow 9 AM
2. Practice problems (30 min) — Tomorrow 3 PM
...

Want me to schedule these on your calendar?"
```

### Voice Interaction

```
[Activate voice mode]

You: "What do I have today?"

Chiku: "Let me check... You have three things:
1. Team meeting at 2 PM for an hour
2. Dentist at 4:30 PM for 30 minutes
3. Dinner plans at 7 PM"

You: "Move the meeting to 3 PM"

Chiku: "Done! I've moved your team meeting to 3 PM.
Your schedule is all set!"
```

---

## 📡 API Overview

### REST Endpoints

- `GET /api/health` — Health check
- `GET /api/events/{user_id}/range` — Get calendar events
- `GET /api/reminders/{user_id}/upcoming` — Get upcoming reminders
- `GET /api/messages/{user_id}` — Get chat history
- `POST /api/chat` — Legacy chat endpoint

### WebSocket

- `WS /api/ws/{user_id}` — Real-time chat connection

**Message Format:**

```json
// Client → Server
{ "type": "message", "text": "Schedule study time tomorrow" }

// Server → Client
{ "type": "response", "text": "Sure! How much time do you need?" }
```

---

## 📁 Project Structure

```
AZ-AI-Challenge-Team-Chiku/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI server
│   │   ├── config.py                  # Configuration
│   │   ├── agents/
│   │   │   ├── react/                 # ReAct orchestrator
│   │   │   └── decomposer/            # Task breakdown agent
│   │   ├── agent_tools/               # 20+ LangChain tools
│   │   ├── services/                  # Business logic
│   │   ├── models/                    # Data models
│   │   └── utils/                     # Utilities
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx                   # Main UI
│   │   └── api/                       # API routes
│   ├── components/
│   │   ├── chat/                      # Chat interface
│   │   ├── voice/                     # Voice UI
│   │   └── calendar/                  # Calendar widget
│   ├── hooks/                         # React hooks
│   └── lib/
│       ├── stores/                    # Zustand state
│       └── api/                       # API clients
│
└── README.md
```

---

## 🔮 Roadmap

### Phase 1 (Q1 2026)

- [ ] Google Calendar OAuth integration
- [ ] Mobile app (iOS + Android)
- [ ] Habit tracking
- [ ] Energy level tracking

### Phase 2 (Q2 2026)

- [ ] Predictive scheduling
- [ ] Goal hierarchies
- [ ] Progress analytics
- [ ] Team collaboration

### Phase 3 (Q3 2026)

- [ ] Integrations (Todoist, Notion, Slack)
- [ ] Smart home integration
- [ ] Wearable support

### Phase 4 (Q4 2026)

- [ ] Clinical studies
- [ ] Multilingual support
- [ ] Open API for developers

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 Documentation

- **[Full Technical Documentation](CHIKU_PROJECT_DOCUMENTATION.md)** — Complete architecture guide
- **[Backend README](backend/README.md)** — Backend-specific docs
- **[Frontend README](frontend/README.md)** — Frontend-specific docs
- **[API Documentation](http://localhost:8000/docs)** — Interactive API docs (when running)

---

## 🙏 Acknowledgments

### Technologies

- OpenAI — GPT-4o language model
- LangChain & LangGraph — Agent framework
- ElevenLabs — Voice synthesis
- Microsoft Azure — Cloud platform
- MongoDB & Redis — Data storage

### Inspiration

- ADHD community feedback and lived experiences
- Neurodiversity-affirming design principles
- Evidence-based productivity research

### Special Thanks

- Azure AI Challenge organizers
- Beta testers who provided invaluable feedback
- ADHD advocacy organizations for guidance

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 📞 Contact

- **GitHub:** [github.com/Bodhi-Bo/AZ-AI-Challenge-Team-Chiku](https://github.com/Bodhi-Bo/AZ-AI-Challenge-Team-Chiku)
- **Issues:** [github.com/Bodhi-Bo/AZ-AI-Challenge-Team-Chiku/issues](https://github.com/Bodhi-Bo/AZ-AI-Challenge-Team-Chiku/issues)
- **Email:** [your-email@example.com]

---

<div align="center">

**Built with ❤️ for the neurodivergent community**

_"Executive function support shouldn't feel like another task.
With Chiku, it feels like having a compassionate friend by your side."_

⭐ **If Chiku helps you, please star this repo!** ⭐

</div>
