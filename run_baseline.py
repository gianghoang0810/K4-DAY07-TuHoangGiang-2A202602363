import json
from pathlib import Path
from bench import parse_frontmatter
from src.chunking import ChunkingStrategyComparator

def main():
    data_dir = Path("data/utsc-library-services")
    files_to_test = [
        "utsc-borrowing-policy.md",
        "utsc-technology-loans.md",
        "utsc-course-reserves.md"
    ]
    
    comparator = ChunkingStrategyComparator()
    results = {}
    
    for filename in files_to_test:
        path = data_dir / filename
        if not path.exists():
            continue
        _, content = parse_frontmatter(path)
        comparison = comparator.compare(content, chunk_size=500)
        
        # Only store the count and avg_length to avoid huge output
        results[filename] = {
            strat: {
                "count": data["count"], 
                "avg_length": round(data["avg_length"], 2)
            } 
            for strat, data in comparison.items()
        }
        
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
