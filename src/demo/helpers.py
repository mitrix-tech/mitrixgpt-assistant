def pretty_print_docs(docs):
    print(
        f"\n{'-' * 100}\n".join(
            [f"Document {i + 1} ID:{d.id} Metadata: {d.metadata}:\n\n" + d.page_content for i, d in enumerate(docs)]
        )
    )
