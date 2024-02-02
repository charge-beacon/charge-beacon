class Event:
    def __init__(self, name):
        self.name = name

    def send(self, message: str, data: dict[str, any]) -> None:
        from app.tasks import event
        event.delay(self.name, message, data)


APP_SIGNUP = Event('app_signup')
CREATE_SEARCH = Event('create_search')
