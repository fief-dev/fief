import argparse
import sys
from ast import literal_eval
from typing import IO

import libcst as cst
from libcst.codemod import (
    CodemodContext,
    ContextAwareTransformer,
    TransformSuccess,
    transform_module,
)

from fief.models.base import TABLE_PREFIX_PLACEHOLDER


class ConvertTablePrefixStrings(ContextAwareTransformer):
    def leave_SimpleString(
        self, original_node: cst.SimpleString, updated_node: cst.SimpleString
    ) -> cst.SimpleString | cst.FormattedString:
        literal_string_value = literal_eval(updated_node.value)
        if TABLE_PREFIX_PLACEHOLDER in literal_string_value:
            before, after = literal_string_value.split(TABLE_PREFIX_PLACEHOLDER)
            return cst.FormattedString(
                [
                    cst.FormattedStringText(before),
                    cst.FormattedStringExpression(cst.Name("table_prefix")),
                    cst.FormattedStringText(after),
                ]
            )
        return updated_node


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file", help="The file to transform", type=argparse.FileType("r+")
    )
    args = parser.parse_args()
    file: IO = args.file

    context = CodemodContext()
    result = transform_module(ConvertTablePrefixStrings(context), file.read())

    if not isinstance(result, TransformSuccess):
        print(f"Error: {result}")
        sys.exit(1)

    file.seek(0)
    file.write(result.code)
