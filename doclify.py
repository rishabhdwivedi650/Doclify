import os
import sys
from pathlib import Path

from groq import Groq

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".cpp", ".c", ".html", ".css"
}


def collect_files(folder):
    files = []

    for path in folder.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            if ".git" not in path.parts and "node_modules" not in path.parts:
                files.append(path)

    return files


def build_context(files, root):
    parts = []

    for path in files[:30]:
        try:
            text = path.read_text(
                encoding="utf-8",
                errors="ignore"
            )
        except OSError:
            continue

        text = text[:8000]
        relative = path.relative_to(root)

        parts.append(
            f"FILE: {relative}\n{text}"
        )

    return "\n\n".join(parts)


def generate_readme(context):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set."
        )

    client = Groq(api_key=api_key)

    prompt = f"""
Create a simple GitHub README for this software project.

Include:
- Project overview
- Main features
- Technologies
- Setup
- Basic usage

Use only information supported by the code.
Do not invent features.

Project files:

{context}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You write simple technical documentation."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content


def main():
    folder = Path(
        sys.argv[1] if len(sys.argv) > 1 else "."
    ).resolve()

    if not folder.exists() or not folder.is_dir():
        print("Please provide a valid project folder.")
        return

    files = collect_files(folder)

    if not files:
        print("No supported source files found.")
        return

    print(
        f"Found {len(files)} source file(s). "
        "Generating documentation..."
    )

    context = build_context(files, folder)
    readme = generate_readme(context)

    output = folder / "GENERATED_README.md"
    output.write_text(readme, encoding="utf-8")

    print(
        f"Documentation saved to: {output}"
    )


if __name__ == "__main__":
    main()
