# ELIZA - A Reconstruction of the 1966 Chatbot

This repository contains a didactic reconstruction of the ELIZA chatbot program in Python, based on Joseph Weizenbaum's original 1966 description (https://dl.acm.org/doi/10.1145/365153.365168).

## Files

- `weizenbaum_1966_appendix.txt` - Transcribed appendix from the 1966 paper 
- `to_json.py` - Script that processes the appendix and produces `eliza.json`
- `eliza.json` - Modern JSON representation of ELIZA's rules and responses
- `test_eliza.py` - Pytest tests based on a sample dialog between a user and ELIZA from the paper 
- `eliza.py` - Main ELIZA program using Python's `cmd` module

## Installation

This project uses pipenv for dependency management:

```bash
pipenv install
```

## Usage

### Running ELIZA

To start an interactive chat session:

```bash
python eliza.py
```

### Regenerating the JSON data

To convert the appendix file to JSON format:

```bash
python to_json.py > eliza.json
```

### Running Tests

To run the test suite:

```bash
pipenv run pytest test_eliza.py -v
```
