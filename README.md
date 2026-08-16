# Home Lens

**Understand whether a house truly fits your family—not just your search filters.**

Home Lens is a Streamlit project that looks up one US property by
address and compares it with a buyer's stated preferences. It returns a structured,
explainable recommendation rather than a free-form chatbot answer.

## Problem statement

Property listings expose facts but do not explain how those facts relate to a
specific family's budget, commute, space, maintenance tolerance, and must-have
features. This application organizes those tradeoffs while keeping unknown facts
visible.

## API-enhanced scope

> Property information is manually entered in the Week 1 MVP so the project can focus on LangChain, prompt engineering, structured output, and explainable AI recommendations. Automatic listing-data retrieval is intentionally deferred to a future iteration.

The project now includes the originally deferred API enhancement because it greatly
reduces manual entry. RentCast retrieves public property records and any matching
sale listing from a full US address. Returned values remain editable and must be
reviewed. The optional listing URL is still reference text only and is never opened
or scraped. This project has no agents, RAG, database, Zillow integration, or web
scraping.

## Features

- Buyer-preference and property-information forms
- RentCast address lookup that prefills available property details
- Deterministic mortgage, ownership-cost, and upfront-cash estimate
- Fictional sample property for demonstrations
- Input validation before any model request
- A 0–100 fit score and one of three recommendations
- Matching features, unmet needs, risks, and missing facts
- Exactly five questions for the listing agent
- Explicit assumptions and responsible-AI disclaimer
- Session-state preservation across Streamlit reruns
- Friendly handling of missing credentials and common OpenAI errors

## Application workflow

```text
Property address → RentCast API → Editable property form
                                  +
Buyer preferences                 
        +
Reviewed property information
        ↓
LangChain ChatPromptTemplate
        ↓
ChatOpenAI
        ↓
Pydantic structured output
        ↓
Streamlit recommendation
```

## Architecture

```text
app.py                 Streamlit form and result presentation
property_lookup.py     RentCast lookup and response normalization
mortgage_calculator.py Standard amortization and itemized cost calculations
validation.py          Deterministic input validation
home_analysis_chain.py Prompt, ChatOpenAI configuration, and LCEL chain
models.py              Pydantic output contract
tests/                 Unit tests with no live model requests
```

The UI assembles plain Python dictionaries. Validation rejects incomplete or
invalid values before `home_analysis_chain.py` sends them to the model. The model
response must pass the `HomeAnalysis` Pydantic schema before it reaches the UI.

## LangChain implementation

