def hide_session_string(session_string: str) -> str:
  return session_string[:4] + ".." + session_string[len(session_string)-4:len(session_string)]