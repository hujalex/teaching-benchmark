Build a teaching quality verifier for a reinforcement learning environment.

The verifier scores how well a model explains a concept from a textbook page.
It takes a source markdown page and a model completion as input and returns 
a composite float score between 0 and 1.

## Input

The verifier receives:
- `source_text`: raw markdown string of a textbook page
- `completion`: the model's explanation of the concept
- `kg`: a knowledge graph dict extracted from the source page containing:
  - `concepts`: list of dicts with `concept_id`, `canonical`, `surface_forms`
  - `prerequisite_edges`: list of dicts with `concept`, `prereq`, `confidence`, `signal`

## Metrics to implement

Implement each metric as a private method. All methods take `source_text`, 
`completion`, and `kg` as needed. Each returns a float in [0, 1].

### 1. Concept Coverage (weight: 0.20)
- Extract all surface forms for each required concept from kg["concepts"]
- Check whether each surface form appears in the completion (case-insensitive)
- Score = concepts mentioned / total concepts
- Use string matching only, no embeddings

### 2. Sentence Coverage (weight: 0.20)
- Split source_text and completion into sentences
- Encode both with SentenceTransformer("all-MiniLM-L6-v2")
- For each source sentence find max cosine similarity to any completion sentence
- Score = mean of per-source-sentence max similarities

### 3. Contradiction Detection (weight: 0.15)
- Split source_text into sentences
- Split completion into sentences  
- Use CrossEncoder("cross-encoder/nli-deberta-v3-small") to score all pairs
- NLI label mapping: entailment=1.0, neutral=0.5, contradiction=0.0
- Score = mean of max per-source-sentence NLI scores across completion sentences
- Batch all pairs in a single model call

### 4. Entailment Chain (weight: 0.15)
- Split completion into sentences
- Use same CrossEncoder as metric 3 — do not load it twice
- Score consecutive sentence pairs (sentence[i], sentence[i+1])
- NLI label mapping: entailment=1.0, neutral=0.5, contradiction=0.0
- Score = mean across all consecutive pairs
- Batch with contradiction pairs in a single model call

### 5. Prerequisite Order (weight: 0.10)
- Use kg["prerequisite_edges"], filter to confidence == "high" only
- Find first mention position of each concept in completion using surface_forms
- For each edge (concept, prereq): violation if prereq appears after concept
- Score = 1 - (violations / total high confidence edges)
- Return 1.0 if no high confidence edges exist

### 6. Coherence Scoring (weight: 0.08)
- Use spacy en_core_web_sm
- Unresolved pronoun ratio: count pronouns without clear antecedents using coreferee
- Discourse connective density: count sentences containing connectives
  ("therefore", "however", "because", "thus", "hence", "consequently", 
  "this means", "as a result")
- Score = 0.6 * pronoun_score + 0.4 * connective_score

### 7. Example Grounding (weight: 0.07)
- Detect example sentences using markers:
  ("for example", "e.g.", "consider", "suppose", "imagine", "such as")
- For each example sentence check if it contains:
  - A number (token.like_num in spacy)
  - A named entity (doc.ents)
  - Inline code (regex: `[^`]+` or \d+)
- Score = grounded examples / total example sentences
- Return 0.0 if no example sentences found

### 8. Information Density (weight: 0.03)
- Use spacy POS tags
- Content POS: NOUN, VERB, ADJ, ADV
- Score per sentence = content tokens / total tokens
- Score = mean across all sentences

### 9. Readability Curve (weight: 0.02)
- Use textstat.flesch_kincaid_grade() per sentence
- Score = proportion of consecutive sentence pairs where grade increases
- Score = increasing pairs / (total sentences - 1)
- Return 1.0 if fewer than 2 sentences

## Architecture requirements

- Class name: TeachingVerifier
- Inherits from BaseVerifier with method signature:
  verify(self, prompt: str, completion: str, metadata: dict) -> float
- metadata contains: topic (str), used to look up kg from self.kg_index
- Load all models in __init__ — never inside verify() or metric methods
- Load knowledge graph dataset from HuggingFace path passed to __init__
- Batch all NLI calls for metrics 3 and 4 into a single CrossEncoder.predict() call
- Store WEIGHTS as a class-level constant dict
- Each metric method logs its score via self._log()
- verify() returns the composite float only

## Dependency installs required (include as a comment block at top of file)

spacy, coreferee, en_core_web_sm, keybert, sentence-transformers, 
networkx, nltk, textstat, datasets

## File structure

Multi-file: one per each metric
Include a __main__ block that runs a smoke test with a hardcoded 
source page and completion and prints all sub-scores and composite