`home_analysis_chain.py` uses supported package-level imports:

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
```

`ChatOpenAI` is configured with a low temperature, a 45-second timeout, and two
retries. `with_structured_output(HomeAnalysis)` asks the model provider to return
the required schema. The application never manually parses a free-form answer.

## ChatPromptTemplate

The prompt has two separate messages:

- The **system message** establishes the impartial role, evidence boundaries,
  relevant decision criteria, and responsible-AI restrictions.
- The **human message** supplies clearly labeled `BUYER PROFILE`,
  `PROPERTY INFORMATION`, `KNOWN CONCERNS`, and `ANALYSIS REQUEST` sections.

The form data is serialized into readable JSON within the human message. That
makes each supplied fact explicit and keeps the prompt easy to explain.

## LangChain Expression Language

LangChain Expression Language (LCEL) connects compatible components using `|`:

```python
structured_llm = llm.with_structured_output(HomeAnalysis)
analysis_chain = prompt | structured_llm
```

The formatted prompt flows into the structured model, and the chain returns a
validated `HomeAnalysis` instance.

## Pydantic structured output

`HomeAnalysis` is the response contract. Pydantic enforces:

- A fit score from 0 through 100
- `Strong Fit`, `Consider`, or `Not Recommended`
- Exactly five listing-agent questions
- Named lists for fits, unmet preferences, risks, missing information, and assumptions
- A final explanation and disclaimer

If the model cannot satisfy this contract, the UI reports a structured-output
error instead of showing unreliable partial data.

## Mortgage and ownership-cost estimate

The mortgage calculator is deterministic and does not use an LLM. It applies the
standard fixed-rate amortization formula and itemizes principal and interest,
property tax, homeowners insurance, HOA, PMI when the down payment is below 20%,
and an optional maintenance reserve. It also estimates closing costs and cash
needed before closing. All rates and costs are editable assumptions, not quotes.

## Prompt-engineering approach

The prompt uses five core techniques:

1. **Role** — an impartial research assistant, not a salesperson.
2. **Evidence boundary** — only user-supplied facts may be used.
3. **Decision criteria** — price, space, age, recurring costs, schools, commute,
   maintenance, and must-have features are named explicitly.
4. **Uncertainty handling** — unknowns and assumptions receive separate fields.
5. **Safety boundaries** — no protected-characteristic inference, demographic
   assumptions, appreciation guarantees, or professional-advice claims.

## Technology stack

- Python 3.11+
- Streamlit
- LangChain and LangChain Core
- LangChain OpenAI integration
- OpenAI Python SDK
- Pydantic
- python-dotenv
- pytest
- uv for dependency management and reproducible environments

## Local setup with uv

Prerequisite: install [uv](https://docs.astral.sh/uv/getting-started/installation/).
The repository selects Python 3.12 through `.python-version`; uv can download that
version automatically when it is not already installed.

```bash
cd /path/to/HomeLens
uv sync --locked
cp .env.example .env
```

`uv sync --locked` creates and manages `.venv` from `pyproject.toml` and
`uv.lock`. Activating the virtual environment or running `pip install` is not
required.

Edit `.env` and add your own OpenAI API key and model:

```text
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1-mini
RENTCAST_API_KEY=your_rentcast_api_key_here
```

Never commit `.env`. It is already excluded by `.gitignore`.

## Replit setup

1. Create a new **Python** Repl.
2. Upload all project files, including `pyproject.toml`, `uv.lock`,
   `.python-version`, and the `tests` folder.
3. In Replit **Shell**, install uv if the `uv` command is unavailable:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

4. Install the locked project environment:

   ```bash
   uv sync --locked
   ```

5. Open **Tools → Secrets** and create:

   - `OPENAI_API_KEY` with your API key
   - `OPENAI_MODEL` with `gpt-4.1-mini` or another model that supports structured output
   - `RENTCAST_API_KEY` with your RentCast API key

6. Set the Replit Run command to:

   ```bash
   uv run --locked streamlit run app.py --server.address 0.0.0.0 --server.port 3000
   ```

7. Select **Run** and open the web preview.

Do not upload a local `.env` file to Replit or paste a key into source code.

## Environment variables

| Variable | Required | Purpose |
|---|---:|---|
| `OPENAI_API_KEY` | Yes | Authenticates model requests |
| `OPENAI_MODEL` | No | Model name; defaults to `gpt-4.1-mini` |
| `RENTCAST_API_KEY` | Yes for lookup | Retrieves property and sale-listing data by address |

The selected model must support structured output through `ChatOpenAI`.

## Run the application

```bash
uv run --locked streamlit run app.py
```

Then open the local URL printed by Streamlit, normally
`http://localhost:8501`.

Run automated checks with:

```bash
uv run --locked pytest
uv run --locked python -m compileall app.py home_analysis_chain.py models.py validation.py tests
```

## Sample demonstration

1. Enter a full US address and select **Look Up Property**, or select
   **Load Sample Property** for a credential-free form demonstration.
2. Review and correct the populated fields. Add any values the API could not
   provide, especially school rating, commute, known concerns, and buyer preferences.
3. Point out the fictional-sample notice and manual-entry MVP notice.
4. Select **Analyze Property**.
5. Explain how validation runs before the model.
6. Walk through the recommendation, score, supporting evidence, unknowns,
   questions, assumptions, mortgage breakdown, final assessment, and disclaimers.

The sample represents no real or currently available property. A successful live
analysis requires a valid OpenAI key, API access, and model access.

## Responsible-AI considerations

- The model may use only information the user supplied.
- Missing facts must remain missing rather than being inferred.
- Assumptions are visibly separated from facts.
- The prompt prohibits conclusions based on protected characteristics and
  neighborhood-demographic inference.
- The application provides no guarantees about appreciation, returns, safety,
  school outcomes, or future conditions.
- The result is informational—not financial, legal, appraisal, inspection,
  mortgage, or real-estate advice.
- Buyers should independently verify listing claims and consult qualified
  professionals before making a decision.

## Current limitations

- API information may be incomplete, delayed, or inaccurate and is not independently verified.
- A lookup uses two RentCast requests: one property record and one sale listing.
- Some fields, including school rating, commute, and known concerns, still require review or entry.
- Only one property is analyzed at a time.
- The score is an AI judgment, not an appraisal or deterministic financial model.
- Model output may vary between requests despite the low temperature.
- No listing documents, images, inspection records, comparable sales, or live data
  are analyzed.
- A valid OpenAI credential and network connection are required for analysis.
- Mortgage results are educational estimates and exclude lender-specific fees,
  utilities, and costs not entered by the user.

## Future roadmap

- **Week 1:** Analyze one manually entered property using LangChain
- **Week 2:** Retrieve property details through a documented property-data API
- **Week 3:** Add property documents and RAG
- **Week 4:** Add specialized agents and compare two or three properties
- **Week 5:** Add evaluations, scoring consistency, and guardrails
- **Week 6:** Polish the application and prepare the final presentation

Future features should preserve the Week 1 evidence, uncertainty, privacy, and
responsible-AI boundaries.
