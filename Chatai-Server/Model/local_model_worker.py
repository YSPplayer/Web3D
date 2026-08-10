import gc
import json
import sys
import threading
import traceback
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer


def write_event(event: dict):
    sys.stdout.write(json.dumps(event, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def cleanup_cuda():
    gc.collect()
    if torch.cuda.is_available():
        try:
            torch.cuda.synchronize()
        except Exception:
            pass
        torch.cuda.empty_cache()
        try:
            torch.cuda.ipc_collect()
        except Exception:
            pass
        try:
            torch.cuda.reset_peak_memory_stats()
        except Exception:
            pass


def end_streamer(streamer):
    if streamer is None:
        return
    try:
        streamer.on_finalized_text("", stream_end=True)
    except Exception:
        pass


def load_model(model_path: Path):
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        local_files_only=True
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        local_files_only=True,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    model.eval()
    return tokenizer, model


def run_chat(request_id: int, messages: list[dict], tokenizer, model):
    inputs = None
    streamer = None
    generation_kwargs = None
    thread = None
    error = None

    try:
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        streamer = TextIteratorStreamer(
            tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )
        generation_kwargs = {
            **inputs,
            "streamer": streamer,
            "max_new_tokens": 1024,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9,
            "eos_token_id": tokenizer.eos_token_id
        }

        def generate():
            nonlocal error
            try:
                model.generate(**generation_kwargs)
            except Exception as exc:
                error = exc
            finally:
                end_streamer(streamer)

        thread = threading.Thread(target=generate, daemon=True)
        thread.start()

        for text in streamer:
            if text:
                write_event({
                    "id": request_id,
                    "type": "delta",
                    "content": text
                })

        thread.join(timeout=2)
        if error is not None:
            raise error

        write_event({
            "id": request_id,
            "type": "done"
        })
    except Exception as exc:
        write_event({
            "id": request_id,
            "type": "error",
            "message": str(exc)
        })
        traceback.print_exc(file=sys.stderr)
    finally:
        del generation_kwargs
        del streamer
        del inputs
        cleanup_cuda()


def count_tokens(request_id: int, command: dict, tokenizer):
    try:
        text = command.get("text")
        messages = command.get("messages")

        if text is None and messages is not None:
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

        count = len(tokenizer.encode(text or ""))
        write_event({
            "id": request_id,
            "type": "token_count",
            "count": count
        })
    except Exception as exc:
        write_event({
            "id": request_id,
            "type": "error",
            "message": str(exc)
        })
        traceback.print_exc(file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        write_event({
            "type": "startup_error",
            "message": "缺少模型路径参数"
        })
        return 1

    model_path = Path(sys.argv[1])
    if not model_path.exists():
        write_event({
            "type": "startup_error",
            "message": f"本地模型路径不存在: {model_path}"
        })
        return 1

    tokenizer = None
    model = None
    try:
        tokenizer, model = load_model(model_path)
        write_event({
            "type": "ready",
            "model_path": str(model_path)
        })

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                command = json.loads(line)
            except Exception:
                continue

            command_type = command.get("type")
            if command_type == "shutdown":
                break
            if command_type == "chat":
                run_chat(
                    command.get("id"),
                    command.get("messages") or [],
                    tokenizer,
                    model
                )
            if command_type == "count_tokens":
                count_tokens(
                    command.get("id"),
                    command,
                    tokenizer
                )
    except Exception as exc:
        write_event({
            "type": "startup_error",
            "message": str(exc)
        })
        traceback.print_exc(file=sys.stderr)
        return 1
    finally:
        del model
        del tokenizer
        cleanup_cuda()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
