# Quick check script
from MongoDataStore import MongoDataStore

MongoDataStore.connect()

print("Indexes on transactions collection:")
for idx in MongoDataStore._db.transactions.list_indexes():
    print(f"  - {idx['name']}: {idx.get('key', {})}")
