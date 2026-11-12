# Policy Assistant – AI-Powered Policy Intelligence System

An intelligent Policy Assistant designed to simplify policy discovery, understanding, and information retrieval using Generative AI and Retrieval-Augmented Generation (RAG).



## Overview

Policy Assistant enables users to interact with policy documents through natural language questions. Instead of manually searching lengthy documents, users can upload policy files and receive relevant, context-aware responses based on the document content.

The system aims to make policy information more accessible, searchable, and easier to understand.

## Key Features

- **Document Upload:** Upload policy documents for processing.
- **RAG-Based Question Answering:** Retrieve relevant information from uploaded documents.
- **Context-Aware Responses:** Generate answers grounded in retrieved policy content.
- **AI-Powered Interaction:** Ask questions using natural language.
- **Authentication:** Secure user access.
- **Admin Interface:** Dedicated administrative functionality.
- **Policy Knowledge Retrieval:** Search relevant information from the indexed policy documents.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React.js, Vite |
| Backend | Python, FastAPI |
| AI Integration | Gemini API |
| RAG Framework | Retrieval-Augmented Generation |
| Vector Database | ChromaDB |
| Embeddings | Sentence Transformers |
| Authentication | JWT |
| Database | SQLite |

## Project Structure

```text
policy-assistant/
│
├── backend/
│   ├── app/
│   ├── data/
│   │   └── chroma/
│   ├── scripts/
│   ├── .env
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api.js
│   │   ├── App.jsx
│   │   ├── auth.jsx
│   │   └── config.js
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Sathvika2955/Policy-Assistant.git
cd Policy-Assistant
```

### 2. Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the environment variables using your `.env.example` file.

Add the required API keys and application configuration.

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Configure the frontend environment variables using `.env.example`, if required.

Start the development server:

```bash
npm run dev
```

## Application Workflow

1. User authenticates with the application.
2. Policy documents are uploaded.
3. Documents are processed and divided into smaller chunks.
4. Embeddings are generated for semantic retrieval.
5. Relevant document chunks are retrieved based on the user's question.
6. The AI model generates a context-aware response using the retrieved information.
7. The user receives the response through the chat interface.

## Security Considerations

- API keys and secrets are stored in environment variables.
- Sensitive configuration files are excluded from version control.
- Authentication is implemented using JWT.
- Access to administrative functionality is role-based.

## Future Enhancements

- Support for additional policy document formats.
- Improved semantic search and retrieval accuracy.
- Source citations and document-level references.
- Enhanced response evaluation and hallucination reduction.
- Improved user experience and administrative analytics.

## Project Status

**Development in Progress**


---

**Developed by:** Sathvika Nidadavolu

**GitHub:** [Sathvika2955](https://github.com/Sathvika2955)