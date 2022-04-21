from dataclasses import dataclass, field
import logging
from typing import Any, List, Optional


PROTO_NONE_TYPE = "string"


def nullable_declaration(_type: str) -> str:
    default_value: str = None
    if _type == "string":
        default_value = ""
    elif _type == "int32":
        default_value = "0"
    elif _type == "double":
        default_value = "0.0"
    elif _type == "bool":
        default_value = "false"
    else: # could me message type
        default_value = ""
    return f" [(nullable) = '{default_value}']"


@dataclass
class FieldFragment:
    field_type: str
    name: str
    index: int
    nullable: bool = False

    def declaration(self) -> str:
        _type = self.field_type or PROTO_NONE_TYPE
        null_option = nullable_declaration(_type) if self.nullable else ""
        return f"{_type} {self.name} = {self.index}{null_option};"

    def is_alias(self, _field: "FieldFragment") -> Optional[bool]:
        if _field.index != self.index:
            return False
        elif _field.field_type == self.field_type:
            return None
        elif (_field.nullable or self.nullable) and (
            not _field.field_type or not self.field_type
        ):
            return True
        else:
            return False


@dataclass
class MessageFragment:
    name: str
    fields: List[FieldFragment] = field(default_factory=lambda: list())

    def declaration(self) -> str:
        _fields = "\n".join(["\t" + _field.declaration() for _field in self.fields])
        return f"message {self.name} {{\n{_fields}\n}}"


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

    def _find_message(self, fields: List[FieldFragment]) -> MessageFragment:
        _fields: List[FieldFragment] = sorted(fields, key=lambda f: f.index)
        for msg_idx, message in enumerate(self.messages):
            if message.fields == fields:
                return message

            if len(message.fields) != len(fields):
                continue

            alias_field_indexes: List[int] = []
            match: bool = True
            msg_fields: List[FieldFragment] = sorted(
                message.fields, key=lambda f: f.index
            )
            for idx in range(len(msg_fields)):
                _field: FieldFragment = _fields[idx]
                msg_field: FieldFragment = msg_fields[idx]
                if _field == msg_field:
                    continue

                is_alias = msg_field.is_alias(_field)
                if is_alias is True:
                    if msg_field.field_type is None or not msg_field.nullable:
                        alias_field_indexes.append(idx)
                elif is_alias is None:
                    continue
                else:
                    match = False
                    break

            if not match:
                continue

            for idx in alias_field_indexes:
                if not _fields[idx].field_type:
                    self.messages[msg_idx].fields[idx].nullable = True
                else:
                    self.messages[msg_idx].fields[idx].field_type = _fields[idx].field_type
                    self.messages[msg_idx].fields[idx].name = _fields[idx].name
            return self.messages[msg_idx]

    def get_or_create(self, fields: List[FieldFragment]) -> MessageFragment:
        message: MessageFragment = self._find_message(fields)
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
            _field = FieldFragment(None, _name, idx + 1, nullable=True)
            fields.append(_field)
        else:
            _name: str = f"field{idx + 1}"
            _type: str = guess_type(value)
            _field = FieldFragment(_type, _name, idx + 1)
            fields.append(_field)

    message = factory.get_or_create(fields)
    return message


with open("data.json", "r", encoding="utf-8") as f:
    raw = f.read()

import json

raw = raw.split("\n")[2]
j = json.loads(raw)
sub_j = json.loads(j[0][2])

msg = build_message(sub_j)
msg.name = "Main"
print(msg)

factory.messages.reverse()
str_messages = "\n".join(m.declaration() for m in factory.messages)

package_name: str = "google_flights"
content: str = f"""syntax = "proto3";

package {package_name};

{str_messages}
"""
with open("top2.proto", "w") as f:
    f.write(content)
