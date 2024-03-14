channels = [
    {
        "name": "Achievement Hunter",
        "slug": "achievement-hunter",
        "uuid": "2cb2a70c-be50-46f5-93d7-84a1baabb4f7",
    },
    {
        "name": "All Good No Worries",
        "slug": "all-good-no-worries",
        "uuid": "b0252a94-e97d-4784-9fc0-03b97be9df38",
    },
    {
        "name": "Best Friends Today",
        "slug": "best-friends-today",
        "uuid": "d679726b-c41e-4044-85b3-3a088739c0e6",
    },
    {
        "name": "Camp Camp",
        "slug": "camp-camp",
        "uuid": "a0b578e2-56d7-4b60-8432-b97ba3426aaa",
    },
    {
        "name": "Death Battle",
        "slug": "death-battle",
        "uuid": "dd838359-a0e0-405f-b18b-5b0ed16ef852",
    },
    {
        "name": "Dogbark",
        "slug": "dogbark",
        "uuid": "ef34750e-ab1c-4c29-985f-cf42b066102b",
    },
    {
        "name": "F__kFace",
        "slug": "f-kface",
        "uuid": "75ba87e8-06fd-4482-bad9-52a4da2c6181",
    },
    {
        "name": "Friends of RT",
        "slug": "friends-of-rt",
        "uuid": "cb748682-3335-4faf-8fce-1273da49aa20",
    },
    {
        "name": "Funhaus",
        "slug": "funhaus",
        "uuid": "2dc2a30b-55b7-443c-b565-1b3be9257fc4",
    },
    {
        "name": "Inside Gaming",
        "slug": "inside-gaming",
        "uuid": "8d8e8f0c-f58c-444e-bac4-1c33339bf105",
    },
    {
        "name": "Kinda Funny",
        "slug": "kinda-funny",
        "uuid": "6ce10ccb-f945-4b21-b157-5c5619bf1de3",
        "title": "Kinda Funny",
        "id": "kinda-funny",
        "value": "6ce10ccb-f945-4b21-b157-5c5619bf1de3",
    },
    {
        "name": "Red vs. Blue",
        "slug": "red-vs-blue-universe",
        "uuid": "5167de51-5719-4c1a-b9c5-ed727ef8f3a3",
    },
    {
        "name": "Red Web",
        "slug": "red-web",
        "uuid": "16d7e2f0-e67a-4bfd-9c27-427e722da888",
    },
    {
        "name": "Rooster Teeth",
        "slug": "rooster-teeth",
        "uuid": "92b6bb21-91d2-4b1b-bf95-3268fa0d9939",
    },
    {
        "name": "RWBY",
        "slug": "rwby-universe",
        "uuid": "92f780eb-ebfe-4bf5-a3b5-c6ad5460a5f1",
    },
    {
        "name": "Tales From the Stinky Dragon",
        "slug": "tales-from-the-stinky-dragon",
        "uuid": "44ef6a57-e965-40e6-942b-c28d7dec727b",
    },
]


def get_channel_name_from_id(channel_id):
    for channel in channels:
        if "uuid" in channel and channel["uuid"] == channel_id:
            return channel["name"].strip()
    return None
