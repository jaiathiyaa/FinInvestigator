from app.services.finance_verifier import verify_finance_entity

result = verify_finance_entity(
    company_name="Tesla, Inc.",
    ticker="TSLA",
    exchange="NASDAQ",
)

print("\nFINAL RESULT")
print("=" * 80)

for key, value in result.items():
    if key != "raw_data" and key != "summary":
        print(f"{key}: {value}")