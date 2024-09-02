import bcrypt

class PasswordHash:
  """
  Store password hash (generated with bcrypt) and check against entered password. 
  """

  def __init__(self, password_hash: bytes) -> None:
      self.__pwd_hash = password_hash

  def check(self, password: str) -> bool:
      """
      Check entered password against stored password hash.
      """
      pwd_bytes = password.encode('utf-8')
      return bcrypt.checkpw(pwd_bytes, self.__pwd_hash)
