from dataclasses import dataclass, field
import logging
from typing import Any, List, Optional, Union


PROTO_NONE_TYPE = "string"

PROTO_TYPES = ["string", "int32", "double", "bool"]


@dataclass
class FieldFragment:
    """Represents a field in a protobuf message."""

    field_type: str
    name: str
    index: int
    nullable: bool = False
    repeated: bool = False

    def is_alias(self, _field: "FieldFragment") -> Optional[bool]:
        """Determines if this field is an nullable alias of another field."""

        if _field.index != self.index:
            return False
        elif _field.repeated != self.repeated:
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


class FragmentFactory:
    def __init__(self) -> None:
        self.messages: List[MessageFragment] = list()

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

            # update nullable message fields to have proper type and nullable flag
            for idx in alias_field_indexes:
                if not _fields[idx].field_type:
                    self.messages[msg_idx].fields[idx].nullable = True
                else:
                    self.messages[msg_idx].fields[idx].field_type = _fields[
                        idx
                    ].field_type
                    self.messages[msg_idx].fields[idx].name = _fields[idx].name
            return self.messages[msg_idx]

    def get_or_create(self, fields: List[FieldFragment]) -> MessageFragment:
        message: MessageFragment = self._find_message(fields)
        if not message:
            msg_name: str = self._get_message_name(fields)
            message = MessageFragment(msg_name, fields=fields)
            self.messages.append(message)
        return message

    def _get_message_name(self, fields: List[FieldFragment]) -> str:
        """Tries to generate a contextually relevant name for the message."""

        if len(fields) == 0:
            return "Empty"
        elif len(fields) == 1:
            _type: str = fields[0].field_type
            if not _type:
                return "Null"
            elif _type not in PROTO_TYPES:  # message type
                return f"{_type}Container"
            else:
                return _type.capitalize()
        else:
            return f"Msg{len(self.messages)}"


class ProtoFileBuilder:
    def _nullable_declaration(self, _type: str) -> str:
        default_value: str = None
        if _type == "string":
            default_value = ""
        elif _type == "int32":
            default_value = "0"
        elif _type == "double":
            default_value = "0.0"
        elif _type == "bool":
            default_value = "false"
        else:  # could be message type
            default_value = ""
        return f" [(nullable) = '{default_value}']"

    def _fragment_declaration(self, field: FieldFragment) -> str:
        """Returns the field protobuf text for the .proto file."""

        _type = field.field_type or PROTO_NONE_TYPE
        null_option = self._nullable_declaration(_type) if field.nullable else ""
        repeated_option = "repeated " if field.repeated else ""
        return f"{repeated_option}{_type} {field.name} = {field.index}{null_option};"

    def _message_declaration(self, message: MessageFragment) -> str:
        _fields = "\n".join(
            ["\t" + self._fragment_declaration(_field) for _field in message.fields]
        )
        return f"message {message.name} {{\n{_fields}\n}}"

    def build(self, package_name: str, messages: List[MessageFragment]) -> str:
        contents: str = "\n".join(
            [self._message_declaration(message) for message in messages]
        )
        return f'syntax = "proto3";\n\npackage {package_name};\n\n{contents}\n'


class ProtoGenerator:
    def __init__(self) -> None:
        self.factory: FragmentFactory = FragmentFactory()

    def _py_to_proto_field_type(self, value: Any) -> str:
        if isinstance(value, str):
            return "string"
        elif isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int32"
        elif isinstance(value, float):
            return "double"
        else:
            logging.warn(f"Detected unknown python to proto field type: {type(value)}")
            return "int32"

    def _build_message(
        self, arr: List[Any], use_repeated_fields: bool = False
    ) -> Union[MessageFragment, FieldFragment]:
        fields: List[FieldFragment] = list()
        for idx, value in enumerate(arr):
            if isinstance(value, list):
                sub_message = self._build_message(value)
                if isinstance(sub_message, FieldFragment):
                    _name: str = f"field{idx + 1}"
                    _field = FieldFragment(
                        sub_message.field_type, _name, idx + 1, repeated=True
                    )
                else:
                    _name: str = f"msg{idx + 1}"
                    _field = FieldFragment(sub_message.name, _name, idx + 1)
            elif value is None:
                _name: str = f"none{idx + 1}"
                _field = FieldFragment(None, _name, idx + 1, nullable=True)
            else:
                _name: str = f"field{idx + 1}"
                _type: str = self._py_to_proto_field_type(value)
                _field = FieldFragment(_type, _name, idx + 1)
            fields.append(_field)

        is_repeated: bool = (
            use_repeated_fields
            and len(set([_field.field_type for _field in fields])) == 1
            and len(fields) > 1
        )
        if is_repeated:
            return FieldFragment(fields[0].field_type, None, None, repeated=True)
        elif len(fields) == 1 and fields[0].field_type:
            fields[0].name = "value"

        message: MessageFragment = self.factory.get_or_create(fields)
        return message

    def build(self, arr: List[Any], package_name: str) -> str:
        top_message: MessageFragment = self._build_message(arr)
        top_message.name = "EntryPoint"
        builder = ProtoFileBuilder()
        return builder.build(package_name, self.factory.messages)


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Build a .proto model for an protobuf array.")
    parser.add_argument("arr_json", help="File containing the arr protobuf object.")
    parser.add_argument("output_proto", help="File name to save the output .proto model.")
    parser.add_argument("--package", help=".proto model package name.")

    args = parser.parse_args()
    
    with open(args.arr_json, "r", encoding="utf-8") as f:
        raw_arr: str = f.read()

    arr: List[Any] = json.loads(raw_arr)
    generator: ProtoGenerator = ProtoGenerator()
    package_name: str = args.package or "generated"
    content = generator.build(arr, package_name)

    with open(args.output_proto, "w") as f:
        f.write(content)

    print(f"Generated protobuf model: {args.output_proto}")