from dataclasses import dataclass, field
from typing import Any, List

@dataclass
class FieldFragment:
    field_type: str
    name: str
    index: int
    nullable: bool = False


@dataclass
class MessageFragment:
    name: str
    fields: List[FieldFragment] = field(default_factory=lambda: list())


class FragmentFactory:
    def __init__(self) -> None:
        self.messages: List[MessageFragment] = list()
        self.num_words = {
            1: "One",
            2: "Two",
            3: "Three",
            4: "Four",
            5: "Five",
            6: "Six",
            7: "Seven",
            8: "Eight",
            9: "Nine",
            10: "Ten",
            11: "Eleven",
            12: "Twelve",
            13: "Thirteen",
            14: "Fourteen",
            15: "Fifteen",
            16: "Sixteen",
            17: "Seventeen",
            18: "Eighteen",
            19: "Nineteen",
            20: "Twenty",
            30: "Thirty",
            40: "Forty",
            50: "Fifty",
            60: "Sixty",
            70: "Seventy",
            80: "Eighty",
            90: "Ninety",
            0: "Zero",
        }

    def _get_message_name(self) -> str:
        num = len(self.messages)
        if num in self.num_words:
            return "Msg" + self.num_words[num]
        return "Msg" + self.num_words[num - (num % 10)] + self.num_words[num % 10]

    def get_or_create(self, fields: List[FieldFragment]) -> MessageFragment:
        message: MessageFragment = next(
            filter(lambda msg: msg.fields == fields, self.messages), None
        )
        if not message:
            msg_name: str = self._get_message_name()  # f"Msg{len(self.messages)}"
            message = MessageFragment(msg_name, fields=fields)
            self.messages.append(message)
        return message

def guess_type(value: Any) -> str:
    if isinstance(value, str):
        return "string"
    elif isinstance(value, int):
        return "int32"
    elif isinstance(value, float):
        return "double"
    elif isinstance(value, bool):
        return "bool"
    else:
        print(type(value), value)
        return "int32"


factory: FragmentFactory = FragmentFactory()


def build_message(arr: List[Any]) -> MessageFragment:
    fields: List[FieldFragment] = list()
    for idx, value in enumerate(arr):
        if isinstance(value, list):
            sub_message = build_message(value)

            _name: str = f"msg{idx + 1}"
            _field = FieldFragment(sub_message.name, _name, idx + 1)
            fields.append(_field)
        elif value is None:
            _name: str = f"none{idx + 1}"
            _field = FieldFragment("string", _name, idx + 1, nullable=True)
            fields.append(_field)
        else:
            _name: str = f"field{idx + 1}"
            _type: str = guess_type(value)
            _field = FieldFragment(_type, _name, idx + 1)
            fields.append(_field)

    message = factory.get_or_create(fields)
    return message


def stringify_message(message: MessageFragment) -> str:
    nullable: str = " [(nullable) = '']"
    fields: str = "\n".join(
        [
            f"\t{_field.field_type} {_field.name} = {_field.index}{nullable if _field.nullable else ''};"
            for _field in message.fields
        ]
    )
    return f"message {message.name} {{\n{fields}\n}}"


with open('data.json','r', encoding="utf-8") as f:
    raw = f.read()

import json
raw = raw.split("\n")[2]
j = json.loads(raw)
sub_j = json.loads(j[0][2])

msg = build_message(sub_j)
msg.name = "Main"
print(msg)

factory.messages.reverse()
str_messages = "\n".join(stringify_message(m) for m in factory.messages)

package_name: str = "google_flights"
content: str = f"""syntax = "proto3";

package {package_name};

{str_messages}
"""
with open("top.proto", 'w') as f:
    f.write(content)