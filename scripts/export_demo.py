from cisco_insights.pipeline import export_outputs

if __name__ == "__main__":
    for path in export_outputs():
        print(path)
