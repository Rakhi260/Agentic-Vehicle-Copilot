from supervisor import process_query
from supervisor import build_context

query = input("Query: ")

result = process_query(query)

context = build_context(result)

print(context)