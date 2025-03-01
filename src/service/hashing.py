from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Hasher:
    """
    Класс, предоставляющий 2 статических метода:
    :verify_password: Метод для проверки соответствия пароля в чистом виде и после хеширования.
    :get_password_hash: Метод для хеширования пароля.
    """

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
