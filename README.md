# protobuf2arr-tools
 Utility functions and generators for working with the Google protobuf array format.

## Proto model generator

Generate a protobuf model from an unknown format protobuf array object. Often times we get protobuf array messages from Google internal services and need to build proto models to interact with them. This tool generates a template for that protobuf array by trying to guess the data type of each index.

### CLI Usage
```
usage: proto_builder.py [-h] [--package PACKAGE] arr_json output_proto

Build a .proto model for an protobuf array.

positional arguments:
  arr_json           File containing the arr protobuf object.
  output_proto       File name to save the output .proto model.

options:
  -h, --help         show this help message and exit
  --package PACKAGE  .proto model package name.

```

### Example
```
>>> head data.json
[[null, [[1650289911312855, 44780456, 1997349351], null, 2], 0, "92xdYpeME6iXrcUP58O0uAc"], [[[[["YSF", 0], "Hello World", ... 

>>> proto_builder.py data.json message.proto
Generated protobuf model: message.proto

>>> head message.proto
syntax = "proto3";

package generated;

message EntryPoint {
	Msg2 msg1 = 1;
	Msg11 msg2 = 2;
	string none3 = 3 [(nullable) = ''];
	Msg29 msg4 = 4;
	string none5 = 5 [(nullable) = ''];
	string none6 = 6 [(nullable) = ''];
	Msg31Container msg7 = 7;
	Msg41 msg8 = 8;
	string none9 = 9 [(nullable) = ''];
	string none10 = 10 [(nullable) = ''];
	string none11 = 11 [(nullable) = ''];
	Msg42Container msg12 = 12;
	Msg3 msg13 = 13;
	string none14 = 14 [(nullable) = ''];
	Msg1 msg15 = 15;
	string none16 = 16 [(nullable) = ''];
	string none17 = 17 [(nullable) = ''];
	Msg47 msg18 = 18;
	Msg3 msg19 = 19;
	string none20 = 20 [(nullable) = ''];
	bool field21 = 21;
}

...
```