"""Region-aware multilingual evals: ask local questions in the local language.

INCLUDE-2.0 (2026) found that frontier models score about 14.5 points lower
on locally embedded knowledge than on widely documented facts about a region,
and that open-weight models do not reliably answer the same whether a
question is asked in English or in its original language. Translating an
English benchmark misses both; the questions have to be about the region.

Each regional fact is asked twice, in English and in the original language.
Scoring needs aliases: asked in Polish, a correct answer about Kraków names
the river *Wisła*, not *Vistula*. A scorer that only knows the English name
marks that right answer wrong and measures translation, not knowledge.

The scripted model is right on every English question, wrong on one local
one, and answers another in the local name.
"""

from __future__ import annotations

from typing import Any

from _shared import check_scorer, explanations, lesson_model, offline, run_eval
from inspect_ai import Task
from inspect_ai.dataset import Sample
from inspect_ai.solver import generate, system_message

SYSTEM = "Answer with the name only, in the language of the question."

# (id, language, English question, local question, accepted answers)
FACTS = [
    ("dresden", "de", "Which river flows through Dresden?",
     "Welcher Fluss fließt durch Dresden?", ["Elbe"]),
    ("cluj", "ro", "What is the seat of Cluj County?",
     "Care este reședința județului Cluj?", ["Cluj-Napoca"]),
    ("bahia", "pt", "What is the capital of the Brazilian state of Bahia?",
     "Qual é a capital do estado da Bahia?", ["Salvador"]),
    ("krakow", "pl", "On which river does Kraków lie?",
     "Nad jaką rzeką leży Kraków?", ["Vistula", "Wisła"]),
    ("jalisco", "es", "What is the capital of the Mexican state of Jalisco?",
     "¿Cuál es la capital del estado de Jalisco?", ["Guadalajara"]),
]  # fmt: skip

SCRIPTED_LOCAL = {"bahia": "Feira de Santana", "krakow": "Wisła"}
PLANTED = {"bahia-local"}


def with_aliases(completion: str, meta: dict[str, Any]) -> str | None:
    text = completion.casefold()
    ok = any(name.casefold() in text for name in meta["answers"])
    return None if ok else f"none of {meta['answers']}"


def english_only(completion: str, meta: dict[str, Any]) -> str | None:
    return None if meta["answers"][0].casefold() in completion.casefold() else "wrong"


def main() -> None:
    dataset, scripted = [], {}
    for key, lang, english, local_q, answers in FACTS:
        meta = {"answers": answers, "lang": lang}
        dataset.append(Sample(id=f"{key}-en", input=english, metadata=meta))
        dataset.append(Sample(id=f"{key}-local", input=local_q, metadata=meta))
        scripted[english] = answers[0]
        scripted[local_q] = SCRIPTED_LOCAL.get(key, answers[-1])

    task = Task(
        dataset=dataset,
        solver=[system_message(SYSTEM), generate()],
        scorer=[
            check_scorer("aliases", with_aliases),
            check_scorer("english_only", english_only),
        ],
    )
    log = run_eval(task, lesson_model(scripted))
    wrong = set(explanations(log, "aliases"))
    naive = set(explanations(log, "english_only"))
    en = 1 - len({w for w in wrong if w.endswith("-en")}) / len(FACTS)
    local = 1 - len({w for w in wrong if w.endswith("-local")}) / len(FACTS)

    if offline() and (wrong != PLANTED or naive != PLANTED | {"krakow-local"}):
        raise AssertionError(f"aliases={wrong} english_only={naive}")
    print(
        f"OK: English={en:.2f} local language={local:.2f} gap={en - local:.2f}; "
        f"an English-only scorer would also fail {sorted(naive - wrong)}"
    )


if __name__ == "__main__":
    main()
