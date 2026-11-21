# Indic Fine-Tuning Track

This folder is a separate research track for the VoiceDesign AI review. It contains a small labeled Hindi/Marathi/English dataset and a LoRA training script for structured marketing-prompt extraction.

## What this is

This is an actual fine-tuning starting point for the **language extraction model**, not the diffusion image model. The trained adapter is not integrated into the production app yet.

## Install

From the repository root:

```powershell
python -m pip install datasets transformers peft accelerate torch
```

## Inspect the dataset

```powershell
Get-Content training\indic_prompt_dataset.jsonl
```

The labels include:

- `businessName`
- `businessType`
- `services`
- `colors`
- `cta`
- `visualObjects`

## Start LoRA training

```powershell
python training\train_indic_lora.py --epochs 3
```

The adapter is written to `training/output/indic-extractor-lora`.

For a short review smoke run:

```powershell
python training\train_indic_lora.py --epochs 1 --output training/output/review-smoke
```

## Review wording

Use this accurate statement:

> We started a separate Indic-language fine-tuning track using labeled Hindi, Marathi, and English marketing prompts. We are training a LoRA adapter for structured prompt extraction; production integration and larger-scale evaluation are the next phase.

Do not claim production integration until the adapter has been evaluated and connected to the backend.
