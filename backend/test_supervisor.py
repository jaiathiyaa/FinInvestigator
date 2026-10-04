from app.agents.supervisor import supervisor


TEST_QUERIES = [
    "Why did NVIDIA stock rise?",
    "Why did NVIDIA stock fall?",
    "What caused NVIDIA shares to rise?",
    "What caused NVIDIA shares to fall?",
    "Investigate NVIDIA",
    "Why did Apple shares rise?",
    "What caused Microsoft stock to fall?",
    "Why did Tata Consultancy Services stock rise?",
]


def main():
    print("=" * 70)
    print("SUPERVISOR ENTITY EXTRACTION TEST")
    print("=" * 70)

    for query in TEST_QUERIES:
        result = supervisor(
            {
                "query": query,
                "trace": [],
                "errors": [],
            }
        )

        print()
        print("-" * 70)
        print(f"Query:     {query}")
        print(
            f"Company:   {result.get('company')}"
        )
        print(
            f"Intent:    "
            f"{result.get('investigation_intent')}"
        )
        print(
            f"Direction: "
            f"{result.get('price_direction')}"
        )

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()