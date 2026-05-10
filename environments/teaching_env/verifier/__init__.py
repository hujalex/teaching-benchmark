# Intentionally empty — importing this package must NOT pull in heavy ML
# dependencies (sentence-transformers, spacy, etc.) so that
# `import teaching_env` stays cheap. Import concrete modules directly:
#   from verifier.teaching_verifier import TeachingVerifier
#   from verifier.base import clean_source
