from cisco_insights.pipeline import bootstrap, export_outputs, validate_warehouse

if __name__ == "__main__":
    database = bootstrap()
    outputs = export_outputs()
    print(f"Built {database}")
    print(validate_warehouse())
    print("Exports:")
    for output in outputs:
        print(f"- {output}")
