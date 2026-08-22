import os
import hashlib
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred_path = os.path.join(os.path.dirname(__file__), '.firebase-credentials.json')
if not os.path.exists(cred_path):
    print("Credentials not found!")
    exit(1)

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client(database_id='galarixdb')

def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()

def migrate_keys():
    keys_ref = db.collection('api_keys')
    docs = keys_ref.stream()
    
    count = 0
    for doc in docs:
        data = doc.to_dict()
        if 'key' in data and 'key_hash' not in data:
            raw_key = data['key']
            hashed_key = _hash_key(raw_key)
            prefix = raw_key[:7]
            
            update_data = {
                'key_hash': hashed_key,
                'key_prefix': prefix,
                'usage_count': data.get('usage_count', 0),
                'tier': data.get('tier', 'free')
            }
            # Optional: remove the plaintext key if you want to be fully secure
            # update_data['key'] = firestore.DELETE_FIELD
            
            doc.reference.update(update_data)
            print(f"Migrated key {prefix}...")
            count += 1
            
    print(f"Migration complete! Migrated {count} keys.")

if __name__ == '__main__':
    migrate_keys()
