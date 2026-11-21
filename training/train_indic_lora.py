"""Train a LoRA adapter for Indic marketing-prompt extraction.

This trains an extraction model only. It does not fine-tune the image model.
"""

import argparse
import json
from pathlib import Path

from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, DataCollatorForLanguageModeling, Trainer, TrainingArguments


SYSTEM = (
    "Extract marketing fields from Hindi, Marathi, English, or mixed prompts. "
    "Return valid JSON with businessName, businessType, services, colors, cta, and visualObjects."
)


def format_example(example):
    user = f"System: {SYSTEM}\nUser: {example['prompt']}\nAssistant:"
    answer = json.dumps(example["output"], ensure_ascii=False)
    return {"text": f"{user} {answer}"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--data", default="training/indic_prompt_dataset.jsonl")
    parser.add_argument("--output", default="training/output/indic-extractor-lora")
    parser.add_argument("--epochs", type=float, default=3)
    args = parser.parse_args()

    dataset = load_dataset("json", data_files=args.data, split="train")
    dataset = dataset.map(format_example)
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, max_length=512)

    tokenized = dataset.map(tokenize, batched=True, remove_columns=dataset.column_names)
    model = AutoModelForCausalLM.from_pretrained(args.model)
    model.config.use_cache = False
    lora = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        task_type="CAUSAL_LM",
    )
    training_args = TrainingArguments(
        output_dir=args.output,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        logging_steps=1,
        save_strategy="epoch",
        report_to="none",
        fp16=False,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )
    trainer.train()
    trainer.save_model(args.output)
    tokenizer.save_pretrained(args.output)
    print(f"LoRA adapter saved to: {args.output}")


if __name__ == "__main__":
    main()
