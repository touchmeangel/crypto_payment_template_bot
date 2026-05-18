from sqlalchemy import TypeDecorator, LargeBinary
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

class Base(AsyncAttrs, DeclarativeBase):
    pass

class I128(TypeDecorator):
  impl = LargeBinary(16)  # 16 bytes = 128 bits
  cache_ok = True

  def process_bind_param(self, value, dialect):
    if value is None:
      return None
    if not isinstance(value, int):
      raise TypeError("I128 expects int")
    # Signed 128-bit range: -2**127 to 2**127 - 1
    min_val = -(2 ** 127)
    max_val = 2**127 - 1
    if not (min_val <= value <= max_val):
      raise ValueError("Value out of signed 128-bit range")
    # Convert to two’s complement unsigned representation
    if value < 0:
      value = (1 << 128) + value
    return value.to_bytes(16, byteorder="big", signed=False)

  def process_result_value(self, value, dialect):
    if value is None:
      return None
    unsigned = int.from_bytes(value, byteorder="big", signed=False)
    # Interpret as signed if highest bit is set
    if unsigned & (1 << 127):
      return unsigned - (1 << 128)
    return unsigned

class U256(TypeDecorator):
  impl = LargeBinary(32)
  cache_ok = True

  def process_bind_param(self, value, dialect):
    if value is None:
      return None
    if not isinstance(value, int):
      raise TypeError("U256 expects int")
    if value < 0 or value >= 2**256:
      raise ValueError("Value out of u256 range")
    return value.to_bytes(32, byteorder="big")

  def process_result_value(self, value, dialect):
    if value is None:
      return None
    return int.from_bytes(value, byteorder="big")