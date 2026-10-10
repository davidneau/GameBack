import os
import threading
from tiktok import transcribe_live, get_stream_url, isLivingDef
from datetime import datetime
import asyncio

class Worker():
    def __init__(self, users_id):
        self.users_id = users_id

    async def run(self):
        while True:
            await self.process()
            await asyncio.sleep(5)

    async def process(self):
        for user_id, is_recording in self.users_id.items():
            await asyncio.sleep(2)
            if is_recording:
                continue
            print(f"{user_id} : vérification du live...")
            is_living = await isLivingDef(user_id)
            if not is_living:
                print(f"{user_id} is not living")
                continue

            # IMPORTANT :
            # on marque immédiatement comme traité
            self.users_id[user_id] = True

            print(f"{user_id} is living, recording...")
            try:
                maintenant = datetime.now().strftime("%d%m%Y_%H%M")
                dossier = os.path.join(
                    "resume",
                    user_id,
                    maintenant
                )

                os.makedirs(dossier, exist_ok=True)

                """ url = get_stream_url(user_id) """

                output_file = os.path.join(
                    dossier,
                    "retranscription.txt"
                )

                thread = threading.Thread(
                    target=transcribe_live,
                    args=(user_id, output_file),
                    daemon=True
                )

                thread.start()
            except Exception as e:
                print(f"Erreur avec {user_id}: {e}")

                # Important : autoriser une nouvelle tentative
                self.users_id[user_id] = False

users_id = {
    "lemondeducabaret": False,
    "sullypapillon1": False,
    "jonathanwadoux7": False,
    "madamemeletout": False,
    "miss.jazz.artiste": False,
    "missjazzetmisscoco": False,
    "orkanouille": False,
}

if __name__ == "__main__":
    worker = Worker(users_id)
    asyncio.run(worker.run())