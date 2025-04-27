from fief.storage import M, StorageProtocol


class Registration:
    """
    Logic to handle user registration.
    """

    def __init__(self, user_model: type[M], storage: StorageProtocol) -> None:
        self._user_model = user_model
        self._storage = storage
