'''Training code for the learned syllabifiers in learned.py.

Requires the train dependency group (scikit-learn and a local celex
checkout next to this repository, with the licensed CELEX data):

    uv sync --group train

Train both models and report evaluation with:

    .venv/bin/python -m dutch_syllabifier.training
'''
