from supervisor import process_query

query = input("Enter Query: ")

result = process_query(query)

print("\n")

for key, value in result.items():
    print(key)
    print(value)
    print()