from enum import Enum
from typing import Type, TypeVar, Optional, Iterable

T = TypeVar("T", bound=Enum)


def await_user_input(
    enum_cls: Type[T],
    prompt: str,
    exit_values: Iterable[str] = ("q", "quit", "exit"),
) -> Optional[T]:
    """
    Prompt the user to choose an Enum option.

    Args:
        enum_cls: The Enum class defining the available options.
        prompt: Text shown to the user before listing options.
        exit_values: Strings that cause the function to return None.

    Returns:
        The chosen Enum member, or None if the user quits.
    """

    options_text = "\n".join(
        f"{member.value}. {member.name.title().replace('_', ' ')}"
        for member in enum_cls
    )

    while True:
        print(f"\n{prompt}\n{options_text}\n({', '.join(exit_values)} to quit)")
        choice = input("Select option: ").strip().lower()

        if choice in exit_values:
            return None

        if not choice.isdigit():
            print("Please enter a valid number.")
            continue

        try:
            return enum_cls(int(choice))
        except ValueError:
            print("Invalid option. Please choose a valid number.")
