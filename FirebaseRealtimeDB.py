import firebase_admin
from firebase_admin import credentials, db

class FirebaseRealtimeDB:
    def __init__(self, cred_path, db_url):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {'databaseURL': db_url})

    def set_latest_clipboard(self, data):
        ref = db.reference('clipboard')
        ref.set(data)

    def get_latest_clipboard(self):
        ref = db.reference('clipboard')
        return ref.get()

    def listen_latest_clipboard(self, callback):
        ref = db.reference('clipboard')
        ref.listen(lambda event: callback(event.data))